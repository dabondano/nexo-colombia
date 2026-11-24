import hashlib

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import Role
from app.core.audit import AuditEvent
from app.ingestion.datasets import constitution
from app.ingestion.pipeline import run_sync
from app.sources.registry import seed_registry
from tests.constitution_page import page
from tests.test_auth import login, make_user

API = "/api/v1"
LESSON_HASH = hashlib.sha256(b"contenido de la leccion").hexdigest()


def load_constitution(session: Session, **changes: str) -> None:
    seed_registry(session)
    run_sync(session, constitution.SPEC, constitution.rows_from_html(page(**changes)))


def test_only_reviewers_and_admins_record_reviews(client: TestClient, session: Session) -> None:
    load_constitution(session)
    make_user(session, "revision@ejemplo.gov.co", Role.LEGAL_REVIEWER)
    make_user(session, "datos@ejemplo.gov.co", Role.DATA_STEWARD)
    make_user(session, "admin@ejemplo.gov.co", Role.ADMIN)
    body = {
        "content_type": "lesson",
        "content_key": "estructura-del-estado",
        "fingerprint": LESSON_HASH,
        "decision": "approved",
    }
    assert client.post(f"{API}/reviews", json=body).status_code == 401
    steward = login(client, "datos@ejemplo.gov.co")
    assert client.post(f"{API}/reviews", json=body, headers=steward).status_code == 403
    for email in ("revision@ejemplo.gov.co", "admin@ejemplo.gov.co"):
        headers = login(client, email)
        assert client.post(f"{API}/reviews", json=body, headers=headers).status_code == 201


def test_lesson_reviews_need_a_fingerprint_and_reasons(
    client: TestClient, session: Session
) -> None:
    make_user(session, "revision@ejemplo.gov.co", Role.LEGAL_REVIEWER)
    headers = login(client, "revision@ejemplo.gov.co")
    base = {"content_type": "lesson", "content_key": "estructura-del-estado"}
    missing = client.post(f"{API}/reviews", headers=headers, json={**base, "decision": "approved"})
    assert missing.status_code == 422
    bad_key = {**base, "content_key": "../otra", "fingerprint": LESSON_HASH, "decision": "approved"}
    assert client.post(f"{API}/reviews", headers=headers, json=bad_key).status_code == 422
    no_reason = {**base, "fingerprint": LESSON_HASH, "decision": "changes_requested"}
    assert client.post(f"{API}/reviews", headers=headers, json=no_reason).status_code == 400
    with_reason = {**no_reason, "notes": "El paso 2 confunde ramas y órganos."}
    assert client.post(f"{API}/reviews", headers=headers, json=with_reason).status_code == 201


def test_history_is_staff_only_and_public_view_hides_notes(
    client: TestClient, session: Session
) -> None:
    load_constitution(session)
    make_user(session, "revision@ejemplo.gov.co", Role.LEGAL_REVIEWER)
    headers = login(client, "revision@ejemplo.gov.co")
    article = {"content_type": "constitution_provision", "content_key": "articulo-11"}
    first = client.post(
        f"{API}/reviews",
        headers=headers,
        json={**article, "decision": "changes_requested", "notes": "Nota interna de ejemplo."},
    )
    second = client.post(
        f"{API}/reviews",
        headers=headers,
        # A client-supplied fingerprint is ignored for provisions.
        json={**article, "fingerprint": "inventada", "decision": "approved"},
    )
    assert first.status_code == second.status_code == 201
    assert second.json()["fingerprint"] == first.json()["fingerprint"] != "inventada"

    params = {"content_type": "constitution_provision", "content_key": "articulo-11"}
    assert client.get(f"{API}/reviews", params=params).status_code == 401
    history = client.get(f"{API}/reviews", params=params, headers=headers).json()
    assert [item["decision"] for item in history] == ["approved", "changes_requested"]
    assert history[1]["notes"] == "Nota interna de ejemplo."

    public = client.get(f"{API}/reviews/latest", params={"content_type": "constitution_provision"})
    assert public.status_code == 200
    (latest,) = public.json()
    assert latest["decision"] == "approved" and latest["content_key"] == "articulo-11"
    assert (
        "notes" not in latest and "reviewer_email" not in latest and "reviewer_name" not in latest
    )

    missing = {**article, "content_key": "articulo-999", "decision": "approved"}
    assert client.post(f"{API}/reviews", headers=headers, json=missing).status_code == 404
    assert session.scalars(select(AuditEvent).where(AuditEvent.action == "review_recorded")).all()


def test_a_new_wording_does_not_carry_the_review(client: TestClient, session: Session) -> None:
    load_constitution(session)
    make_user(session, "revision@ejemplo.gov.co", Role.LEGAL_REVIEWER)
    headers = login(client, "revision@ejemplo.gov.co")
    reviewed = client.post(
        f"{API}/reviews",
        headers=headers,
        json={
            "content_type": "constitution_provision",
            "content_key": "articulo-1",
            "decision": "approved",
        },
    ).json()["fingerprint"]
    load_constitution(session, article_1="Colombia es un Estado social de derecho, texto nuevo.")
    article = client.get(
        f"{API}/instruments/constitucion-politica-1991/provisions/articulo-1"
    ).json()
    assert article["version_id"] != reviewed
