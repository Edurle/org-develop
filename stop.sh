#!/usr/bin/env bash

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_DIR="$ROOT_DIR/.pids"

stopped=0

for service in backend frontend; do
    pid_file="$PID_DIR/$service.pid"
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "Stopping $service (PID $pid)..."
            kill "$pid" 2>/dev/null
            # Also kill any child processes (e.g., uvicorn workers, node processes)
            pkill -P "$pid" 2>/dev/null || true
            stopped=$((stopped + 1))
        else
            echo "$service (PID $pid) is not running."
        fi
        rm -f "$pid_file"
    fi
done

# Fallback: kill by port if pid files missing
if [ "$stopped" -eq 0 ]; then
    echo "No PID files found, trying to kill by port..."
    for port in 8000 3000; do
        pid=$(lsof -ti :$port 2>/dev/null)
        if [ -n "$pid" ]; then
            echo "Killing process on port $port (PID $pid)..."
            kill $pid 2>/dev/null || true
        fi
    done
fi

echo "Done."
