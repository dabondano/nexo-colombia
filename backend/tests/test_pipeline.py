from collections.abc import Iterator

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.catalog.models import Institution
from app.ingestion.datasets import bills, entities
from app.ingestion.pipeline import run_sync
from app.legislation.models import LegislativeInitiative
from app.sources.models import SourceRecord, SyncReject, SyncRun
from app.sources.registry import seed_registry
from tests.samples import Row, bill_row, entity_row


def count(session: Session, model: type) -> int:
    return session.scalar(select(func.count()).select_from(model)) or 0


@pytest.fixture
def registry(session: Session) -> None:
    seed_registry(session)


def test_sync_publishes_records_with_provenance(session: Session, registry: None) -> None:
    result = run_sync(session, entities.SPEC, [entity_row("9001"), entity_row("9002")])

    assert (result.rows_seen, result.rows_new, result.rows_rejected) == (2, 2, 0)
    institution = session.scalars(
        select(Institution).where(Institution.official_code == "9001")
    ).one()
    record = session.get(SourceRecord, institution.source_record_id)
    assert record is not None
    assert record.external_id == "9001"
    assert record.sync_run_id == result.sync_run_id
    assert record.original_url == "https://www.datos.gov.co/d/h7zv-k39x"
    assert record.published_at is not None
    assert len(record.content_hash) == 64

    run = session.get(SyncRun, result.sync_run_id)
    assert run is not None
    assert (run.status, run.rows_seen, run.rows_new) == ("succeeded", 2, 2)
    assert run.finished_at is not None


def test_only_allow_listed_fields_are_stored(session: Session, registry: None) -> None:
    run_sync(session, entities.SPEC, [entity_row("9001"), entity_row("9002", nombre="")])

    record = session.scalars(select(SourceRecord)).one()
    reject = session.scalars(select(SyncReject)).one()
    for stored in (record.payload, reject.payload):
        assert set(stored) <= entities.ALLOWED_FIELDS
        assert "email" not in stored
        assert "nombre_representante" not in stored
        assert "ccb_telefono" not in stored


def test_invalid_rows_are_rejected_with_a_reason_and_not_published(
    session: Session, registry: None
) -> None:
    rows = [
        bill_row("proyecto-valido"),
        bill_row("proyecto-valido", proyecto="La misma dirección, otra fila"),
        bill_row("fila-de-relleno", t_tulo=".. FALLA EN EL APLICATIVO..."),
        bill_row("sin-enlace", link_del_proyecto={"url": "No Aplica"}),
    ]
    result = run_sync(session, bills.SPEC, rows)

    assert (result.rows_seen, result.rows_new, result.rows_rejected) == (4, 1, 3)
    assert count(session, LegislativeInitiative) == 1
    reasons = sorted(r.reason for r in session.scalars(select(SyncReject)))
    assert reasons == [
        "Fila de relleno del sistema de origen (falla en el aplicativo)",
        "Identificador duplicado en la misma descarga",
        "Sin identificador en la fuente",
    ]


def test_repeating_a_sync_changes_nothing(session: Session, registry: None) -> None:
    rows = [entity_row("9001"), entity_row("9002")]
    run_sync(session, entities.SPEC, rows)
    second = run_sync(session, entities.SPEC, rows)

    assert (second.rows_new, second.rows_changed, second.rows_unchanged) == (0, 0, 2)
    assert count(session, Institution) == 2
    assert count(session, SourceRecord) == 2
    assert count(session, SyncRun) == 2


def test_a_changed_row_adds_a_version_and_keeps_the_earlier_one(
    session: Session, registry: None
) -> None:
    run_sync(session, entities.SPEC, [entity_row("9001")])
    first = session.scalars(select(Institution)).one()
    first_record_id = first.source_record_id

    result = run_sync(
        session, entities.SPEC, [entity_row("9001", nombre="ALCALDÍA DE EJEMPLO - RENOMBRADA")]
    )
    assert (result.rows_new, result.rows_changed) == (0, 1)

    session.expire_all()
    institution = session.scalars(select(Institution)).one()
    assert institution.id == first.id
    assert institution.name == "ALCALDÍA DE EJEMPLO - RENOMBRADA"
    assert institution.source_record_id != first_record_id
    # Nothing was overwritten: both raw versions exist.
    versions = session.scalars(select(SourceRecord).order_by(SourceRecord.acquired_at)).all()
    assert [v.payload["nombre"] for v in versions] == [
        "ALCALDÍA DE EJEMPLO - PRUEBA",
        "ALCALDÍA DE EJEMPLO - RENOMBRADA",
    ]

    # The source goes back to the earlier content: stored as a third version.
    reverted = run_sync(session, entities.SPEC, [entity_row("9001")])
    assert reverted.rows_changed == 1
    assert count(session, SourceRecord) == 3


def test_a_failed_download_leaves_published_data_untouched(
    session: Session, registry: None
) -> None:
    run_sync(session, entities.SPEC, [entity_row("9001")])

    def broken_download() -> Iterator[Row]:
        yield entity_row("9001", nombre="CAMBIO QUE NO DEBE QUEDAR")
        yield entity_row("9002")
        raise ConnectionError("el portal dejó de responder")

    with pytest.raises(ConnectionError):
        run_sync(session, entities.SPEC, broken_download())

    session.expire_all()
    institution = session.scalars(select(Institution)).one()
    assert institution.name == "ALCALDÍA DE EJEMPLO - PRUEBA"
    assert count(session, SourceRecord) == 1
    runs = session.scalars(select(SyncRun).order_by(SyncRun.started_at)).all()
    assert [r.status for r in runs] == ["succeeded", "failed"]
    assert runs[1].error is not None
    assert "el portal dejó de responder" in runs[1].error


def test_sync_requires_a_registered_source(session: Session) -> None:
    with pytest.raises(LookupError):
        run_sync(session, entities.SPEC, [entity_row()])
