"""The restricted application account cannot rewrite history or the schema."""

import pytest
from sqlalchemy import Connection, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.core.grants import apply_grants

ROLE = "nexo_app_test"


@pytest.fixture
def app_role(session: Session) -> Connection:
    connection = session.connection()
    exists = connection.execute(text("SELECT 1 FROM pg_roles WHERE rolname = :r"), {"r": ROLE})
    if exists.first() is None:
        connection.execute(text(f"CREATE ROLE {ROLE} NOLOGIN"))
    apply_grants(connection, ROLE)
    session.commit()
    connection = session.connection()
    connection.execute(
        text(
            "INSERT INTO core.audit_event (id, action, details) "
            "VALUES (gen_random_uuid(), 'sign_in', '{}')"
        )
    )
    session.commit()
    return session.connection()


def as_app(connection: Connection, statement: str) -> None:
    """Runs one statement as the application account, then undoes it."""
    transaction = connection.begin_nested()
    try:
        connection.execute(text(f"SET LOCAL ROLE {ROLE}"))
        connection.execute(text(statement))
    finally:
        transaction.rollback()


@pytest.mark.parametrize(
    "statement",
    [
        "SELECT count(*) FROM core.institution",
        "SELECT count(*) FROM search.document",
        "INSERT INTO core.audit_event (id, action, details) VALUES (gen_random_uuid(), 'x', '{}')",
        "UPDATE core.institution SET name = name",
        "DELETE FROM core.relationship",
        # The one raw-layer deletion it may make (A-015).
        "SELECT core.prune_contract_raw_records()",
    ],
)
def test_the_application_can_do_its_work(app_role: Connection, statement: str) -> None:
    as_app(app_role, statement)


@pytest.mark.parametrize(
    "statement",
    [
        "UPDATE core.audit_event SET action = 'otro'",
        "DELETE FROM core.audit_event",
        "TRUNCATE core.audit_event",
        "UPDATE core.source_record SET content_hash = content_hash",
        "DELETE FROM core.source_record",
        "DELETE FROM core.sync_reject",
        "UPDATE core.content_review SET notes = ''",
        "CREATE TABLE core.intruso (id int)",
        "DROP TABLE core.institution",
        "ALTER TABLE core.institution ADD COLUMN x int",
        "UPDATE core.alembic_version SET version_num = version_num",
    ],
)
def test_the_application_cannot_rewrite_history_or_schema(
    app_role: Connection, statement: str
) -> None:
    with pytest.raises(DBAPIError, match="permission denied|must be owner"):
        as_app(app_role, statement)


def test_role_names_are_checked(session: Session) -> None:
    with pytest.raises(ValueError):
        apply_grants(session.connection(), "nexo; DROP TABLE x")


def test_a_role_with_broad_powers_is_refused(session: Session) -> None:
    connection = session.connection()
    exists = connection.execute(text("SELECT 1 FROM pg_roles WHERE rolname = 'nexo_broad_test'"))
    if exists.first() is None:
        connection.execute(text("CREATE ROLE nexo_broad_test NOLOGIN"))
    connection.execute(text("GRANT pg_write_all_data TO nexo_broad_test"))
    with pytest.raises(SystemExit, match="pg_write_all_data"):
        apply_grants(connection, "nexo_broad_test")
    session.rollback()
