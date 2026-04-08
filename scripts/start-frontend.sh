#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
API_HOST="${API_HOST:-127.0.0.1}"
API_PORT="${API_PORT:-8000}"

cd "$ROOT_DIR/frontend"

if [ ! -d node_modules ]; then
  echo "找不到 frontend/node_modules，請先執行 ./scripts/setup.sh" >&2
  exit 1
fi

export VITE_API_BASE_URL="${VITE_API_BASE_URL:-http://${API_HOST}:${API_PORT}}"

exec npm run dev -- --host "$FRONTEND_HOST" --port "$FRONTEND_PORT"
