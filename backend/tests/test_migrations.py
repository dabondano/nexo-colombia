from alembic import command
from sqlalchemy import inspect

from app.core.db import CORE_SCHEMA, get_engine
from tests.conftest import alembic_config


def test_migrations_downgrade_and_upgrade_cleanly() -> None:
    cfg = alembic_config()
    command.downgrade(cfg, "base")
    assert "source" not in inspect(get_engine()).get_table_names(schema=CORE_SCHEMA)
    command.upgrade(cfg, "head")
    tables = set(inspect(get_engine()).get_table_names(schema=CORE_SCHEMA))
    assert {
        "source",
        "sync_run",
        "source_record",
        "sync_reject",
        "institution",
        "legislative_initiative",
    } <= tables
