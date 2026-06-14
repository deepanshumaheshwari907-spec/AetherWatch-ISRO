#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")"
python3 verify_system.py

python3 -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 &
API_PID=$!
python3 -m streamlit run frontend/app.py --server.port 8501 &
DASHBOARD_PID=$!

trap 'kill "$API_PID" "$DASHBOARD_PID" 2>/dev/null || true' INT TERM EXIT
wait "$API_PID" "$DASHBOARD_PID"
