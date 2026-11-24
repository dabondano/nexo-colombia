"""SECOP II contracts: minimization, mapping, NIT links (A-016), window (A-015), API."""

from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ingestion.datasets import contracts, entities
from app.ingestion.pipeline import RowRejected, run_sync
from app.procurement.links import check_digit, link_contract_institutions, nit_key
from app.procurement.models import Contract
from app.procurement.retention import prune_contracts
from app.search.models import SearchDocument
from app.sources.models import SourceRecord
from app.sources.registry import seed_registry
from tests.samples import company_contract, contract_row, entity_row

API = "/api/v1"
TODAY = date(2026, 11, 24)


def load(session: Session, *rows: dict) -> None:  # type: ignore[type-arg]
    run_sync(session, contracts.SPEC, [contracts.minimize(row) for row in rows])


def test_natural_persons_are_not_named_or_identified() -> None:
    kept = contracts.minimize(contract_row())
    assert "proveedor_adjudicado" not in kept and "documento_proveedor" not in kept
    values = contracts.map_row(kept)
    assert values["supplier_kind"] == "persona_natural"
    assert values["supplier_name"] is None and values["supplier_nit"] is None


def test_companies_keep_name_and_nit() -> None:
    values = contracts.map_row(contracts.minimize(company_contract()))
    assert values["supplier_kind"] == "empresa"
    assert values["supplier_name"] == "EMPRESA DE EJEMPLO S.A.S."
    assert values["supplier_nit"] == "900000099"


def test_officials_and_bank_fields_are_never_stored(session: Session) -> None:
    seed_registry(session)
    load(session, contract_row())
    payload = session.scalars(select(SourceRecord.payload)).one()
    assert not {"n_mero_de_cuenta", "nombre_supervisor", "proveedor_adjudicado"} & set(payload)
    assert "nombre_supervisor" not in contracts.FIELDS


def test_mapping() -> None:
    values = contracts.map_row(contracts.minimize(contract_row()))
    assert values["value"] == Decimal(12000000) and values["paid"] == Decimal(3000000)
    assert values["signed_on"] == date(2026, 11, 2)
    assert values["process_url"].startswith("https://community.secop.gov.co/")
    assert values["data_quality_status"] == "acceptable"


def test_payments_above_invoices_are_marked_conflicting() -> None:
    values = contracts.map_row(contract_row(valor_pagado="5000000"))
    assert values["data_quality_status"] == "conflicting"


@pytest.mark.parametrize(
    ("field", "value"),
    [("valor_del_contrato", None), ("valor_del_contrato", "-1"), ("fecha_de_firma", "ayer")],
)
def test_invalid_rows_are_rejected(field: str, value: str | None) -> None:
    with pytest.raises(RowRejected):
        contracts.map_row({**contract_row(), field: value})


def test_window_is_a_rolling_number_of_days() -> None:
    assert contracts.window_start(TODAY) == date(2026, 8, 26)
    assert "fecha_de_firma >= '2026-08-26T00:00:00'" in contracts.where_clause(TODAY)
    assert "orden = 'Nacional'" in contracts.where_clause(TODAY)


def test_dian_check_digit() -> None:
    # Published NITs: SENA 899.999.034-1, DIAN 800.197.268-4.
    assert check_digit("899999034") == 1
    assert check_digit("800197268") == 4
    assert nit_key("8999990341") == "899999034"
    assert nit_key("8999990349") == "8999990349"  # wrong check digit: kept as is
    assert nit_key("899.999.034") == "899999034"


