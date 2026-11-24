from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.auth.models import Role, UserAccount
from app.auth.security import hash_password, password_problem
from app.auth.service import IDLE_TIMEOUT, MAX_FAILED_ATTEMPTS, resolve, sign_in
from app.core.audit import AuditEvent

API = "/api/v1"
PASSWORD = "una-clave-de-prueba-larga"  # noqa: S105 (test fixture)


def make_user(
    session: Session,
    email: str = "admin@ejemplo.gov.co",
    role: Role = Role.ADMIN,
    must_change: bool = False,
) -> UserAccount:
    user = UserAccount(
        email=email,
        display_name="Persona de ejemplo",
        role=role.value,
        password_hash=hash_password(PASSWORD),
        must_change_password=must_change,
    )
    session.add(user)
    session.commit()
    return user


def login(client: TestClient, email: str, password: str = PASSWORD) -> dict[str, str]:
    response = client.post(f"{API}/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['token']}"}


def test_sign_in_and_out(client: TestClient, session: Session) -> None:
    make_user(session)
    response = client.post(
        f"{API}/auth/login", json={"email": " Admin@Ejemplo.gov.co ", "password": PASSWORD}
    )
    assert response.status_code == 200
    body = response.json()
    assert "password_hash" not in body["user"]
    headers = {"Authorization": f"Bearer {body['token']}"}
    assert client.get(f"{API}/auth/me", headers=headers).json()["role"] == "admin"
    assert client.post(f"{API}/auth/logout", headers=headers).status_code == 204
    assert client.get(f"{API}/auth/me", headers=headers).status_code == 401
    actions = list(session.scalars(select(AuditEvent.action).order_by(AuditEvent.occurred_at)))
    assert actions == ["sign_in", "sign_out"]


def test_failed_sign_ins_look_the_same_and_lock_the_account(
    client: TestClient, session: Session
) -> None:
    make_user(session)
    unknown = client.post(
        f"{API}/auth/login", json={"email": "nadie@ejemplo.gov.co", "password": "x"}
    )
    wrong = client.post(
        f"{API}/auth/login", json={"email": "admin@ejemplo.gov.co", "password": "otra-clave-mala"}
    )
    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json() == wrong.json()

    for _ in range(MAX_FAILED_ATTEMPTS - 1):
        client.post(f"{API}/auth/login", json={"email": "admin@ejemplo.gov.co", "password": "mala"})
    locked = client.post(
        f"{API}/auth/login", json={"email": "admin@ejemplo.gov.co", "password": PASSWORD}
    )
    assert locked.status_code == 401
    assert locked.json() == wrong.json()
    reasons = [
        event.details["reason"]
        for event in session.scalars(
            select(AuditEvent).where(AuditEvent.action == "sign_in_failed")
        )
    ]
    assert "wrong_password_locked" in reasons and reasons[-1] == "locked"
    # After the lockout, the right password works again.
    later = datetime.now(UTC) + timedelta(minutes=16)
    assert sign_in(session, "admin@ejemplo.gov.co", PASSWORD, now=later) is not None


def test_sessions_expire_when_idle(session: Session) -> None:
    make_user(session)
    start = datetime.now(UTC)
    result = sign_in(session, "admin@ejemplo.gov.co", PASSWORD, now=start)
    assert result is not None
    assert resolve(session, result.token, now=start + timedelta(minutes=30)) is not None
    assert resolve(session, result.token, now=start + timedelta(minutes=30) + IDLE_TIMEOUT) is None
    assert resolve(session, "token-inventado") is None


def test_roles(client: TestClient, session: Session) -> None:
    make_user(session)
    make_user(session, "datos@ejemplo.gov.co", Role.DATA_STEWARD)
    make_user(session, "revision@ejemplo.gov.co", Role.LEGAL_REVIEWER)
    admin = login(client, "admin@ejemplo.gov.co")
    steward = login(client, "datos@ejemplo.gov.co")
    reviewer = login(client, "revision@ejemplo.gov.co")

    expected = {
        "/admin/users": {"admin": 200, "steward": 403, "reviewer": 403, "none": 401},
        "/admin/audit": {"admin": 200, "steward": 403, "reviewer": 403, "none": 401},
        "/admin/sync-runs": {"admin": 200, "steward": 200, "reviewer": 403, "none": 401},
    }
    for path, by_role in expected.items():
        for name, headers in {
            "admin": admin,
            "steward": steward,
            "reviewer": reviewer,
            "none": {},
        }.items():
            assert client.get(f"{API}{path}", headers=headers).status_code == by_role[name], (
                path,
                name,
            )
    bogus = {"Authorization": "Bearer no-es-un-token"}
    assert client.get(f"{API}/admin/users", headers=bogus).status_code == 401


