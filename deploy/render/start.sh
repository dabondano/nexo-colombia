#!/usr/bin/env bash
# Starts the API (internal, 127.0.0.1:8000) and the web server (public, $PORT).
# If either stops, the container stops and the platform restarts it.
set -euo pipefail

cd /app/api
# Migrations as the owner when NEXO_MIGRATION_DATABASE_URL is set; then the
# restricted application account (NEXO_DATABASE_URL) gets its privileges.
alembic upgrade head
if [ -n "${NEXO_MIGRATION_DATABASE_URL:-}" ]; then
  python -m app.core.grants
fi
uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1 &

cd /app/web
PORT="${PORT:-10000}" HOSTNAME=0.0.0.0 node server.js &

wait -n
exit 1
