"""Data-quality monitoring for the staff panel."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.sources.models import Source, SyncRun
from app.sources.quality import data_quality, database_size, report
from app.sources.registry import seed_registry

NOW = datetime(2026, 11, 24, 12, tzinfo=UTC)


def _run(
    source: Source,
    days_ago: int,
    seen: int,
    rejected: int = 0,
    status: str = "succeeded",
    error: str | None = None,
) -> SyncRun:  # noqa: E501
    started = NOW - timedelta(days=days_ago)
    return SyncRun(
        source_id=source.id,
        mode="full",
        status=status,
        started_at=started,
        finished_at=started + timedelta(minutes=1),
        rows_seen=seen,
        rows_rejected=rejected,
        error=error,
    )


def _source(session: Session) -> Source:
    seed_registry(session)
    return session.query(Source).filter(Source.external_ref == "datos.gov.co:jbjy-vk9h").one()


def test_steady_source_has_no_checks(session: Session) -> None:
    source = _source(session)
    # A constant share of rejects (like the Cámara representatives) is not flagged.
    session.add_all([_run(source, 8, 1000, 500), _run(source, 1, 1000, 500)])
    session.commit()
    [item] = data_quality(session, NOW)
    assert item.checks == []
    assert item.last_success_at is not None


def test_fewer_rows_more_rejects_and_staleness_are_flagged(session: Session) -> None:
    source = _source(session)
    session.add_all([_run(source, 17, 1000, 0), _run(source, 10, 800, 50)])
    session.commit()
    [item] = data_quality(session, NOW)
    assert any("20 % menos" in check or "20% menos" in check for check in item.checks)
    assert any("rechazadas subieron" in check for check in item.checks)
    assert any("hace 9 días" in check for check in item.checks)


def test_failed_last_run_is_flagged(session: Session) -> None:
    source = _source(session)
    session.add_all([_run(source, 2, 1000), _run(source, 0, 0, status="failed", error="HTTP 503")])
    session.commit()
    [item] = data_quality(session, NOW)
    assert item.checks == ["La última sincronización falló: HTTP 503."]


def test_endpoint_is_for_data_stewards(client, session: Session) -> None:  # type: ignore[no-untyped-def]
    assert client.get("/api/v1/admin/data-quality").status_code == 401


def test_database_size_warns_near_the_plan_limit(
    session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    size = database_size(session)
    assert size.used_mb > 0 and size.check is None  # test database is small
    monkeypatch.setattr(get_settings(), "database_size_limit_mb", 1)
    small = database_size(session)
    assert small.check is not None and "NEXO_SECOP_WINDOW_DAYS" in small.check


def test_report_is_empty_without_checks(session: Session) -> None:
    source = _source(session)
    session.add(_run(source, 1, 1000))
    session.commit()
    assert report(session, NOW) is None


def test_report_lists_each_source_with_checks(session: Session) -> None:
    source = _source(session)
    session.add(_run(source, 12, 1000))
    session.commit()
    text = report(session, NOW)
    assert text is not None
    assert "### SECOP II - Contratos Electrónicos" in text and "hace 11 días" in text
