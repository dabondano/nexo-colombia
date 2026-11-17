"""Rebuild the search index from the canonical records.

Usage:  python -m app.search.reindex

The index is derived data. Records are indexed as they are published; this
command rebuilds everything, for example after the indexing rules change.
"""

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.catalog.models import Institution
from app.core.db import get_engine
from app.legislation.models import LegislativeInitiative
from app.search.indexing import index_entry, initiative_entry, institution_entry
from app.search.models import SearchDocument


def reindex(session: Session) -> int:
    """Replace the whole index in one transaction. Returns the number of documents."""
    session.execute(delete(SearchDocument))
    count = 0
    for institution in session.scalars(select(Institution)).yield_per(1000):
        index_entry(session, institution_entry(institution))
        count += 1
    for initiative in session.scalars(select(LegislativeInitiative)).yield_per(1000):
        index_entry(session, initiative_entry(initiative))
        count += 1
    session.commit()
    return count


if __name__ == "__main__":
    with Session(get_engine()) as _session:
        print(f"Documentos indexados: {reindex(_session)}")
