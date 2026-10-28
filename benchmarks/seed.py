"""Seed a synthetic dataset directly in Postgres (fast, set-based SQL).

Usage: uv run python benchmarks/seed.py --users 2000 --posts 20000 --comments-per-post 5
"""
import argparse
import os
import sys

import psycopg2

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--users", type=int, default=2000)
    p.add_argument("--posts", type=int, default=20000)
    p.add_argument("--comments-per-post", type=float, default=5)
    p.add_argument("--votes-per-post", type=float, default=10)
    p.add_argument("--dsn", default=os.environ["DATABASE_URL"])
    a = p.parse_args()

    from src.database import Base, engine  # noqa: F401
    from src.auth.models.user_account import User_Account  # noqa: F401
    from src.post.models import Post  # noqa: F401
    from src.post_actions.models import Comment, Vote  # noqa: F401
    from src.notifications.models import Notification  # noqa: F401

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    conn = psycopg2.connect(a.dsn)
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO user_account (login_id, public_key, recovery_phrase_hashes, pseudonym)
        SELECT 'user_' || g, 'AAAA', '[]'::json, 'bench_user_' || g
        FROM generate_series(1, %s) g
        """,
        (a.users,),
    )

    cur.execute(
        """
        INSERT INTO posts (user_id, title, description, severity, status,
                           upvotes_count, downvotes_count, created_at, updated_at)
        SELECT 1 + (g %% %s), 'Report number ' || g || ' about an incident',
               'Synthetic description for report ' || g || ' ' || repeat('lorem ipsum ', 10),
               (ARRAY['low','medium','high'])[1 + g %% 3], 'UNVERIFIED', 0, 0,
               now() - (g || ' minutes')::interval, now()
        FROM generate_series(1, %s) g
        """,
        (a.users, a.posts),
    )

    n_comments = int(a.posts * a.comments_per_post)
    cur.execute(
        """
        INSERT INTO post_comments (post_id, user_id, content, created_at)
        SELECT 1 + (g %% %s), 1 + (g * 7 %% %s), 'Synthetic comment ' || g, now()
        FROM generate_series(1, %s) g
        """,
        (a.posts, a.users, n_comments),
    )

    # distinct (post, user) pairs; counters kept consistent with vote rows
    n_votes = int(a.posts * a.votes_per_post)
    cur.execute(
        """
        INSERT INTO post_votes (post_id, user_id, vote_type, created_at)
        SELECT DISTINCT ON (post_id, user_id) post_id, user_id, vt, now() FROM (
            SELECT 1 + (g %% %s) AS post_id, 1 + ((g / %s) * 197 + g * 13) %% %s AS user_id,
                   CASE WHEN g %% 4 = 0 THEN 'DOWNVOTE' ELSE 'UPVOTE' END::votetype AS vt
            FROM generate_series(1, %s) g
        ) s
        """,
        (a.posts, a.posts, a.users, n_votes),
    )
    cur.execute(
        """
        UPDATE posts p SET
          upvotes_count = COALESCE((SELECT count(*) FROM post_votes v WHERE v.post_id=p.id AND v.vote_type='UPVOTE'),0),
          downvotes_count = COALESCE((SELECT count(*) FROM post_votes v WHERE v.post_id=p.id AND v.vote_type='DOWNVOTE'),0)
        """
    )
    conn.commit()
    for t in ("user_account", "posts", "post_comments", "post_votes"):
        cur.execute(f"SELECT count(*) FROM {t}")
        print(t, cur.fetchone()[0])
    cur.execute("ANALYZE")
    conn.commit()


if __name__ == "__main__":
    main()
