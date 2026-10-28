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
- Dataset sizes beyond 20,000 posts. Search uses `ILIKE '%q%'`, which scans the table
  and will get slower as it grows.
- Vote counter correctness under concurrent votes on one post. The counters are still
  updated with an unlocked read-modify-write.

## Reproducing

```bash
# Postgres reachable at $DATABASE_URL (default: localhost:5433/ichtaka)
uv sync --group bench
benchmarks/sweep.sh my-run                 # reseeds, then runs 50/100/200/400/800 users
benchmarks/sweep.sh before /path/to/worktree   # run another checkout of the code
```
