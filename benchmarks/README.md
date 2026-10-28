# Load testing

Simulated load against the API to measure throughput and latency, and to check that
changes actually help. These are synthetic users, not production traffic.

## Results

Same machine, same dataset, same scripts. "Before" is the code with only the broken
endpoints fixed (commit `f602d9f`); "after" is the current branch. One uvicorn worker.

| Concurrent users | Before: req/s | Before: p50 / p95 | After: req/s | After: p50 / p95 |
| ---: | ---: | ---: | ---: | ---: |
| 50  | 46.7 | 55 / 220 ms     | 49.4  | 14 / 64 ms   |
| 100 | 58.1 | 670 / 1,100 ms  | 96.5  | 24 / 150 ms  |
| 200 | 57.4 | 2,400 / 3,100 ms | 130.6 | 470 / 740 ms |
| 400 | 55.3 | 6,000 / 12,000 ms | 123.8 | 2,000 / 3,000 ms |
| 800 | 56.0 | 6,300 / 26,000 ms | 109.7 | 1,700 / 6,700 ms |

- Peak throughput went from about 58 to about 131 requests per second (2.2x).
- At 200 users, p95 latency went from 3.1 s to 0.74 s.
- Error rate was 0% at every level before and at most 0.05% after.
- Past saturation (about 130 req/s here) extra users only add queueing, so latency
  climbs while throughput stays flat. That is expected for a closed-loop test.

Repeat runs landed within about 3% of the sweep numbers (before, 100 users: 59.6 and
57.8 req/s; after, 200 users: 127.8 and 124.3 req/s). Raw output is in `results/`.

## What changed between before and after

1. Database calls no longer block the event loop. Read handlers are plain `def` so
   FastAPI runs them in its threadpool, and write paths use `run_in_threadpool`.
2. The feed, search and trending queries no longer trigger N+1 loads. Queries per
   request: feed 15 to 5, post detail 11 to 5, search 24 to 4, trending 7 to 3.
   `Post.comments` was `lazy="selectin"`, which loaded every comment on every post query.
3. Indexes on `posts.created_at`, `posts.user_id`, `post_comments.post_id`,
   `post_comments.parent_id` and `notifications(recipient_id, created_at)`.
   Existing databases need `sql/001_indexes.sql`.
4. A connection pool deadlock found by this testing. The auth dependency held a pooled
   connection while the request waited for a worker thread, so above about 300 users
   all threads could block on pool checkout. Throughput dropped to about 17 req/s
   with 30 s tails until this was fixed.

I also fixed four endpoints that returned 500 before any of this (post detail,
search, vote, comment).

## Vote counts under simultaneous voting

Speed is no use if the numbers are wrong, so `vote_consistency.py` fires many votes at
once and then checks each post's stored vote counter against the actual vote rows.
"Wrong votes" is the total gap between the two across the test posts. Three runs each:

| Scenario | Before: wrong votes | After: wrong votes |
| --- | ---: | ---: |
| 200 users upvote one post at once | 188 to 196 | 0 |
| 300 users cast random up/down votes on 5 posts (1,500 votes) | 486 to 519 | 0 |
| 150 users double-click the same vote | 86 to 98, plus 97 to 106 server errors | 0, no errors |

Cause: voting read the counter, added one in Python and wrote the result back. Requests
that overlapped read the same starting value and overwrote each other, so out of 200
simultaneous upvotes the counter only recorded a handful. A double click made both
requests try to insert the same vote row and one of them failed with a 500.

Fix: lock the post row at the start of the vote (`SELECT ... FOR UPDATE`). Votes on the
same post then run one after another and each sees the previous one. Votes on different
posts do not block each other. Throughput on the main load test did not change
(133 req/s at 200 users, against 131 before).

Run it with `uv run python benchmarks/vote_consistency.py`.

## Larger dataset: 500,000 posts

Everything above used 20,000 posts. To see what happens as the data grows, the same
tests were run on 500,000 posts, 1.5 million comments and 2 million votes (884 MB).
Same machine, same traffic mix, one worker.

