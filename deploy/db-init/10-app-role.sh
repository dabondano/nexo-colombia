#!/usr/bin/env bash
# Runs once, when the database volume is first created (postgres image convention).
# Creates the restricted account the application connects as; the API grants its
# privileges at every start (app.core.grants).
set -euo pipefail
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  -v app_password="$NEXO_APP_DB_PASSWORD" <<'SQL'
CREATE ROLE nexo_app LOGIN PASSWORD :'app_password';
SQL
