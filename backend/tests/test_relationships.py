import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.relationships import Relationship, public_only
from app.ingestion.datasets import entities
from app.ingestion.pipeline import run_sync
from app.sources.models import SourceRecord
from app.sources.registry import seed_registry
from tests.samples import entity_row


def link(**overrides: object) -> Relationship:
    values: dict[str, object] = {
        "subject_type": "person",
        "subject_id": uuid.uuid4(),
        "predicate": "author_of",
        "object_type": "legislative_initiative",
        "object_id": uuid.uuid4(),
        "confidence_class": "analytical_association",
        "epistemic_label": "hipotesis_analitica",
        "method_note": "Regla de ejemplo",
    }
    values.update(overrides)
    return Relationship(**values)


def test_an_analytical_association_needs_a_method_note(session: Session) -> None:
    session.add(link(method_note=None))
    with pytest.raises(IntegrityError, match="relationship_has_source_or_method"):
        session.flush()
    session.rollback()


def test_other_classes_need_a_source_record(session: Session) -> None:
    session.add(link(confidence_class="verified_official", epistemic_label="hecho_documentado"))
    with pytest.raises(IntegrityError, match="relationship_has_source_or_method"):
        session.flush()
    session.rollback()


def test_the_same_link_is_stored_once(session: Session) -> None:
    first = link()
    session.add(first)
    session.flush()
    session.add(link(subject_id=first.subject_id, object_id=first.object_id))
    with pytest.raises(IntegrityError):
        session.flush()
    session.rollback()


def test_unverified_claims_are_never_public(session: Session) -> None:
    seed_registry(session)
    run_sync(session, entities.SPEC, [entity_row("9001")])
    record_id = session.scalars(select(SourceRecord.id)).first()
    session.add(link())
    session.add(
        link(
            confidence_class="unverified_claim",
            epistemic_label="no_verificado",
            source_record_id=record_id,
        )
    )
    session.flush()
    shown = session.scalars(select(Relationship.confidence_class).where(public_only())).all()
    assert shown == ["analytical_association"]