The code that was fine at 20,000 posts was not fine at 500,000:

| Request, one at a time, no other load | Before | After |
| --- | ---: | ---: |
| Search for a phrase | 1,389 ms | 29 ms |
| Search that matches nothing | 1,286 ms | 7 ms |
| Feed, first page | 44 ms | 7 ms |
| Trending | 210 ms | 2 ms (cached) |
| Feed, page 40,000 | 505 ms | 219 ms |

Under load (500,000 posts):

| Concurrent users | Before: req/s | Before: p50 / p95 | After: req/s | After: p50 / p95 |
| ---: | ---: | ---: | ---: | ---: |
| 25  | 22.0 | 32 / 1,300 ms | 24.7  | 11 / 28 ms |
| 50  | 41.1 | 59 / 420 ms | 49.4  | 12 / 36 ms |
| 100 | 46.2 | 620 / 1,900 ms | 96.7  | 14 / 54 ms |
| 200 | 33.6 | 4,000 / 11,000 ms | 145.2 | 320 / 570 ms |
| 400 | not run | not run | 143.5 | 1,600 / 2,400 ms |

A repeat of the 200-user run after the changes gave 139.8 req/s (p95 640 ms).
At 100 users the "after" figure is limited by how many requests the simulated users
send, not by the server.

What was wrong and what fixed it:

1. **Search scanned the whole table.** `ILIKE '%text%'` cannot use a normal index, so each
   search read all 500,000 posts. A search takes seconds, and while it ran it held a
   worker and the database, so every other request queued behind it. Votes went from
   23 ms to 430 ms at 100 users. Fix: trigram (`pg_trgm`) indexes on post title,
   post description and user pseudonym. The index took 12 seconds to build and is 34 MB
   for the descriptions. `sql/002_search_trigram.sql` adds it to an existing database.
2. **The feed counted every post on every page view.** An exact `COUNT(*)` over 500,000
   rows costs about 44 ms. The total is now reused for 5 seconds.
3. **Trending recalculated a week of posts and comments on every request.** The result
   is now reused for 30 seconds.

Both caches live inside one server process, so each worker keeps its own copy. The
side effect is that the total page count can be up to 5 seconds out of date and a
newly popular post can take up to 30 seconds to show in trending.

Still slow: jumping to a very deep page (page 40,000 takes 219 ms) because the database
has to skip 400,000 rows to get there. Fixing that properly means changing the feed to
"next page after this post" instead of page numbers, which changes the API.

To rerun at this size:

```bash
SEED_ARGS="--posts 500000 --comments-per-post 3 --votes-per-post 4" benchmarks/sweep.sh seed-only  # seeds, then runs
BENCH_POSTS=500000 SKIP_SEED=1 LEVELS="25 50 100 200 400" benchmarks/sweep.sh large-run
```

## Setup

- Machine: 4 vCPU, 16 GB RAM. Postgres 16, the load generator and the API all ran on
  it, so they competed for CPU. Numbers on separate hosts would be higher.
- Data: 2,000 users, 20,000 posts, 100,000 comments, about 200,000 votes.
- Traffic mix per user: 80% readers (feed 10 : detail 3 : search 1), 20% voters
  (vote 4 : comment 1). Think time 0.5 to 1.5 s. Feed page numbers are skewed toward
  early pages.
- Tokens are minted directly for seeded users, so signup and login are not measured.
- 45 seconds per level, 50 users/s ramp.

## Not covered

- Auth (signup, login, verify) cost.
- WebSocket fan-out.
- Multi-worker or multi-host scaling.
- Datasets beyond 500,000 posts, and very deep pagination.

## Reproducing

```bash
# Postgres reachable at $DATABASE_URL (default: localhost:5433/ichtaka)
uv sync --group bench
benchmarks/sweep.sh my-run                 # reseeds, then runs 50/100/200/400/800 users
benchmarks/sweep.sh before /path/to/worktree   # run another checkout of the code
```
