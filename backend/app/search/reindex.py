"""Rebuild the search index from the canonical records.

Usage:  python -m app.search.reindex

The index is derived data. Records are indexed as they are published; this
command rebuilds everything, for example after the indexing rules change.
"""

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.catalog.models import Institution
from app.congress.models import Person, PositionHolding
from app.core.db import get_engine
from app.law.models import LegalInstrument, LegalProvision, ProvisionVersion
from app.legislation.models import LegislativeInitiative
from app.search.indexing import (
    index_entry,
    initiative_entry,
    institution_entry,
    provision_entry,
    representative_entry,
)
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
    holdings = select(PositionHolding, Person).join(Person, Person.id == PositionHolding.person_id)
    for holding, person in session.execute(holdings).yield_per(1000):
        index_entry(session, representative_entry(holding, person))
        count += 1
    provisions = (
        select(LegalProvision, LegalInstrument, ProvisionVersion.text)
        .join(LegalInstrument, LegalInstrument.id == LegalProvision.instrument_id)
        .join(ProvisionVersion, ProvisionVersion.provision_id == LegalProvision.id)
        .where(ProvisionVersion.superseded_at.is_(None), ProvisionVersion.text != "")
    )
    for provision, instrument, text in session.execute(provisions).yield_per(1000):
        index_entry(session, provision_entry(provision, instrument, text))
        count += 1
    session.commit()
    return count


if __name__ == "__main__":
    with Session(get_engine()) as _session:
        print(f"Documentos indexados: {reindex(_session)}")
