"""Test fixtures.

Integration tests run against a real PostgreSQL database, created by the
migrations themselves, so the migrations are exercised on every run.
Set NEXO_TEST_DATABASE_URL to point at a disposable database.
"""

import os
from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

TEST_DATABASE_URL = os.environ.get(
    "NEXO_TEST_DATABASE_URL", "postgresql+psycopg://nexo:nexo@localhost:5432/nexo_test"
)
os.environ["NEXO_DATABASE_URL"] = TEST_DATABASE_URL

from app.core.db import CORE_SCHEMA, get_engine  # noqa: E402
from app.main import create_app  # noqa: E402

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def alembic_config() -> Config:
    cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "migrations"))
    return cfg


@pytest.fixture(scope="session", autouse=True)
def _migrated_database() -> Iterator[None]:
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text(f"DROP SCHEMA IF EXISTS {CORE_SCHEMA} CASCADE"))
    command.upgrade(alembic_config(), "head")
    yield
    with engine.begin() as conn:
        conn.execute(text(f"DROP SCHEMA IF EXISTS {CORE_SCHEMA} CASCADE"))


@pytest.fixture
def session() -> Iterator[Session]:
    engine = get_engine()
    with Session(engine, expire_on_commit=False) as s:
        yield s
    with engine.begin() as conn:
        conn.execute(
            text(
                f"TRUNCATE {CORE_SCHEMA}.source_record, {CORE_SCHEMA}.sync_run, "
                f"{CORE_SCHEMA}.source CASCADE"
            )
        )


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(create_app()) as c:
        yield c
