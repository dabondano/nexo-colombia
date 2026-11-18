#!/usr/bin/env bash
# Synchronize every dataset from its official source, relink authors, rebuild search.
# Run weekly from cron; each run is listed in the staff panel and the audit log.
set -euo pipefail
cd "$(dirname "$0")/.."
echo "$(date -u +%FT%TZ) sync started"
docker compose exec -T api python -m app.ingestion.cli all
docker compose exec -T api python -m app.search.reindex
echo "$(date -u +%FT%TZ) sync finished"
