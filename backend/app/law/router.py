"""Public, read-only endpoints for legal instruments ("Constitución")."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_session
from app.core.labels import DataQualityStatus
from app.core.provenance import load_provenance
from app.law.constitution import ARTICLE, PREAMBLE
from app.law.models import LegalInstrument, LegalProvision, ProvisionVersion
from app.law.schemas import (
    InstrumentOut,
    InstrumentSummary,
    OutlineItem,
    ProvisionOut,
    ProvisionRef,
    SegmentOut,
)
from app.search.indexing import excerpt

instruments_router = APIRouter(prefix="/instruments", tags=["law"])
provisions_router = APIRouter(prefix="/provisions", tags=["law"])

SessionDep = Annotated[Session, Depends(get_session)]
EXCERPT_LENGTH = 110
# Provisions that have a page of their own; divisions only appear in the outline.
READABLE_KINDS = (PREAMBLE, ARTICLE)


@instruments_router.get("", response_model=list[InstrumentSummary])
def list_instruments(session: SessionDep) -> list[LegalInstrument]:
    return list(
        session.scalars(
            select(LegalInstrument).order_by(LegalInstrument.hierarchy_level, LegalInstrument.year)
        )
    )


@instruments_router.head("/{slug}", include_in_schema=False)
def instrument_exists(slug: str, session: SessionDep) -> Response:
    """Existence check without the outline, used by the web app to answer 404 early."""
    found = session.scalar(select(LegalInstrument.id).where(LegalInstrument.slug == slug))
    return Response(status_code=200 if found else 404)


@instruments_router.get("/{slug}", response_model=InstrumentOut)
def get_instrument(slug: str, session: SessionDep) -> InstrumentOut:
    instrument = session.scalar(select(LegalInstrument).where(LegalInstrument.slug == slug))
    if instrument is None:
        raise HTTPException(status_code=404, detail="Norma no encontrada")
    rows = session.execute(
        select(LegalProvision, ProvisionVersion.text)
        .outerjoin(
            ProvisionVersion,
            (ProvisionVersion.provision_id == LegalProvision.id)
            & ProvisionVersion.superseded_at.is_(None),
        )
        .where(LegalProvision.instrument_id == instrument.id)
        .order_by(LegalProvision.position)
    ).all()
    outline = [
        OutlineItem(
            id=provision.id,
            parent_id=provision.parent_id,
            path=provision.path,
            kind=provision.kind,
            label=provision.label,
            heading=provision.heading,
            excerpt=excerpt(text, EXCERPT_LENGTH) if text and provision.kind == ARTICLE else None,
            data_quality_status=provision.data_quality_status,
        )
        for provision, text in rows
    ]
    articles = [item for item in outline if item.kind == ARTICLE]
    return InstrumentOut(
        **InstrumentSummary.model_validate(instrument).model_dump(),
        article_count=len(articles),
        articles_needing_review=sum(
            item.data_quality_status == DataQualityStatus.INCOMPLETE.value for item in articles
        ),
        outline=outline,
        provenance=load_provenance(session, instrument.source_record_id),
    )


def _ref(provision: LegalProvision | None) -> ProvisionRef | None:
    if provision is None:
        return None
    return ProvisionRef(
        id=provision.id, path=provision.path, label=provision.label, heading=provision.heading
    )


def _neighbour(session: Session, provision: LegalProvision, *, after: bool) -> ProvisionRef | None:
    """The readable provision just before or after this one in reading order."""
    statement = select(LegalProvision).where(
        LegalProvision.instrument_id == provision.instrument_id,
        LegalProvision.kind.in_(READABLE_KINDS),
    )
    if after:
        statement = statement.where(LegalProvision.position > provision.position).order_by(
            LegalProvision.position
        )
    else:
        statement = statement.where(LegalProvision.position < provision.position).order_by(
            LegalProvision.position.desc()
        )
    return _ref(session.scalar(statement.limit(1)))


@instruments_router.head("/{slug}/provisions/{path:path}", include_in_schema=False)
def provision_exists(slug: str, path: str, session: SessionDep) -> Response:
    """Existence check without the provision body, used by the web app to answer 404 early."""
    found = session.scalar(
        select(LegalProvision.id)
        .join(LegalInstrument, LegalInstrument.id == LegalProvision.instrument_id)
        .where(LegalInstrument.slug == slug, LegalProvision.path == path)
    )
    return Response(status_code=200 if found else 404)


@instruments_router.get("/{slug}/provisions/{path:path}", response_model=ProvisionOut)
def get_provision_by_path(slug: str, path: str, session: SessionDep) -> ProvisionOut:
    """A provision by its stable key, e.g. `articulo-11`: addresses that survive a reload."""
    provision = session.scalar(
        select(LegalProvision)
        .join(LegalInstrument, LegalInstrument.id == LegalProvision.instrument_id)
        .where(LegalInstrument.slug == slug, LegalProvision.path == path)
    )
    if provision is None:
        raise HTTPException(status_code=404, detail="Disposición no encontrada")
    return _provision_out(session, provision)


@provisions_router.head("/{provision_id}", include_in_schema=False)
def provision_id_exists(provision_id: uuid.UUID, session: SessionDep) -> Response:
    """Existence check without the provision body, used by the web app to answer 404 early."""
    found = session.scalar(select(LegalProvision.id).where(LegalProvision.id == provision_id))
    return Response(status_code=200 if found else 404)


@provisions_router.get("/{provision_id}", response_model=ProvisionOut)
def get_provision(provision_id: uuid.UUID, session: SessionDep) -> ProvisionOut:
    provision = session.get(LegalProvision, provision_id)
    if provision is None:
        raise HTTPException(status_code=404, detail="Disposición no encontrada")
    return _provision_out(session, provision)


def _provision_out(session: Session, provision: LegalProvision) -> ProvisionOut:
    instrument = session.get_one(LegalInstrument, provision.instrument_id)
    version = session.scalar(
        select(ProvisionVersion).where(
            ProvisionVersion.provision_id == provision.id, ProvisionVersion.superseded_at.is_(None)
        )
    )
    ancestors: list[ProvisionRef] = []
    parent_id = provision.parent_id
    while parent_id is not None:
        parent = session.get_one(LegalProvision, parent_id)
        ancestors.insert(0, _ref(parent))  # type: ignore[arg-type]
        parent_id = parent.parent_id
    return ProvisionOut(
        id=provision.id,
        path=provision.path,
        kind=provision.kind,
        label=provision.label,
        heading=provision.heading,
        data_quality_status=provision.data_quality_status,
        instrument=InstrumentSummary.model_validate(instrument),
        ancestors=ancestors,
        segments=[SegmentOut(**segment) for segment in (version.segments if version else [])],
        recorded_at=version.recorded_at if version else None,
        version_id=version.id if version else None,
        previous=_neighbour(session, provision, after=False),
        next=_neighbour(session, provision, after=True),
        provenance=load_provenance(session, provision.source_record_id),
    )
