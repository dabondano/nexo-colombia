"""Public, read-only endpoints for the source registry ("Fuentes")."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_session
from app.core.labels import SyncStatus
from app.sources.models import Source, SyncRun
from app.sources.schemas import SourceOut, SyncRunOut

router = APIRouter(prefix="/sources", tags=["sources"])

SessionDep = Annotated[Session, Depends(get_session)]


def _last_successful_sync(session: Session, source_id: uuid.UUID) -> SyncRunOut | None:
    run = session.scalars(
        select(SyncRun)
        .where(SyncRun.source_id == source_id, SyncRun.status == SyncStatus.SUCCEEDED.value)
        .order_by(SyncRun.finished_at.desc())
        .limit(1)
    ).first()
    return SyncRunOut.model_validate(run) if run else None


def _to_out(session: Session, source: Source) -> SourceOut:
    out = SourceOut.model_validate(source)
    out.last_successful_sync = _last_successful_sync(session, source.id)
    return out


@router.get("", response_model=list[SourceOut])
def list_sources(session: SessionDep) -> list[SourceOut]:
    sources = session.scalars(select(Source).order_by(Source.institution, Source.name)).all()
    return [_to_out(session, s) for s in sources]


@router.get("/{source_id}", response_model=SourceOut)
def get_source(source_id: uuid.UUID, session: SessionDep) -> SourceOut:
    source = session.get(Source, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Fuente no encontrada")
    return _to_out(session, source)


@router.get("/{source_id}/sync-runs", response_model=list[SyncRunOut])
def list_sync_runs(source_id: uuid.UUID, session: SessionDep) -> list[SyncRunOut]:
    if session.get(Source, source_id) is None:
        raise HTTPException(status_code=404, detail="Fuente no encontrada")
    runs = session.scalars(
        select(SyncRun)
        .where(SyncRun.source_id == source_id)
        .order_by(SyncRun.started_at.desc())
        .limit(50)
    ).all()
    return [SyncRunOut.model_validate(r) for r in runs]
