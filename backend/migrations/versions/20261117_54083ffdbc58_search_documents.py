"""search documents

The index is derived from the canonical records. After upgrading a database
that already holds records, rebuild it with:  python -m app.search.reindex

Revision ID: 54083ffdbc58
Revises: a493cfa65eac
Create Date: 2026-11-17 06:56:01.932701
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "54083ffdbc58"
down_revision: str | None = "a493cfa65eac"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS search")
    op.create_table(
        "document",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("record_type", sa.String(length=40), nullable=False),
        sa.Column("record_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("record_date", sa.Date(), nullable=True),
        sa.Column("jurisdiction_code", sa.String(length=2), nullable=False),
        sa.Column("tsv", postgresql.TSVECTOR(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_document")),
        sa.UniqueConstraint("record_type", "record_id", name=op.f("uq_document_record_type")),
        schema="search",
    )
    op.create_index(
        op.f("ix_document_record_date"), "document", ["record_date"], unique=False, schema="search"
    )
    op.create_index(
        op.f("ix_document_record_type"), "document", ["record_type"], unique=False, schema="search"
    )
    op.create_index(
        "ix_document_tsv",
        "document",
        ["tsv"],
        unique=False,
        schema="search",
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index("ix_document_tsv", table_name="document", schema="search", postgresql_using="gin")
    op.drop_index(op.f("ix_document_record_type"), table_name="document", schema="search")
    op.drop_index(op.f("ix_document_record_date"), table_name="document", schema="search")
    op.drop_table("document", schema="search")
    op.execute("DROP SCHEMA search")
