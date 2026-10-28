#!/usr/bin/env bash
# Usage: benchmarks/run.sh <label> [users] [duration] [spawn_rate]
# Expects Postgres reachable at $DATABASE_URL and a seeded dataset.
set -euo pipefail
cd "$(dirname "$0")/.."
LABEL=${1:?label}; USERS=${2:-100}; DUR=${3:-60s}; RATE=${4:-20}
OUT=benchmarks/results/$LABEL; mkdir -p "$OUT"

source benchmarks/env.sh
WORKERS=${WORKERS:-1}

uv run uvicorn src.app:app --port 8000 --workers "$WORKERS" --log-level warning &
SRV=$!; trap 'kill $SRV 2>/dev/null || true' EXIT
for _ in $(seq 60); do curl -sf localhost:8000/ >/dev/null && break; sleep 0.5; done

uv run locust -f benchmarks/locustfile.py --headless --host http://localhost:8000 \
  -u "$USERS" -r "$RATE" -t "$DUR" --csv "$OUT/locust" --only-summary 2>&1 | tail -30
