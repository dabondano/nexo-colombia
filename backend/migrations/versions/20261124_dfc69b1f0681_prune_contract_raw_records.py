"""prune contract raw records

The one deletion allowed in the append-only raw layer (A-015, owner decision of
2026-11-24): SECOP II raw records whose contract has left the loading window.
SECURITY DEFINER so the restricted application role, which cannot delete from
core.source_record, can run exactly this and nothing broader.

Revision ID: dfc69b1f0681
Revises: 80980f730f21
Create Date: 2026-11-24 03:19:37.955408
"""

from collections.abc import Sequence

from alembic import op

revision: str = "dfc69b1f0681"
down_revision: str | None = "80980f730f21"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE FUNCTION core.prune_contract_raw_records() RETURNS integer
        LANGUAGE sql SECURITY DEFINER SET search_path = core, pg_temp AS $$
            WITH removed AS (
                DELETE FROM core.source_record AS raw
                USING core.source AS src
                WHERE raw.source_id = src.id
                  AND src.external_ref = 'datos.gov.co:jbjy-vk9h'
                  AND NOT EXISTS (
                      SELECT 1 FROM core.contract AS c WHERE c.source_key = raw.external_id
                  )
                RETURNING 1
            )
            SELECT count(*)::integer FROM removed
        $$
        """
    )
    op.execute("REVOKE ALL ON FUNCTION core.prune_contract_raw_records() FROM PUBLIC")


def downgrade() -> None:
    op.execute("DROP FUNCTION core.prune_contract_raw_records()")
