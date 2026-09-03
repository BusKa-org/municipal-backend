#!/usr/bin/env bash
# Runs one full tier per the plan's "Execution procedure":
#   1. generate/refresh data for the tier
#   2. quick internal smoke pass (handled by k6's own ramp-up here)
#   3. start observe.sh
#   4. run the full k6 scenario mix
#   5. stop observe.sh, collect everything into results/<tier>-<timestamp>/
#
# Usage:
#   ./loadtest/run_tier.sh <tier> [--data-source <tier>] [--extra <scenario,scenario>]
#
# Examples:
#   ./loadtest/run_tier.sh smoke
#   ./loadtest/run_tier.sh baseline
#   ./loadtest/run_tier.sh load-spike --data-source load
#   ./loadtest/run_tier.sh load --extra routing_proxy,batch_trip_generation
#
# Assumes:
#   - docker-compose.loadtest.yml is already up (`docker compose -f docker-compose.loadtest.yml up -d --build`)
#   - the host Python env has the app installed (`uv sync` or `pip install -e .` from buska-backend/)
#   - k6 is installed on the host (`brew install k6` or see https://k6.io/docs/get-started/installation/)
set -euo pipefail

TIER="${1:?Usage: run_tier.sh <tier> [--data-source <tier>] [--extra <scenario,scenario>]}"
shift || true

DATA_SOURCE="$TIER"
EXTRA=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --data-source) DATA_SOURCE="$2"; shift 2 ;;
    --extra) EXTRA="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

cd "$(dirname "$0")/.."  # buska-backend/
LOADTEST_DIR="loadtest"
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
RESULT_DIR="$LOADTEST_DIR/results/${TIER}-${TIMESTAMP}"
mkdir -p "$RESULT_DIR"

export DB_HOST="${DB_HOST:-localhost}"
export DB_PORT="${DB_PORT:-5432}"
export DB_USER="${DB_USER:-buska_user}"
export DB_PASSWORD="${DB_PASSWORD:-buska_pass}"
export DB_NAME="${DB_NAME:-buska_db}"
export FLASK_ENV="${FLASK_ENV:-development}"  # generator only needs DB access, not prod secret validation
BASE_URL="${BASE_URL:-http://localhost:5000}"

echo "=================================================================="
echo " BusKá Load Test — tier: $TIER  (data source: $DATA_SOURCE)"
echo " Results: $RESULT_DIR"
echo "=================================================================="

echo "==> [1/5] Sanity check: API health"
if ! curl -sf "$BASE_URL/health" > /dev/null; then
  echo "API not reachable at $BASE_URL/health — is docker-compose.loadtest.yml up?"
  exit 1
fi

if [[ "$DATA_SOURCE" == "$TIER" ]]; then
  echo "==> [2/5] Generating data for tier $TIER"
  python "$LOADTEST_DIR/generate_data.py" \
    --tier "$LOADTEST_DIR/tiers/${TIER}.json" \
    --export "$LOADTEST_DIR/exports/${TIER}_export.json" \
    | tee "$RESULT_DIR/generate_data.log"
else
  echo "==> [2/5] Reusing dataset from tier '$DATA_SOURCE' (no generation needed)"
  if [[ ! -f "$LOADTEST_DIR/exports/${DATA_SOURCE}_export.json" ]]; then
    echo "Expected $LOADTEST_DIR/exports/${DATA_SOURCE}_export.json to already exist. Run that tier first."
    exit 1
  fi
fi

echo "==> [3/5] Starting observability capture"
bash "$LOADTEST_DIR/observe.sh" start "$RESULT_DIR"
trap 'bash "'"$LOADTEST_DIR"'/observe.sh" stop' EXIT

echo "==> [4/5] Running k6"
K6_ARGS=(run "$LOADTEST_DIR/k6/main.js"
  -e "TIER=$TIER"
  -e "DATA_SOURCE=$DATA_SOURCE"
  -e "BASE_URL=$BASE_URL"
  --summary-export "$RESULT_DIR/k6_summary.json")
# The per-request JSON stream (`--out json`) is opt-in (K6_RAW=1). It is huge
# and, on long/high-VU runs (e.g. the multi-hour soak), grows to tens of GB and
# starves k6's own event loop — inflating latencies and effectively invalidating
# the run. The aggregated --summary-export above is all the analysis needs.
if [[ "${K6_RAW:-0}" == "1" ]]; then
  K6_ARGS+=(--out "json=$RESULT_DIR/k6_raw.jsonl")
fi
if [[ -n "$EXTRA" ]]; then
  K6_ARGS+=(-e "EXTRA_SCENARIOS=$EXTRA")
fi

set +e
k6 "${K6_ARGS[@]}" | tee "$RESULT_DIR/k6_stdout.log"
K6_EXIT=$?
set -e

echo "==> [5/5] Stopping observability capture"
bash "$LOADTEST_DIR/observe.sh" stop
trap - EXIT

echo "=================================================================="
echo " Done. k6 exit code: $K6_EXIT"
echo " Results: $RESULT_DIR"
echo "=================================================================="
exit $K6_EXIT
