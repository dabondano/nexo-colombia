import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.ingestion.datasets import bills, entities
from app.ingestion.pipeline import run_sync
from app.search.indexing import number_variants
from app.search.models import SearchDocument
from app.search.reindex import reindex
from app.sources.registry import seed_registry
from tests.samples import bill_row, entity_row

API = "/api/v1/search"


@pytest.fixture
def loaded(session: Session) -> None:
    seed_registry(session)
    run_sync(
        session,
        entities.SPEC,
        [
            entity_row("9001"),  # ALCALDÍA DE EJEMPLO - PRUEBA, Boyacá
            entity_row(
                "9002",
                nombre="MINISTERIO DE EJEMPLO DE EDUCACION",
                orden="NACIONAL",
                naturaleza_juridica="MINISTERIO",
                departamento="BOGOTÁ D.C",
                municipio="BOGOTÁ D.C",
                ccb_nit_inst="899999001",
            ),
        ],
    )
    run_sync(
        session,
        bills.SPEC,
        [
            bill_row("proyecto-a"),  # "Educación rural (ejemplo)", 001/2026C, filed 2026-07-20
            bill_row(
                "proyecto-b",
                no_c_mara="045/2024C",
                proyecto="Pensiones de ejemplo",
                t_tulo="Por la cual se reforma el régimen de pensiones de ejemplo",
                objeto_del_proyecto="Objeto de ejemplo sobre educación superior.",
                autores="H.S. Senadora De Ejemplo",
                legislatura="2024-2025",
                fecha_c_mara="2024 Aug 01 12:00:00 AM",
            ),
        ],
    )


def titles(client: TestClient, **params: str) -> list[str]:
    response = client.get(API, params=params)
    assert response.status_code == 200, response.text
    return [item["title"] for item in response.json()["items"]]


def test_helpers() -> None:
    assert number_variants("217/2026C") == ["217/2026C", "217/2026", "217 2026"]
    assert number_variants("068/2012 S") == ["068/2012 S", "068/2012S", "068/2012", "068 2012"]
    assert number_variants(None) == []


def test_search_finds_records_of_every_type(
    client: TestClient, session: Session, loaded: None
) -> None:
    body = client.get(API, params={"q": "educación"}).json()
    assert body["query"] == "educación"
    assert body["total"] == 3
    assert body["counts"] == [
        {"record_type": "legislative_initiative", "count": 2},
        {"record_type": "institution", "count": 1},
    ]
    by_title = {item["title"]: item for item in body["items"]}
    assert set(by_title) == {
        "Educación rural (ejemplo)",
        "MINISTERIO DE EJEMPLO DE EDUCACION",
        "Pensiones de ejemplo",  # matches through its purpose: "educación superior"
    }
    bill = by_title["Educación rural (ejemplo)"]
    assert bill["record_type"] == "legislative_initiative"
    assert bill["record_date"] == "2026-07-20"
    assert "Cámara 001/2026C" in bill["summary"]
    entity = by_title["MINISTERIO DE EJEMPLO DE EDUCACION"]
    assert entity["record_type"] == "institution"
    assert entity["summary"] == "MINISTERIO · NACIONAL · BOGOTÁ D.C, BOGOTÁ D.C"
    # A match in the name ranks above a match in supporting text.
    assert body["items"][-1]["title"] == "Pensiones de ejemplo"


def test_search_ignores_accents_case_and_plurals(
    client: TestClient, session: Session, loaded: None
) -> None:
    assert "Educación rural (ejemplo)" in titles(client, q="EDUCACION rural")
    assert titles(client, q="alcaldia") == ["ALCALDÍA DE EJEMPLO - PRUEBA"]
    assert titles(client, q="alcaldías") == ["ALCALDÍA DE EJEMPLO - PRUEBA"]
    assert titles(client, q="pensión") == ["Pensiones de ejemplo"]
    assert titles(client, q="boyaca") == ["ALCALDÍA DE EJEMPLO - PRUEBA"]


