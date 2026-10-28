"""Locust scenarios. Tokens are minted locally with the app's JWT secret for
seeded users, so login cost is not part of these numbers (auth is benchmarked
separately).

Env: JWT_SECRET_KEY, JWT_ALGORITHM, BENCH_USERS, BENCH_POSTS
"""
import os
import random
import sys
from datetime import datetime, timedelta

import jwt
from locust import HttpUser, between, task

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.utils.encoding import encode_ids  # noqa: E402

SECRET = os.environ["JWT_SECRET_KEY"]
ALG = os.environ.get("JWT_ALGORITHM", "HS256")
N_USERS = int(os.environ.get("BENCH_USERS", 2000))
N_POSTS = int(os.environ.get("BENCH_POSTS", 20000))
MAX_PAGE = max(1, N_POSTS // 10)


def token_for(uid: int) -> str:
    return jwt.encode(
        {"sub": str(uid), "pseudonym": f"bench_user_{uid}", "type": "access",
         "exp": datetime.utcnow() + timedelta(hours=2)},
        SECRET, algorithm=ALG,
    )


class Reader(HttpUser):
    """Browses the feed and opens posts; most of the traffic."""
    weight = 8
    wait_time = between(0.5, 1.5)

    def on_start(self):
        uid = random.randint(1, N_USERS)
        self.client.headers["Authorization"] = f"Bearer {token_for(uid)}"

    @task(10)
    def feed(self):
        page = min(int(random.paretovariate(1.2)), MAX_PAGE)  # mostly early pages
        self.client.get(f"/v1/posts/?page={page}&limit=10", name="GET /v1/posts (feed)")

    @task(3)
    def post_detail(self):
        self.client.get(f"/v1/posts/{encode_ids(random.randint(1, N_POSTS))}",
                        name="GET /v1/posts/{id}")

    @task(1)
    def search(self):
        self.client.get(f"/v1/search?q=number%20{random.randint(1, N_POSTS)}",
                        name="GET /v1/search")


class Voter(HttpUser):
    """Votes and comments on posts."""
    weight = 2
    wait_time = between(0.5, 1.5)

    def on_start(self):
        uid = random.randint(1, N_USERS)
        self.client.headers["Authorization"] = f"Bearer {token_for(uid)}"

    @task(4)
    def vote(self):
        pid = encode_ids(random.randint(1, N_POSTS))
        self.client.post(f"/v1/posts/actions/{pid}/vote",
                         json={"vote_type": random.choice(["upvote", "downvote"])},
                         name="POST /v1/posts/actions/{id}/vote")

    @task(1)
    def comment(self):
        pid = encode_ids(random.randint(1, N_POSTS))
        self.client.post(f"/v1/posts/actions/{pid}/comments",
                         json={"content": "load test comment"},
                         name="POST /v1/posts/actions/{id}/comments")
