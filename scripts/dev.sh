#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_HOST="${API_HOST:-127.0.0.1}"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
BACKEND_PID=""

pick_port() {
  python3 - "$1" <<'PY'
import socket
import sys

start_port = int(sys.argv[1])

for port in range(start_port, start_port + 50):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(("127.0.0.1", port))
    except OSError:
        sock.close()
        continue

    sock.close()
    print(port)
    raise SystemExit(0)

raise SystemExit(1)
PY
}

API_PORT="${API_PORT:-$(pick_port 8000)}"
FRONTEND_PORT="${FRONTEND_PORT:-$(pick_port 5173)}"
export API_HOST API_PORT FRONTEND_HOST FRONTEND_PORT

cleanup() {
  if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID"
    wait "$BACKEND_PID" 2>/dev/null || true
  fi
}

trap cleanup EXIT INT TERM

"$ROOT_DIR/scripts/start-backend.sh" &
BACKEND_PID=$!

for _ in $(seq 1 20); do
  if curl -fsS "http://${API_HOST}:${API_PORT}/api/health" >/dev/null 2>&1; then
    break
  fi

  if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo "Backend 啟動失敗" >&2
    exit 1
  fi

  sleep 1
done

echo "Backend 啟動中：http://${API_HOST}:${API_PORT}"
echo "Frontend 啟動中：http://${FRONTEND_HOST}:${FRONTEND_PORT}"

"$ROOT_DIR/scripts/start-frontend.sh"