def test_search_by_identifiers_and_authors(
    client: TestClient, session: Session, loaded: None
) -> None:
    assert titles(client, q="001/2026C") == ["Educación rural (ejemplo)"]
    assert titles(client, q="045/2024") == ["Pensiones de ejemplo"]
    assert titles(client, q="899999001") == ["MINISTERIO DE EJEMPLO DE EDUCACION"]
    assert titles(client, q="senadora") == ["Pensiones de ejemplo"]


def test_all_words_are_required_and_phrases_and_exclusions_work(
    client: TestClient, session: Session, loaded: None
) -> None:
    assert titles(client, q="educación pensiones") == ["Pensiones de ejemplo"]
    assert titles(client, q='"educación rural"') == ["Educación rural (ejemplo)"]
    assert titles(client, q="ejemplo -educación -alcaldía") == []
    assert titles(client, q="inexistente") == []


def test_type_and_date_filters(client: TestClient, session: Session, loaded: None) -> None:
    assert titles(client, q="educación", type="institution") == [
        "MINISTERIO DE EJEMPLO DE EDUCACION"
    ]
    only_bills = client.get(API, params={"q": "educación", "type": "legislative_initiative"})
    assert only_bills.json()["total"] == 2
    # Counts per type stay complete, so the other type can still be offered.
    assert len(only_bills.json()["counts"]) == 2

    # A date range keeps only dated records inside it.
    assert titles(client, q="ejemplo", date_from="2026-01-01") == ["Educación rural (ejemplo)"]
    assert titles(client, q="ejemplo", date_to="2024-12-31") == ["Pensiones de ejemplo"]
    assert titles(client, q="ejemplo", date_from="2025-01-01", date_to="2025-12-31") == []


def test_paging(client: TestClient, session: Session, loaded: None) -> None:
    first = client.get(API, params={"q": "ejemplo", "limit": 3}).json()
    rest = client.get(API, params={"q": "ejemplo", "limit": 3, "offset": 3}).json()
    assert first["total"] == rest["total"] == 4
    assert len(first["items"]) == 3
    assert len(rest["items"]) == 1
    seen = {item["record_id"] for item in first["items"] + rest["items"]}
    assert len(seen) == 4


def test_input_that_cannot_be_searched_returns_nothing(
    client: TestClient, session: Session, loaded: None
) -> None:
    for text in ("de la", "...", "   ", "%", "'; DROP TABLE core.source; --", "((( !!! &&& |||"):
        body = client.get(API, params={"q": text}).json()
        assert body["items"] == [], text
    assert client.get(API).status_code == 422
    assert client.get(API, params={"q": ""}).status_code == 422
    assert client.get(API, params={"q": "x" * 201}).status_code == 422
    assert client.get(API, params={"q": "ejemplo", "type": "persona"}).status_code == 422
    assert client.get(API, params={"q": "ejemplo", "date_from": "ayer"}).status_code == 422
    # The table named in the hostile input is still there.
    assert client.get("/api/v1/sources").status_code == 200


def test_index_follows_changes_and_can_be_rebuilt(
    client: TestClient, session: Session, loaded: None
) -> None:
    def documents() -> int:
        return session.scalar(select(func.count()).select_from(SearchDocument)) or 0

    assert documents() == 4

    # A changed record replaces its document instead of adding one.
    run_sync(session, entities.SPEC, [entity_row("9001", nombre="PERSONERÍA DE EJEMPLO")])
    assert documents() == 4
    assert titles(client, q="prueba", type="institution") == []
    assert titles(client, q="personeria") == ["PERSONERÍA DE EJEMPLO"]

    # The index holds no facts of its own: emptied, it is rebuilt from the records.
    session.execute(delete(SearchDocument))
    session.commit()
    assert titles(client, q="personeria") == []
    assert reindex(session) == 4
    assert titles(client, q="personeria") == ["PERSONERÍA DE EJEMPLO"]
    assert titles(client, q="001/2026C") == ["Educación rural (ejemplo)"]
