"""Entity links reviewed by the data team (A-017)."""

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import Role
from app.budget.links import link_budget_institutions
from app.catalog.mappings import contract_key
from app.catalog.models import Institution
from app.core.audit import AuditEvent
from app.ingestion.datasets import budget, contracts, entities
from app.ingestion.pipeline import run_sync
from app.procurement.links import link_contract_institutions
from app.procurement.models import Contract
from app.sources.registry import seed_registry
from tests.samples import budget_row, company_contract, contract_row, entity_row
from tests.test_auth import login, make_user

API = "/api/v1/admin/entity-mappings"
NOTE = "Mismo código de entidad en el PGN y en el decreto de liquidación"


def load(session: Session) -> dict[str, Institution]:
    seed_registry(session)
    run_sync(
        session,
        entities.SPEC,
        [
            entity_row("9001", nombre="MINISTERIO DE EJEMPLO", ccb_nit_inst="900000002"),
            entity_row("9002", nombre="DEPENDENCIA DE EJEMPLO", ccb_nit_inst="900000002"),
        ],
    )
    run_sync(
        session,
        budget.SPEC,
        [budget_row("97-01-00", nombre_entidad="MINISTERIO DE EJEMPLO - GESTIÓN GENERAL")],
    )
    run_sync(
        session,
        contracts.SPEC,
        [
            contracts.minimize(
                contract_row(
                    "CO1.PCCNTR.1",
                    nombre_entidad="DEPENDENCIA DE EJEMPLO*",
                    nit_entidad="900000002",
                )
            ),  # noqa: E501
            contracts.minimize(
                company_contract(
                    "CO1.PCCNTR.2", nombre_entidad="OTRA OFICINA", nit_entidad="900000002"
                )
            ),  # noqa: E501
        ],
    )
    link_budget_institutions(session)
    link_contract_institutions(session)
    make_user(session, "datos@ejemplo.gov.co", Role.DATA_STEWARD)
    make_user(session, "revision@ejemplo.gov.co", Role.LEGAL_REVIEWER)
    return {i.name: i for i in session.scalars(select(Institution))}


def test_only_stewards_and_admins(client: TestClient, session: Session) -> None:
    load(session)
    params = {"kind": "budget_entity"}
    assert client.get(f"{API}/candidates", params=params).status_code == 401
    reviewer = login(client, "revision@ejemplo.gov.co")
    assert client.get(f"{API}/candidates", params=params, headers=reviewer).status_code == 403


def test_budget_entity_linked_by_review(client: TestClient, session: Session) -> None:
    institutions = load(session)
    steward = login(client, "datos@ejemplo.gov.co")
    pending = client.get(
        f"{API}/candidates", params={"kind": "budget_entity"}, headers=steward
    ).json()
    assert [item["source_value"] for item in pending["items"]] == ["97-01-00"]
    assert "Ninguna entidad" in pending["items"][0]["reason"]
    target = str(institutions["MINISTERIO DE EJEMPLO"].id)
    body = {"kind": "budget_entity", "source_value": "97-01-00", "institution_id": target}
    short = client.post(API, json={**body, "note": "corto"}, headers=steward)
    assert short.status_code == 422
    created = client.post(API, json={**body, "note": NOTE}, headers=steward)
    assert created.status_code == 201, created.text
    assert created.json()["source_name"] == "MINISTERIO DE EJEMPLO - GESTIÓN GENERAL"
    assert client.post(API, json={**body, "note": NOTE}, headers=steward).status_code == 409

    entity = client.get("/api/v1/budget/entities/97-01-00").json()
    assert entity["linked_institution"]["institution_id"] == target
    assert "revisado por el equipo de datos" in entity["linked_institution_rule"]
    assert NOTE in entity["linked_institution_rule"]
    institution = client.get(f"/api/v1/institutions/{target}").json()
    assert institution["budget_entity"]["entity_code"] == "97-01-00"
    assert NOTE in institution["budget_entity_rule"]
    # The weekly relink keeps reviewed links.
    link_budget_institutions(session)
    assert client.get("/api/v1/budget/entities/97-01-00").json()["linked_institution"]
    empty = client.get(f"{API}/candidates", params={"kind": "budget_entity"}, headers=steward)
    assert empty.json()["total"] == 0

    mapping_id = created.json()["id"]
    assert client.delete(f"{API}/{mapping_id}", headers=steward).status_code == 204
    assert client.get("/api/v1/budget/entities/97-01-00").json()["linked_institution"] is None
    actions = set(session.scalars(select(AuditEvent.action)))
    assert {"entity_mapping_created", "entity_mapping_deleted"} <= actions


def test_contract_entity_with_shared_nit_linked_by_review(
    client: TestClient, session: Session
) -> None:
    institutions = load(session)
    steward = login(client, "datos@ejemplo.gov.co")
    pending = client.get(
        f"{API}/candidates", params={"kind": "contract_entity"}, headers=steward
    ).json()
    assert pending["total"] == 2
    assert all("El NIT es de 2 entidades" in item["reason"] for item in pending["items"])
    key = contract_key("900000002", "DEPENDENCIA DE EJEMPLO*")
    assert key in {item["source_value"] for item in pending["items"]}
    target = institutions["DEPENDENCIA DE EJEMPLO"].id
    created = client.post(
        API,
        json={
            "kind": "contract_entity",
            "source_value": key,
            "institution_id": str(target),
            "note": "Nombre de la dependencia en SECOP, verificado en su sitio web",
        },
        headers=steward,
    )
    assert created.status_code == 201, created.text
    links = dict(
        session.execute(select(Contract.source_key, Contract.institution_link_method)).all()
    )
    # Only the reviewed name is linked; the other office with the same NIT is not.
    assert links == {"CO1.PCCNTR.1": "revision", "CO1.PCCNTR.2": None}
    contract_id = session.scalar(select(Contract.id).where(Contract.source_key == "CO1.PCCNTR.1"))
    detail = client.get(f"/api/v1/contracts/{contract_id}").json()
    assert detail["institution"]["institution_id"] == str(target)
    assert "verificado en su sitio web" in detail["institution_rule"]
    assert client.get(f"/api/v1/institutions/{target}").json()["contract_count"] == 1


def test_unknown_source_or_institution(client: TestClient, session: Session) -> None:
    institutions = load(session)
    steward = login(client, "datos@ejemplo.gov.co")
    body = {
        "kind": "budget_entity",
        "source_value": "00-00-00",
        "institution_id": str(institutions["MINISTERIO DE EJEMPLO"].id),
        "note": NOTE,
    }
    assert client.post(API, json=body, headers=steward).status_code == 404
    missing = {
        **body,
        "source_value": "97-01-00",
        "institution_id": "00000000-0000-0000-0000-000000000000",
    }  # noqa: E501
    assert client.post(API, json=missing, headers=steward).status_code == 404
