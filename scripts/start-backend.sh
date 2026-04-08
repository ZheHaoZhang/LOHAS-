#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_HOST="${API_HOST:-127.0.0.1}"
API_PORT="${API_PORT:-8000}"

cd "$ROOT_DIR"

if [ ! -d .venv ]; then
  echo "找不到 .venv，請先執行 ./scripts/setup.sh" >&2
  exit 1
fi

. .venv/bin/activate

exec uvicorn backend.app.main:app --host "$API_HOST" --port "$API_PORT" --reload
