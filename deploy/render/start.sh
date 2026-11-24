#!/usr/bin/env bash
# Starts the API (internal, 127.0.0.1:8000) and the web server (public, $PORT).
# If either stops, the container stops and the platform restarts it.
set -euo pipefail

cd /app/api
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1 &

cd /app/web
PORT="${PORT:-10000}" HOSTNAME=0.0.0.0 node server.js &

wait -n
exit 1