def test_issued_password_must_be_changed_first(client: TestClient, session: Session) -> None:
    make_user(session)
    admin = login(client, "admin@ejemplo.gov.co")
    created = client.post(
        f"{API}/admin/users",
        headers=admin,
        json={"email": "Nueva@Ejemplo.gov.co", "display_name": "Nueva", "role": "data_steward"},
    )
    assert created.status_code == 201
    temporary = created.json()["temporary_password"]
    assert created.json()["user"]["email"] == "nueva@ejemplo.gov.co"
    duplicate = client.post(
        f"{API}/admin/users",
        headers=admin,
        json={"email": "nueva@ejemplo.gov.co", "display_name": "Otra", "role": "admin"},
    )
    assert duplicate.status_code == 409

    new = login(client, "nueva@ejemplo.gov.co", temporary)
    assert client.get(f"{API}/auth/me", headers=new).json()["must_change_password"] is True
    assert client.get(f"{API}/admin/sync-runs", headers=new).status_code == 403

    weak = client.post(
        f"{API}/auth/password",
        headers=new,
        json={"current_password": temporary, "new_password": "corta"},
    )
    assert weak.status_code == 400
    changed = client.post(
        f"{API}/auth/password",
        headers=new,
        json={"current_password": temporary, "new_password": "otra-clave-bien-larga"},
    )
    assert changed.status_code == 204
    assert client.get(f"{API}/admin/sync-runs", headers=new).status_code == 200


def test_role_change_ends_sessions_and_the_last_admin_stays(
    client: TestClient, session: Session
) -> None:
    admin_user = make_user(session)
    steward_user = make_user(session, "datos@ejemplo.gov.co", Role.DATA_STEWARD)
    admin = login(client, "admin@ejemplo.gov.co")
    steward = login(client, "datos@ejemplo.gov.co")

    response = client.patch(
        f"{API}/admin/users/{steward_user.id}", headers=admin, json={"role": "legal_reviewer"}
    )
    assert response.status_code == 200 and response.json()["role"] == "legal_reviewer"
    assert client.get(f"{API}/auth/me", headers=steward).status_code == 401

    last = client.patch(
        f"{API}/admin/users/{admin_user.id}", headers=admin, json={"is_active": False}
    )
    assert last.status_code == 409
    assert client.get(f"{API}/auth/me", headers=admin).status_code == 200

    reset = client.post(f"{API}/admin/users/{steward_user.id}/reset-password", headers=admin)
    assert reset.status_code == 200
    audit = client.get(f"{API}/admin/audit", headers=admin).json()
    actions = {item["action"] for item in audit["items"]}
    assert {"user_updated", "password_reset", "sign_in"} <= actions
    assert any(item["actor_email"] == "admin@ejemplo.gov.co" for item in audit["items"])


def test_audit_log_is_append_only(session: Session) -> None:
    make_user(session)
    sign_in(session, "admin@ejemplo.gov.co", PASSWORD)
    for statement in (
        "UPDATE core.audit_event SET action = 'otro'",
        "DELETE FROM core.audit_event",
    ):
        with pytest.raises(DBAPIError, match="append-only"):
            session.execute(text(statement))
        session.rollback()


def test_password_rules() -> None:
    assert password_problem("corta", "a@b.co") is not None
    assert password_problem("persona@ejemplo.gov.co", "persona@ejemplo.gov.co") is not None
    assert password_problem("aaaaaaaaaaaaaaaa", "a@b.co") is not None
    assert password_problem("x" * 129, "a@b.co") is not None
    assert password_problem("una frase larga y propia", "a@b.co") is None
