#!/usr/bin/env bash
# Captures docker stats + Postgres slow-query log for the duration of one
# load test run. Meant to be started in the background right before k6,
# and stopped right after — see run_tier.sh for the wrapper that does this
# automatically.
#
# Usage:
#   ./observe.sh start <output_dir>
#   ./observe.sh stop
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.loadtest.yml}"
DB_CONTAINER="${DB_CONTAINER:-buska_db_loadtest}"
API_CONTAINER="${API_CONTAINER:-buska_api_loadtest}"
PID_FILE="/tmp/buska_loadtest_observe.pid"

cmd="${1:-}"

start() {
  local out_dir="${1:?output dir required}"
  mkdir -p "$out_dir"

  echo "[observe.sh] docker stats -> $out_dir/docker_stats.log"
  (
    while true; do
      echo "--- $(date -u +%Y-%m-%dT%H:%M:%SZ) ---"
      docker stats --no-stream --format \
        "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}" \
        "$DB_CONTAINER" "$API_CONTAINER" 2>/dev/null || true
      sleep 5
    done
  ) >> "$out_dir/docker_stats.log" 2>&1 &
  echo $! >> "$PID_FILE"

  echo "[observe.sh] tailing Postgres slow-query log -> $out_dir/postgres_slow_queries.log"
  # docker-compose.loadtest.yml sets log_min_duration_statement=200ms on the
  # db service; postgres logs to stderr, which `docker logs` follows.
  (docker logs -f "$DB_CONTAINER" 2>&1 | grep --line-buffered -i "duration:" ) \
    >> "$out_dir/postgres_slow_queries.log" 2>&1 &
  echo $! >> "$PID_FILE"

  echo "[observe.sh] gunicorn access/error logs -> $out_dir/api.log"
  (docker logs -f "$API_CONTAINER") >> "$out_dir/api.log" 2>&1 &
  echo $! >> "$PID_FILE"

  echo "[observe.sh] started (pids: $(tr '\n' ' ' < "$PID_FILE"))"
}

stop() {
  if [[ ! -f "$PID_FILE" ]]; then
    echo "[observe.sh] no pid file found, nothing to stop"
    return 0
  fi
  echo "[observe.sh] stopping observers..."
  while read -r pid; do
    kill "$pid" 2>/dev/null || true
  done < "$PID_FILE"
  rm -f "$PID_FILE"
  echo "[observe.sh] stopped"
}

case "$cmd" in
  start) start "${2:?output dir required}" ;;
  stop) stop ;;
  *)
    echo "Usage: $0 {start <output_dir>|stop}"
    exit 1
    ;;
esac
