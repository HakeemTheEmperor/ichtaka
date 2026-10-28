#!/usr/bin/env bash
# Usage: benchmarks/sweep.sh <label> [app_dir]
# Reseeds, then runs the load test at several concurrency levels and prints a summary table.
set -euo pipefail
cd "$(dirname "$0")/.."
LABEL=${1:?label}; export APP_DIR=${2:-$PWD}
source benchmarks/env.sh
if [ -z "${SKIP_SEED:-}" ]; then
  # SEED_ARGS example: "--posts 500000 --comments-per-post 3 --votes-per-post 4"
  ( cd "$APP_DIR" && PYTHONPATH="$APP_DIR" "$OLDPWD/.venv/bin/python" "$OLDPWD/benchmarks/seed.py" ${SEED_ARGS:-} >/dev/null )
fi
for U in ${LEVELS:-50 100 200 400 800}; do
  benchmarks/run.sh "$LABEL/u$U" "$U" "${DURATION:-45s}" 50 >/dev/null 2>&1 || echo "run $U failed" >&2
done
python3 - "$LABEL" <<'PY'
import csv, sys
label = sys.argv[1]
print(f"{'users':>6} {'req/s':>8} {'p50 ms':>8} {'p95 ms':>8} {'p99 ms':>8} {'fail %':>7}")
import glob, os
for d in sorted(glob.glob(f"benchmarks/results/{label}/u*"), key=lambda p: int(p.split('/u')[-1])):
    row = [r for r in csv.DictReader(open(f"{d}/locust_stats.csv")) if r["Name"] == "Aggregated"][0]
    n, f = int(row["Request Count"]), int(row["Failure Count"])
    print(f"{d.split('/u')[-1]:>6} {float(row['Requests/s']):>8.1f} {row['50%']:>8} {row['95%']:>8} {row['99%']:>8} {100*f/n:>7.2f}")
PY
