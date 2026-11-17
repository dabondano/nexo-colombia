"""provenance tables

Revision ID: 9e193878b159
Revises: (none)
Create Date: 2026-11-17 06:11:35.677730
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "9e193878b159"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "source",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("external_ref", sa.String(length=200), nullable=False),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("institution", sa.String(length=300), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("data_types", sa.Text(), nullable=True),
        sa.Column("acquisition_method", sa.String(length=30), nullable=False),
        sa.Column("update_frequency", sa.String(length=100), nullable=True),
        sa.Column("reliability_class", sa.SmallInteger(), nullable=False),
        sa.Column("licence", sa.String(length=200), nullable=True),
        sa.Column("access_restrictions", sa.Text(), nullable=True),
        sa.Column("known_limitations", sa.Text(), nullable=True),
        sa.Column("verification_status", sa.String(length=20), nullable=False),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("jurisdiction_code", sa.String(length=2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "reliability_class BETWEEN 1 AND 7", name=op.f("ck_source_reliability_class_range")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source")),
        sa.UniqueConstraint("external_ref", name=op.f("uq_source_external_ref")),
        schema="core",
    )
    op.create_table(
        "sync_run",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("mode", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rows_seen", sa.Integer(), nullable=False),
        sa.Column("rows_new", sa.Integer(), nullable=False),
        sa.Column("rows_changed", sa.Integer(), nullable=False),
        sa.Column("rows_rejected", sa.Integer(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["source_id"], ["core.source.id"], name=op.f("fk_sync_run_source_id_source")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sync_run")),
        schema="core",
    )
    op.create_index(
        op.f("ix_sync_run_source_id"), "sync_run", ["source_id"], unique=False, schema="core"
    )
    op.create_table(
        "source_record",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        sa.Column("sync_run_id", sa.Uuid(), nullable=False),
        sa.Column("external_id", sa.String(length=300), nullable=False),
        sa.Column("original_url", sa.Text(), nullable=True),
        sa.Column(
            "acquired_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("extraction_method", sa.String(length=100), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("processing_history", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_id"], ["core.source.id"], name=op.f("fk_source_record_source_id_source")
        ),
        sa.ForeignKeyConstraint(
            ["sync_run_id"],
            ["core.sync_run.id"],
            name=op.f("fk_source_record_sync_run_id_sync_run"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source_record")),
        sa.UniqueConstraint(
            "source_id", "external_id", "content_hash", name=op.f("uq_source_record_source_id")
        ),
        schema="core",
    )
    op.create_index(
        op.f("ix_source_record_source_id"),
        "source_record",
        ["source_id"],
        unique=False,
        schema="core",
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_source_record_source_id"), table_name="source_record", schema="core")
    op.drop_table("source_record", schema="core")
    op.drop_index(op.f("ix_sync_run_source_id"), table_name="sync_run", schema="core")
    op.drop_table("sync_run", schema="core")
    op.drop_table("source", schema="core")
