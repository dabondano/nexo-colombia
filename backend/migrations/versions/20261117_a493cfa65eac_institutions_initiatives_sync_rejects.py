"""institutions, initiatives, sync rejects

Revision ID: a493cfa65eac
Revises: 9e193878b159
Create Date: 2026-11-17 06:26:25.090275
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a493cfa65eac"
down_revision: str | None = "9e193878b159"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sync_reject",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("sync_run_id", sa.Uuid(), nullable=False),
        sa.Column("external_id", sa.String(length=300), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(
            ["sync_run_id"], ["core.sync_run.id"], name=op.f("fk_sync_reject_sync_run_id_sync_run")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sync_reject")),
        schema="core",
    )
    op.create_index(
        op.f("ix_sync_reject_sync_run_id"),
        "sync_reject",
        ["sync_run_id"],
        unique=False,
        schema="core",
    )
    op.create_table(
        "institution",
        sa.Column("official_code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("name_normalized", sa.Text(), nullable=False),
        sa.Column("nit", sa.String(length=20), nullable=True),
        sa.Column("orden", sa.String(length=50), nullable=True),
        sa.Column("suborden", sa.String(length=100), nullable=True),
        sa.Column("nivel", sa.String(length=100), nullable=True),
        sa.Column("clasificacion_organica", sa.String(length=200), nullable=True),
        sa.Column("sector", sa.String(length=200), nullable=True),
        sa.Column("naturaleza_juridica", sa.String(length=200), nullable=True),
        sa.Column("tipo_institucion", sa.String(length=100), nullable=True),
        sa.Column("departamento", sa.String(length=100), nullable=True),
        sa.Column("municipio", sa.String(length=100), nullable=True),
        sa.Column("website", sa.Text(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("estado", sa.String(length=50), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("jurisdiction_code", sa.String(length=2), nullable=False),
        sa.Column("source_record_id", sa.Uuid(), nullable=False),
        sa.Column("data_quality_status", sa.String(length=20), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["source_record_id"],
            ["core.source_record.id"],
            name=op.f("fk_institution_source_record_id_source_record"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_institution")),
        sa.UniqueConstraint("official_code", name=op.f("uq_institution_official_code")),
        schema="core",
    )
    op.create_index(
        op.f("ix_institution_clasificacion_organica"),
        "institution",
        ["clasificacion_organica"],
        unique=False,
        schema="core",
    )
    op.create_index(
        op.f("ix_institution_departamento"),
        "institution",
        ["departamento"],
        unique=False,
        schema="core",
    )
    op.create_index(
        op.f("ix_institution_name_normalized"),
        "institution",
        ["name_normalized"],
        unique=False,
        schema="core",
    )
    op.create_index(op.f("ix_institution_nit"), "institution", ["nit"], unique=False, schema="core")
    op.create_index(
        op.f("ix_institution_orden"), "institution", ["orden"], unique=False, schema="core"
    )
    op.create_index(
        op.f("ix_institution_source_record_id"),
        "institution",
        ["source_record_id"],
        unique=False,
        schema="core",
    )
    op.create_table(
        "legislative_initiative",
        sa.Column("source_key", sa.Text(), nullable=False),
        sa.Column("camara_number", sa.String(length=100), nullable=True),
        sa.Column("senado_number", sa.String(length=100), nullable=True),
        sa.Column("camara_filed_on", sa.Date(), nullable=True),
        sa.Column("senado_filed_on", sa.Date(), nullable=True),
        sa.Column("short_title", sa.Text(), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("title_normalized", sa.Text(), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=True),
        sa.Column("observations", sa.Text(), nullable=True),
        sa.Column("law_type", sa.String(length=100), nullable=True),
        sa.Column("authors_text", sa.Text(), nullable=True),
        sa.Column("authors_normalized", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=100), nullable=True),
        sa.Column("origin_chamber", sa.String(length=50), nullable=True),
        sa.Column("commission", sa.Text(), nullable=True),
        sa.Column("legislature", sa.String(length=20), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("jurisdiction_code", sa.String(length=2), nullable=False),
        sa.Column("source_record_id", sa.Uuid(), nullable=False),
        sa.Column("data_quality_status", sa.String(length=20), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["source_record_id"],
            ["core.source_record.id"],
            name=op.f("fk_legislative_initiative_source_record_id_source_record"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_legislative_initiative")),
        sa.UniqueConstraint("source_key", name=op.f("uq_legislative_initiative_source_key")),
        schema="core",
    )
    op.create_index(
        op.f("ix_legislative_initiative_camara_number"),
        "legislative_initiative",
        ["camara_number"],
        unique=False,
        schema="core",
    )
    op.create_index(
        op.f("ix_legislative_initiative_commission"),
        "legislative_initiative",
        ["commission"],
        unique=False,
        schema="core",
    )
    op.create_index(
        op.f("ix_legislative_initiative_law_type"),
        "legislative_initiative",
        ["law_type"],
        unique=False,
        schema="core",
    )
    op.create_index(
        op.f("ix_legislative_initiative_legislature"),
        "legislative_initiative",
        ["legislature"],
        unique=False,
        schema="core",
    )
    op.create_index(
        op.f("ix_legislative_initiative_senado_number"),
        "legislative_initiative",
        ["senado_number"],
        unique=False,
        schema="core",
    )
    op.create_index(
        op.f("ix_legislative_initiative_source_record_id"),
        "legislative_initiative",
        ["source_record_id"],
        unique=False,
        schema="core",
    )
    op.create_index(
        op.f("ix_legislative_initiative_status"),
        "legislative_initiative",
        ["status"],
        unique=False,
        schema="core",
    )
    op.drop_constraint(
        op.f("uq_source_record_source_id"), "source_record", schema="core", type_="unique"
    )
    op.create_index(
        "ix_source_record_source_external",
        "source_record",
        ["source_id", "external_id"],
        unique=False,
        schema="core",
    )
    op.create_unique_constraint(
        "uq_source_record_item_content_acquisition",
        "source_record",
        ["source_id", "external_id", "content_hash", "acquired_at"],
        schema="core",
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_source_record_item_content_acquisition", "source_record", schema="core", type_="unique"
    )
    op.drop_index("ix_source_record_source_external", table_name="source_record", schema="core")
    op.create_unique_constraint(
        op.f("uq_source_record_source_id"),
        "source_record",
        ["source_id", "external_id", "content_hash"],
        schema="core",
        postgresql_nulls_not_distinct=False,
    )
    op.drop_index(
        op.f("ix_legislative_initiative_status"), table_name="legislative_initiative", schema="core"
    )
    op.drop_index(
        op.f("ix_legislative_initiative_source_record_id"),
        table_name="legislative_initiative",
        schema="core",
    )
    op.drop_index(
        op.f("ix_legislative_initiative_senado_number"),
        table_name="legislative_initiative",
        schema="core",
    )
    op.drop_index(
        op.f("ix_legislative_initiative_legislature"),
        table_name="legislative_initiative",
        schema="core",
    )
    op.drop_index(
        op.f("ix_legislative_initiative_commission"),
        table_name="legislative_initiative",
        schema="core",
    )
    op.drop_index(
        op.f("ix_legislative_initiative_law_type"),
        table_name="legislative_initiative",
        schema="core",
    )
    op.drop_index(
        op.f("ix_legislative_initiative_camara_number"),
        table_name="legislative_initiative",
        schema="core",
    )
    op.drop_table("legislative_initiative", schema="core")
    op.drop_index(op.f("ix_institution_source_record_id"), table_name="institution", schema="core")
    op.drop_index(op.f("ix_institution_orden"), table_name="institution", schema="core")
    op.drop_index(op.f("ix_institution_nit"), table_name="institution", schema="core")
    op.drop_index(op.f("ix_institution_name_normalized"), table_name="institution", schema="core")
    op.drop_index(op.f("ix_institution_departamento"), table_name="institution", schema="core")
    op.drop_index(
        op.f("ix_institution_clasificacion_organica"), table_name="institution", schema="core"
    )
    op.drop_table("institution", schema="core")
    op.drop_index(op.f("ix_sync_reject_sync_run_id"), table_name="sync_reject", schema="core")
    op.drop_table("sync_reject", schema="core")
