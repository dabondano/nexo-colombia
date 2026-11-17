"""Generic ingestion pipeline: acquire, minimize, validate, publish.

Every dataset follows the same steps (docs/02-architecture.md, section 4):

1. Minimize: keep only the fields on the dataset's allow-list.
2. Validate and map: turn the row into canonical values, or reject it with a reason.
3. Publish: store the raw item in `core.source_record` (append-only, by content
   hash) and insert or update the canonical record.

The whole run happens in one transaction. If anything fails, no canonical data
changes, and the run is recorded as failed.
"""

import hashlib
import json
import uuid
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.labels import SyncMode, SyncStatus
from app.sources.models import Source, SourceRecord, SyncReject, SyncRun

Row = dict[str, Any]
Payload = dict[str, Any]

PROCESSING_NOTES = "processing_notes"
REPAIR_STEP = "repair"


class RowRejected(Exception):  # noqa: N818 (a validation outcome, not an error)
    """Raised by a dataset mapper when a row must not be published."""


@dataclass(frozen=True)
class SyncResult:
    sync_run_id: uuid.UUID
    rows_seen: int
    rows_new: int
    rows_changed: int
    rows_unchanged: int
    rows_rejected: int


@dataclass(frozen=True)
class DatasetSpec:
    """Everything the pipeline needs to know about one dataset."""

    source_ref: str
    extraction_method: str
    # Data minimization: only these source fields are ever stored.
    allowed_fields: frozenset[str]
    external_id: Callable[[Payload], str | None]
    original_url: Callable[[Payload], str | None]
    # Returns canonical column values; raises RowRejected for invalid rows. The
    # optional key PROCESSING_NOTES lists, in Spanish, any repair made to the
    # row; the notes are stored with the raw item and shown with the record.
    map_row: Callable[[Payload], dict[str, Any]]
    # Inserts or updates the canonical record. Returns True when it was inserted.
    upsert: Callable[[Session, str, dict[str, Any], uuid.UUID], bool]


def content_hash(payload: Payload) -> str:
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _published_at(row: Row) -> datetime | None:
    value = row.get(":updated_at")
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _latest_hashes(session: Session, source_id: uuid.UUID) -> dict[str, str]:
    """external_id -> content hash of the most recently acquired record."""
    rows = session.execute(
        select(SourceRecord.external_id, SourceRecord.content_hash)
        .where(SourceRecord.source_id == source_id)
        .order_by(SourceRecord.acquired_at)
    )
    return {external_id: digest for external_id, digest in rows}


def _record_failure(
    session: Session, source_id: uuid.UUID, started_at: datetime, error: Exception
) -> None:
    session.add(
        SyncRun(
            source_id=source_id,
            mode=SyncMode.FULL.value,
            status=SyncStatus.FAILED.value,
            started_at=started_at,
            finished_at=datetime.now(UTC),
            error=f"{type(error).__name__}: {error}"[:2000],
        )
    )
    session.commit()


def run_sync(session: Session, spec: DatasetSpec, rows: Iterable[Row]) -> SyncResult:
    source = session.scalar(select(Source).where(Source.external_ref == spec.source_ref))
    if source is None:
        raise LookupError(f"Source {spec.source_ref!r} is not in the registry")
    source_id = source.id
    started_at = datetime.now(UTC)

    try:
        run = SyncRun(source_id=source_id, mode=SyncMode.FULL.value, started_at=started_at)
        session.add(run)
        session.flush()

        known = _latest_hashes(session, source_id)
        seen_in_run: set[str] = set()
        seen = new = changed = unchanged = rejected = 0

        def reject(external_id: str | None, reason: str, payload: Payload) -> None:
            nonlocal rejected
            rejected += 1
            session.add(
                SyncReject(
                    sync_run_id=run.id, external_id=external_id, reason=reason, payload=payload
                )
            )

        for row in rows:
            seen += 1
            payload = {k: v for k, v in row.items() if k in spec.allowed_fields}
            external_id = spec.external_id(payload)
            if not external_id:
                reject(None, "Sin identificador en la fuente", payload)
                continue
            if external_id in seen_in_run:
                reject(external_id, "Identificador duplicado en la misma descarga", payload)
                continue
            seen_in_run.add(external_id)

            try:
                values = spec.map_row(payload)
            except RowRejected as exc:
                reject(external_id, str(exc), payload)
                continue

            notes: list[str] = values.pop(PROCESSING_NOTES, [])

            digest = content_hash(payload)
            if known.get(external_id) == digest:
                unchanged += 1
                continue

            record = SourceRecord(
                source_id=source_id,
                sync_run_id=run.id,
                external_id=external_id,
                original_url=spec.original_url(payload),
                acquired_at=started_at,
                published_at=_published_at(row),
                last_verified_at=started_at,
                content_hash=digest,
                extraction_method=spec.extraction_method,
                payload=payload,
                processing_history=[
                    {"step": "minimize", "kept_fields": sorted(payload)},
                    {"step": "map", "at": started_at.isoformat()},
                    *({"step": REPAIR_STEP, "note": note} for note in notes),
                ],
            )
            session.add(record)
            session.flush()
            if spec.upsert(session, external_id, values, record.id):
                new += 1
            else:
                changed += 1

        run.rows_seen = seen
        run.rows_new = new
        run.rows_changed = changed
        run.rows_rejected = rejected
        run.status = SyncStatus.SUCCEEDED.value
        run.finished_at = datetime.now(UTC)
        result = SyncResult(run.id, seen, new, changed, unchanged, rejected)
        session.commit()
        return result
    except Exception as exc:
        session.rollback()
        _record_failure(session, source_id, started_at, exc)
        raise
