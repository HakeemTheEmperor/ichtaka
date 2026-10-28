"""Check that vote counters stay correct when many people vote at the same time.

For each scenario, fires votes concurrently, then compares every touched post's
stored counters (posts.upvotes_count / downvotes_count) with the real rows in
post_votes. Any difference is "drift": votes that were counted wrongly.

Usage: uv run python benchmarks/vote_consistency.py [--app-dir DIR] [--rounds N]
Needs a seeded database (benchmarks/seed.py) and benchmarks/env.sh sourced.
"""
import argparse
import asyncio
import os
import random
import subprocess
import sys
import time
from datetime import datetime, timedelta

import httpx
import jwt
import psycopg2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from src.utils.encoding import encode_ids  # noqa: E402

BASE = "http://localhost:8000"
SECRET = os.environ["JWT_SECRET_KEY"]
DSN = os.environ["DATABASE_URL"]
POSTS = [1, 2, 3, 4, 5]


def token(uid):
    return jwt.encode({"sub": str(uid), "exp": datetime.utcnow() + timedelta(hours=1)},
                      SECRET, algorithm=os.environ.get("JWT_ALGORITHM", "HS256"))


def reset_posts(cur):
    cur.execute("DELETE FROM post_votes WHERE post_id = ANY(%s)", (POSTS,))
    cur.execute("UPDATE posts SET upvotes_count=0, downvotes_count=0 WHERE id = ANY(%s)", (POSTS,))


def drift(cur):
    """Return (sum of |counter - rows| over test posts, error detail)."""
    cur.execute("""
        SELECT p.id, p.upvotes_count, p.downvotes_count,
          (SELECT count(*) FROM post_votes v WHERE v.post_id=p.id AND v.vote_type='UPVOTE'),
          (SELECT count(*) FROM post_votes v WHERE v.post_id=p.id AND v.vote_type='DOWNVOTE')
        FROM posts p WHERE p.id = ANY(%s) ORDER BY p.id""", (POSTS,))
    total, rows = 0, []
    for pid, up, down, real_up, real_down in cur.fetchall():
        total += abs(up - real_up) + abs(down - real_down)
        rows.append((pid, up, real_up, down, real_down))
    return total, rows


async def vote(client, uid, post, kind, stats):
    try:
        r = await client.post(f"/v1/posts/actions/{encode_ids(post)}/vote",
                              json={"vote_type": kind},
                              headers={"Authorization": f"Bearer {token(uid)}"})
        stats["status"][r.status_code] = stats["status"].get(r.status_code, 0) + 1
    except Exception as e:
        key = type(e).__name__
        stats["status"][key] = stats["status"].get(key, 0) + 1


async def scenario_many_users_one_post(client, n):
    """n different users upvote the same post at the same instant."""
    stats = {"status": {}}
    await asyncio.gather(*[vote(client, uid, 1, "upvote", stats) for uid in range(1, n + 1)])
    return stats


async def scenario_mixed(client, n, rounds):
    """n users each cast several random up/down votes (toggles, switches) across 5 posts."""
    stats = {"status": {}}
    for _ in range(rounds):
        await asyncio.gather(*[
            vote(client, uid, random.choice(POSTS), random.choice(["upvote", "downvote"]), stats)
            for uid in range(1, n + 1)])
    return stats


async def scenario_double_click(client, n):
    """n users each send the same vote twice at once (a double click)."""
    stats = {"status": {}}
    jobs = []
    for uid in range(1, n + 1):
        jobs += [vote(client, uid, 2, "upvote", stats), vote(client, uid, 2, "upvote", stats)]
    await asyncio.gather(*jobs)
    return stats


async def main_async(a, cur):
    results = []
    limits = httpx.Limits(max_connections=500, max_keepalive_connections=0)
    async with httpx.AsyncClient(base_url=BASE, timeout=120, limits=limits) as c:
        for name, fn in [
            ("200 users upvote one post at once", lambda: scenario_many_users_one_post(c, 200)),
            ("300 users, random up/down votes on 5 posts", lambda: scenario_mixed(c, 300, a.rounds)),
            ("150 users double-click the same vote", lambda: scenario_double_click(c, 150)),
        ]:
            reset_posts(cur); cur.connection.commit()
            t = time.time()
            stats = await fn()
            await asyncio.sleep(1)  # let in-flight work settle
            d, rows = drift(cur); cur.connection.commit()
            results.append((name, d, stats["status"], time.time() - t, rows))
    return results


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--app-dir", default=ROOT)
    p.add_argument("--rounds", type=int, default=5)
    a = p.parse_args()

    srv = subprocess.Popen([os.path.join(ROOT, ".venv/bin/uvicorn"), "--app-dir", a.app_dir,
                            "src.app:app", "--port", "8000", "--log-level", "error"], cwd=a.app_dir)
    try:
        for _ in range(60):
            try:
                if httpx.get(BASE + "/").status_code == 200:
                    break
            except Exception:
                time.sleep(0.5)
        conn = psycopg2.connect(DSN); cur = conn.cursor()
        results = asyncio.run(main_async(a, cur))
    finally:
        srv.kill()

    print(f"{'scenario':<46} {'wrong votes':>11}  {'http status counts'}")
    for name, d, status, secs, rows in results:
        print(f"{name:<46} {d:>11}  {dict(sorted(status.items(), key=str))}")
    if "-v" in sys.argv:
        for name, d, status, secs, rows in results:
            print(name, rows)


if __name__ == "__main__":
    main()
