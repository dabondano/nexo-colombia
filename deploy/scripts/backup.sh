#!/usr/bin/env bash
# Daily database backup: a compressed pg_dump in deploy/backups/, keeping 14 days.
# Run from cron (docs/06-deployment-oracle.md). Copy backups off the server too.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p backups
file="backups/nexo-$(date -u +%Y%m%dT%H%M%SZ).dump"
docker compose exec -T db pg_dump -U nexo -Fc nexo > "$file.partial"
mv "$file.partial" "$file"
find backups -name 'nexo-*.dump' -mtime +14 -delete
echo "$(date -u +%FT%TZ) backup written: $file ($(du -h "$file" | cut -f1))"
