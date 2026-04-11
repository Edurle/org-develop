#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_DIR="$ROOT_DIR/.pids"

mkdir -p "$PID_DIR"

cleanup() {
    echo "Startup interrupted, cleaning up..."
    "$ROOT_DIR/stop.sh" 2>/dev/null || true
    exit 1
}
trap cleanup INT TERM

# Start backend
echo "Starting backend..."
(cd "$ROOT_DIR/backend" && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 & echo $! > "$PID_DIR/backend.pid") 

# Start frontend
echo "Starting frontend..."
(cd "$ROOT_DIR/frontend" && npm run dev & echo $! > "$PID_DIR/frontend.pid")

echo ""
echo "Dev servers started:"
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:3000"
echo ""
echo "Run ./stop.sh to stop all servers."

wait
