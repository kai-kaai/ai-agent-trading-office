#!/usr/bin/env bash
# Start AI Agent Trading Office — API server + React dashboard (terminal mode)
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "=== AI Agent Trading Office ==="
echo ""

# Python deps
if ! python3 -c "import fastapi" 2>/dev/null; then
  echo "Installing Python dependencies..."
  pip3 install -r requirements.txt
fi

# Node deps
if [ ! -d "dashboard/node_modules" ]; then
  echo "Installing dashboard dependencies (npm)..."
  cd dashboard && npm install && cd ..
fi

# Start API server
echo "Starting API server on http://127.0.0.1:8080 ..."
python3 -m uvicorn server.app:app --host 127.0.0.1 --port 8080 &
API_PID=$!

cleanup() {
  echo ""
  echo "Shutting down..."
  kill $API_PID 2>/dev/null || true
  exit 0
}
trap cleanup INT TERM

# Start React dev server
echo "Starting dashboard on http://127.0.0.1:5173 ..."
echo ""
echo "  Open in browser: http://127.0.0.1:5173"
echo "  Press Ctrl+C to stop"
echo ""

cd dashboard
npm run dev -- --host 127.0.0.1