@pytest.fixture
def linked(session: Session) -> None:
    seed_registry(session)
    run_sync(
        session,
        entities.SPEC,
        [
            entity_row("9001", nombre="AGENCIA DE EJEMPLO", ccb_nit_inst="900000001"),
            # Two directory entries share one NIT: not linked.
            entity_row("9002", nombre="MINISTERIO DE EJEMPLO", ccb_nit_inst="900000002"),
            entity_row("9003", nombre="DEPENDENCIA DE EJEMPLO", ccb_nit_inst="900000002"),
        ],
    )
    load(
        session,
        contract_row("CO1.PCCNTR.1"),
        # Same entity, NIT published with its check digit.
        contract_row("CO1.PCCNTR.2", nit_entidad=f"900000001{check_digit('900000001')}"),
        company_contract("CO1.PCCNTR.3", nit_entidad="900000002"),
        # Signed before the window: removed by pruning.
        contract_row("CO1.PCCNTR.4", fecha_de_firma="2026-07-15T09:00:00.000"),
    )


def test_contracts_link_to_one_entity_by_nit(session: Session, linked: None) -> None:
    result = link_contract_institutions(session)
    assert (result.linked_nits, result.ambiguous_nits) == (2, 1)
    by_key = dict(session.execute(select(Contract.source_key, Contract.institution_id)).all())
    assert by_key["CO1.PCCNTR.1"] is not None
    assert by_key["CO1.PCCNTR.2"] == by_key["CO1.PCCNTR.1"]
    assert by_key["CO1.PCCNTR.3"] is None


def test_pruning_removes_old_contracts_with_their_raw_copies(
    session: Session, linked: None
) -> None:
    result = prune_contracts(session, today=TODAY)
    assert (result.contracts, result.raw_records) == (1, 1)
    keys = set(session.scalars(select(Contract.source_key)))
    assert keys == {"CO1.PCCNTR.1", "CO1.PCCNTR.2", "CO1.PCCNTR.3"}
    raw = set(session.scalars(select(SourceRecord.external_id)))
    assert "CO1.PCCNTR.4" not in raw and "CO1.PCCNTR.1" in raw
    # Other sources' raw records are untouched.
    assert session.scalar(select(func.count()).select_from(SourceRecord)) == 3 + 3
    documents = session.scalar(
        select(func.count())
        .select_from(SearchDocument)
        .where(SearchDocument.record_type == "contract")
    )
    assert documents == 3


def test_list_detail_and_institution_count(
    client: TestClient, session: Session, linked: None
) -> None:
    link_contract_institutions(session)
    page = client.get(f"{API}/contracts", params={"q": "gestion documental"}).json()
    assert page["total"] == 3  # contract_row's purpose, three times (one older)
    assert [item["signed_on"] for item in page["items"]][0] == "2026-11-02"
    assert "últimos 90 días" in page["window_note"]
    detail = client.get(f"{API}/contracts/{page['items'][0]['id']}").json()
    assert detail["supplier_name"] is None and detail["supplier_label"] == "Persona natural"
    assert "personas naturales" in detail["privacy_note"]
    assert detail["institution"]["name"] == "AGENCIA DE EJEMPLO"
    institution = client.get(f"{API}/institutions/{detail['institution']['institution_id']}").json()
    assert institution["contract_count"] == 3
    filtered = client.get(
        f"{API}/contracts", params={"institution": detail["institution"]["institution_id"]}
    ).json()
    assert filtered["total"] == 3
    company = client.get(f"{API}/contracts", params={"contract_type": "Compraventa"}).json()
    assert company["items"][0]["supplier_name"] == "EMPRESA DE EJEMPLO S.A.S."
    filters = client.get(f"{API}/contracts/filters").json()
    assert {option["value"] for option in filters["modality"]} == {
        "Contratación directa",
        "Mínima cuantía",
    }
    missing = "00000000-0000-0000-0000-000000000000"
    assert client.head(f"{API}/contracts/{missing}").status_code == 404
    assert client.get(f"{API}/contracts/{missing}").status_code == 404


def test_contracts_are_searchable(client: TestClient, session: Session, linked: None) -> None:
    body = client.get(f"{API}/search", params={"q": "elementos de aseo", "type": "contract"})
    hits = body.json()["items"]
    assert len(hits) == 1
    assert "EMPRESA DE EJEMPLO" in hits[0]["summary"]
    assert hits[0]["record_key"] == hits[0]["record_id"]
