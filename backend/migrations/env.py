"""Alembic environment: uses the application's settings and metadata."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, text

from app.auth import models as _auth_models  # noqa: F401  (registers tables)
from app.budget import models as _budget_models  # noqa: F401
from app.catalog import models as _catalog_models  # noqa: F401
from app.congress import models as _congress_models  # noqa: F401
from app.core import audit as _audit_models  # noqa: F401
from app.core import relationships as _relationship_models  # noqa: F401
from app.core.config import get_settings
from app.core.db import CORE_SCHEMA, Base
from app.law import models as _law_models  # noqa: F401
from app.legislation import models as _legislation_models  # noqa: F401
from app.procurement import models as _procurement_models  # noqa: F401
from app.review import models as _review_models  # noqa: F401
from app.search import models as _search_models  # noqa: F401
from app.sources import models as _sources_models  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=get_settings().owner_database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        include_schemas=True,
        version_table_schema=CORE_SCHEMA,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(get_settings().owner_database_url)
    with engine.connect() as connection:
        # The version table lives in the core schema, so it must exist first.
        connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {CORE_SCHEMA}"))
        connection.commit()
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            version_table_schema=CORE_SCHEMA,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
