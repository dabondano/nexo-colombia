from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.ingestion.datasets import budget
from app.ingestion.pipeline import RowRejected, run_sync
from app.sources.registry import seed_registry
from tests.samples import budget_row

API = "/api/v1"


def test_mapping_keeps_published_values_and_cleans_spaces() -> None:
    values = budget.map_row(budget_row())
    assert values["budget_resource"] == "RECURSOS CORRIENTES"  # non-breaking space normalized
    assert values["appropriation"] == Decimal(1000000)
    assert values["payments"] == Decimal(400000)
    assert values["data_quality_status"] == "acceptable"
    assert "obligations_ignored" not in budget.ALLOWED_FIELDS


def test_out_of_order_stages_are_marked_conflicting() -> None:
    values = budget.map_row(budget_row(pagos="900000"))
    assert values["data_quality_status"] == "conflicting"


@pytest.mark.parametrize("value", ["-5", "no aplica", "abc", "NaN"])
def test_invalid_amounts_are_rejected(value: str) -> None:
    with pytest.raises(RowRejected):
        budget.map_row(budget_row(compromisos=value))


@pytest.fixture
def loaded(session: Session) -> None:
    seed_registry(session)
    run_sync(
        session,
        budget.SPEC,
        [
            budget_row(),
            budget_row(
                recurso_presupuestal="DONACIONES",
                situacion_de_fondos="SSF",
                apropiaci_n_vigente="0",
                compromisos="0",
                obligaciones="0",
                pagos="0",
            ),
            budget_row(
                "98-01-00",
                nombre_entidad="MINISTERIO DE EJEMPLO",
                codigo_del_sector="98",
                nombre_del_sector="OTRO SECTOR",
                apropiaci_n_vigente="3000000",
                compromisos="3000000",
                obligaciones="1500000",
                pagos="1500000",
            ),
        ],
    )


def test_summary(client: TestClient, loaded: None) -> None:
    body = client.get(f"{API}/budget/summary").json()
    assert body["entity_count"] == 2 and body["row_count"] == 3
    assert Decimal(body["amounts"]["appropriation"]) == 4000000
    assert Decimal(body["rates"]["commitments"]) == Decimal("0.95")
    assert body["source_updated_at"].startswith("2026-11-07")
    assert "no indica la vigencia" in body["year_note"]
    assert [s["sector_name"] for s in body["sectors"]] == ["OTRO SECTOR", "SECTOR DE EJEMPLO"]


def test_entities_are_alphabetical_with_rates(client: TestClient, loaded: None) -> None:
    page = client.get(f"{API}/budget/entities").json()
    assert [item["entity_name"] for item in page["items"]] == [
        "AGENCIA DE EJEMPLO",
        "MINISTERIO DE EJEMPLO",
    ]
    agency = page["items"][0]
    assert Decimal(agency["amounts"]["appropriation"]) == 1000000
    assert Decimal(agency["rates"]["payments"]) == Decimal("0.4")
    only = client.get(f"{API}/budget/entities", params={"sector": "OTRO SECTOR"}).json()
    assert only["total"] == 1
    assert client.get(f"{API}/budget/entities", params={"q": "ministerio"}).json()["total"] == 1


def test_entity_detail(client: TestClient, loaded: None) -> None:
    body = client.get(f"{API}/budget/entities/99-01-00").json()
    assert len(body["lines"]) == 2
    donations = next(line for line in body["lines"] if line["budget_resource"] == "DONACIONES")
    assert donations["rates"] == {"commitments": None, "obligations": None, "payments": None}
    assert body["epistemic_label"] == "hecho_documentado"
    assert body["provenance"]["source_name"].startswith("Ejecución Presupuestal")
    assert "÷ apropiación vigente" in body["rate_formula"]
    assert client.head(f"{API}/budget/entities/99-01-00").status_code == 200
    assert client.head(f"{API}/budget/entities/00-00-00").status_code == 404
    assert client.get(f"{API}/budget/entities/00-00-00").status_code == 404
    assert client.get(f"{API}/budget/entities/x%20y").status_code == 422
