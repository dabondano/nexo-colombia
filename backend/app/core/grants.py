"""Privileges of the restricted database account the application uses in production.

Usage:  python -m app.core.grants   (with NEXO_MIGRATION_DATABASE_URL set to the owner)

The owner runs migrations; the application connects as NEXO_APP_DB_ROLE
(default "nexo_app"), which must already exist (one SQL line or the hosting
console; see the deployment guides). This grants it reading and writing on the
data tables, and only reading and adding on the tables that are append-only
by design, so neither a bug nor a leaked application password can rewrite
history:

- core.audit_event   security audit log (a trigger also rejects changes)
- core.source_record raw items as acquired (ADR-004)
- core.sync_reject   rejected rows with their reasons
- core.content_review legal reviews, never edited

It cannot create, alter, drop or truncate tables. Idempotent; run after every
migration so new tables are covered.
"""

import re

from sqlalchemy import Connection, create_engine, text

from app.core.config import get_settings
from app.core.db import CORE_SCHEMA, SEARCH_SCHEMA

APPEND_ONLY = ("audit_event", "source_record", "sync_reject", "content_review")
SCHEMAS = (CORE_SCHEMA, SEARCH_SCHEMA)
_ROLE_NAME = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")


def apply_grants(connection: Connection, role: str) -> None:
    if not _ROLE_NAME.fullmatch(role):
        raise ValueError(f"Nombre de rol no válido: {role!r}")
    exists = connection.execute(text("SELECT 1 FROM pg_roles WHERE rolname = :r"), {"r": role})
    if exists.first() is None:
        raise SystemExit(f"El rol {role} no existe; créelo antes (vea la guía de despliegue).")
    problem = broad_powers(connection, role)
    if problem:
        raise SystemExit(
            f"El rol {role} {problem}, así que las restricciones no tendrían efecto. "
            "Créelo con SQL (CREATE ROLE ... LOGIN PASSWORD ...), no desde el panel del proveedor."
        )
    schemas = ", ".join(SCHEMAS)
    statements = [
        f"REVOKE ALL ON ALL TABLES IN SCHEMA {schemas} FROM {role}",
        f"GRANT USAGE ON SCHEMA {schemas} TO {role}",
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA {schemas} TO {role}",
        f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA {schemas} TO {role}",
        *(
            f"REVOKE UPDATE, DELETE, TRUNCATE ON {CORE_SCHEMA}.{table} FROM {role}"
            for table in APPEND_ONLY
        ),
        # The schema version is read, never written, by the application.
        f"REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON {CORE_SCHEMA}.alembic_version FROM {role}",
    ]
    for statement in statements:
        connection.execute(text(statement))


def broad_powers(connection: Connection, role: str) -> str | None:
    """Why the role could bypass table privileges, or None. On Neon, roles made in the
    console join neon_superuser, which holds pg_write_all_data."""
    row = connection.execute(
        text(
            "SELECT rolsuper, rolbypassrls, "
            "pg_has_role(:r, 'pg_write_all_data', 'USAGE') AS writes_all "
            "FROM pg_roles WHERE rolname = :r"
        ),
        {"r": role},
    ).one()
    if row.rolsuper:
        return "es superusuario"
    if row.writes_all:
        return "puede escribir en todas las tablas (pg_write_all_data, p. ej. neon_superuser)"
    if row.rolbypassrls:
        return "omite la seguridad por filas (BYPASSRLS)"
    return None


def main() -> None:
    settings = get_settings()
    engine = create_engine(settings.owner_database_url)
    with engine.begin() as connection:
        apply_grants(connection, settings.app_db_role)
    print(f"Permisos aplicados al rol {settings.app_db_role}.")


if __name__ == "__main__":
    main()
