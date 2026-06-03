#!/usr/bin/env bash
# Start API (8000) + UI (5173). Run from repo root: ./scripts/dev.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ "${1:-}" == "--postgres" ]]; then
  docker compose up -d
  echo "Postgres started (optional checkpoints)"
fi

lsof -ti :8000 2>/dev/null | xargs kill 2>/dev/null || true
lsof -ti :5173 2>/dev/null | xargs kill 2>/dev/null || true
sleep 1

echo "Starting API on http://localhost:8000"
echo "  (loads repo-root .env automatically; set AWS_PROFILE there or in shell)"
"$ROOT/scripts/py" -m uvicorn api.main:app --reload --port 8000 &
API_PID=$!

cleanup() {
  kill "$API_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

for _ in $(seq 1 30); do
  if curl -sf http://localhost:8000/api/status >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

echo "Starting UI on http://localhost:5173"
cd ui && npm run dev
