#!/usr/bin/env bash
# Restore a backup made by backup.sh. Replaces the current database contents.
# Usage: deploy/scripts/restore.sh deploy/backups/nexo-YYYYMMDDTHHMMSSZ.dump
set -euo pipefail
cd "$(dirname "$0")/.."
dump="${1:?Usage: restore.sh path/to/backup.dump}"
[ -f "$dump" ] || { echo "No such file: $dump"; exit 1; }
read -r -p "This replaces the database with $dump. Type RESTORE to continue: " answer
[ "$answer" = "RESTORE" ] || { echo "Cancelled."; exit 1; }
docker compose stop web api
docker compose exec -T db pg_restore -U nexo -d nexo --clean --if-exists --no-owner < "$dump"
docker compose start api web
echo "Restored $dump."
