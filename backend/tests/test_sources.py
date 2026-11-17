import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.labels import AcquisitionMethod, SyncMode, SyncStatus, VerificationStatus
from app.sources.models import Source, SourceRecord, SyncRun


def make_source(**overrides: object) -> Source:
    values: dict[str, object] = {
        "external_ref": "test:fuente-de-prueba",
        "name": "Fuente de prueba (datos de ejemplo)",
        "institution": "Institución de prueba",
        "url": "https://example.org/datos",
        "category": "test",
        "acquisition_method": AcquisitionMethod.API.value,
        "reliability_class": 3,
        "verification_status": VerificationStatus.NOT_VERIFIED.value,
    }
    values.update(overrides)
    return Source(**values)


def test_list_is_empty_without_sources(client: TestClient, session: Session) -> None:
    response = client.get("/api/v1/sources")
    assert response.status_code == 200
    assert response.json() == []


def test_source_is_listed_with_last_successful_sync(client: TestClient, session: Session) -> None:
    source = make_source()
    session.add(source)
    session.flush()
    now = datetime.now(UTC)
    session.add_all(
        [
            SyncRun(
                source_id=source.id,
                mode=SyncMode.FULL.value,
                status=SyncStatus.SUCCEEDED.value,
                started_at=now - timedelta(days=2),
                finished_at=now - timedelta(days=2),
                rows_seen=10,
                rows_new=10,
            ),
            SyncRun(
                source_id=source.id,
                mode=SyncMode.INCREMENTAL.value,
                status=SyncStatus.SUCCEEDED.value,
                started_at=now - timedelta(days=1),
                finished_at=now - timedelta(days=1),
                rows_seen=12,
                rows_new=2,
                rows_rejected=1,
            ),
            SyncRun(
                source_id=source.id,
                mode=SyncMode.INCREMENTAL.value,
                status=SyncStatus.FAILED.value,
                started_at=now,
                finished_at=now,
                error="timeout",
            ),
        ]
    )
    session.commit()

    body = client.get("/api/v1/sources").json()
    assert len(body) == 1
    assert body[0]["name"] == "Fuente de prueba (datos de ejemplo)"
    assert body[0]["verification_status"] == "not_verified"
    # The failed run is newer, but only a successful run counts.
    assert body[0]["last_successful_sync"]["rows_seen"] == 12
    assert body[0]["last_successful_sync"]["rows_rejected"] == 1

    runs = client.get(f"/api/v1/sources/{source.id}/sync-runs").json()
    assert [r["status"] for r in runs] == ["failed", "succeeded", "succeeded"]


def test_unknown_source_returns_404(client: TestClient, session: Session) -> None:
    missing = uuid.uuid4()
    assert client.get(f"/api/v1/sources/{missing}").status_code == 404
    assert client.get(f"/api/v1/sources/{missing}/sync-runs").status_code == 404


def test_reliability_class_must_be_between_1_and_7(session: Session) -> None:
    session.add(make_source(reliability_class=9))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_source_record_is_append_only_by_content_hash(session: Session) -> None:
    source = make_source()
    session.add(source)
    session.flush()
    run = SyncRun(source_id=source.id, mode=SyncMode.FULL.value)
    session.add(run)
    session.flush()

    def record(content_hash: str) -> SourceRecord:
        return SourceRecord(
            source_id=source.id,
            sync_run_id=run.id,
            external_id="registro-1",
            content_hash=content_hash,
            extraction_method="test",
            payload={"campo": "valor"},
        )

    # A changed item (new hash) is a new row next to the old one.
    session.add_all([record("a" * 64), record("b" * 64)])
    session.commit()

    # The same item with the same content cannot be stored twice.
    session.add(record("a" * 64))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_registry_seed_is_idempotent(client: TestClient, session: Session) -> None:
    from app.sources.registry import REGISTRY, seed_registry

    assert seed_registry(session) == len(REGISTRY)
    assert seed_registry(session) == 0

    body = client.get("/api/v1/sources").json()
    assert len(body) == len(REGISTRY)
    assert all(s["verification_status"] == "verified" for s in body)
    assert all(s["last_successful_sync"] is None for s in body)
