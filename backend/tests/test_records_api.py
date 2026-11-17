import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.ingestion.datasets import bills, entities
from app.ingestion.pipeline import run_sync
from app.sources.registry import seed_registry
from tests.samples import bill_row, entity_row

API = "/api/v1"


@pytest.fixture
def loaded(session: Session) -> None:
    seed_registry(session)
    run_sync(
        session,
        entities.SPEC,
        [
            entity_row("9001"),
            entity_row(
                "9002",
                nombre="MINISTERIO DE EJEMPLO Y PROTECCIÓN SOCIAL",
                orden="NACIONAL",
                sector="SALUD Y PROTECCIÓN SOCIAL",
                departamento="BOGOTÁ D.C",
                ccb_nit_inst="No disponible en la fuente",
            ),
            entity_row("9003", nombre="CONCEJO MUNICIPAL DE EJEMPLO"),
        ],
    )
    run_sync(
        session,
        bills.SPEC,
        [
            bill_row("proyecto-a"),
            bill_row(
                "proyecto-b",
                t_tulo="Por la cual se reforma el régimen de ejemplo de salud pública",
                autores="H.S. Senadora De Ejemplo",
                tipo_de_ley="Ley Estatutaria",
                estado_de_ley="Archivado",
                legislatura="2024-2025",
                fecha_c_mara="2024 Aug 01 12:00:00 AM",
            ),
        ],
    )


def test_empty_database_returns_empty_pages(client: TestClient, session: Session) -> None:
    for path in ("/institutions", "/initiatives"):
        body = client.get(f"{API}{path}").json()
        assert body == {"total": 0, "limit": 25, "offset": 0, "items": []}


def test_institutions_are_listed_alphabetically_with_paging(
    client: TestClient, session: Session, loaded: None
) -> None:
    body = client.get(f"{API}/institutions", params={"limit": 2}).json()
    assert body["total"] == 3
    assert [i["name"] for i in body["items"]] == [
        "ALCALDÍA DE EJEMPLO - PRUEBA",
        "CONCEJO MUNICIPAL DE EJEMPLO",
    ]
    rest = client.get(f"{API}/institutions", params={"limit": 2, "offset": 2}).json()
    assert [i["name"] for i in rest["items"]] == ["MINISTERIO DE EJEMPLO Y PROTECCIÓN SOCIAL"]


def test_institution_search_ignores_accents_case_and_word_order(
    client: TestClient, session: Session, loaded: None
) -> None:
    body = client.get(f"{API}/institutions", params={"q": "proteccion MINISTERIO"}).json()
    assert [i["official_code"] for i in body["items"]] == ["9002"]
    assert client.get(f"{API}/institutions", params={"q": "inexistente"}).json()["total"] == 0
    # Characters with a special meaning in SQL patterns are treated as plain text.
    assert client.get(f"{API}/institutions", params={"q": "%"}).json()["total"] == 0


def test_institution_filters(client: TestClient, session: Session, loaded: None) -> None:
    national = client.get(f"{API}/institutions", params={"order": "NACIONAL"}).json()
    assert [i["official_code"] for i in national["items"]] == ["9002"]
    boyaca = client.get(f"{API}/institutions", params={"department": "BOYACÁ"}).json()
    assert boyaca["total"] == 2

    options = client.get(f"{API}/institutions/filters").json()
    assert options["order"] == [
        {"value": "NACIONAL", "count": 1},
        {"value": "TERRITORIAL", "count": 2},
    ]
    # "NO APLICA" in the source is a missing value, so it is not offered as a sector.
    assert options["sector"] == [{"value": "SALUD Y PROTECCIÓN SOCIAL", "count": 1}]


def test_institution_detail_carries_label_quality_and_provenance(
    client: TestClient, session: Session, loaded: None
) -> None:
    listed = client.get(f"{API}/institutions", params={"q": "ministerio"}).json()["items"][0]
    body = client.get(f"{API}/institutions/{listed['id']}").json()

    assert body["name"] == "MINISTERIO DE EJEMPLO Y PROTECCIÓN SOCIAL"
    assert body["epistemic_label"] == "hecho_documentado"
    assert body["data_quality_status"] == "incomplete"  # no NIT in this sample
    assert body["jurisdiction_code"] == "CO"
    provenance = body["provenance"]
    assert provenance["source_name"] == "Universo de entidades"
    assert provenance["source_institution"] == "Departamento Administrativo de la Función Pública"
    assert provenance["source_url"].startswith("https://www.datos.gov.co/")
    assert provenance["licence"] == "CC BY-SA 4.0"
    assert provenance["acquired_at"] is not None
    assert provenance["last_verified_at"] is not None
    # Contact and personal fields are not part of the public record.
    assert not {"email", "telefono", "direccion", "representante"} & set(body)


def test_initiatives_are_listed_newest_legislature_first(
    client: TestClient, session: Session, loaded: None
) -> None:
    body = client.get(f"{API}/initiatives").json()
    assert body["total"] == 2
    assert [i["legislature"] for i in body["items"]] == ["2026-2027", "2024-2025"]


def test_initiative_search_and_filters(client: TestClient, session: Session, loaded: None) -> None:
    def codes(**params: str) -> list[str | None]:
        items = client.get(f"{API}/initiatives", params=params).json()["items"]
        return [i["legislature"] for i in items]

    assert codes(q="educacion rural") == ["2026-2027"]
    assert codes(q="SALUD PÚBLICA") == ["2024-2025"]
    assert codes(author="senadora") == ["2024-2025"]
    assert codes(law_type="Ley Estatutaria") == ["2024-2025"]
    assert codes(status="Trámite en Comisión") == ["2026-2027"]
    assert codes(legislature="2026-2027", status="Archivado") == []

    options = client.get(f"{API}/initiatives/filters").json()
    assert [o["value"] for o in options["legislature"]] == ["2026-2027", "2024-2025"]
    assert {"value": "Archivado", "count": 1} in options["status"]


def test_initiative_detail_carries_label_and_provenance(
    client: TestClient, session: Session, loaded: None
) -> None:
    listed = client.get(f"{API}/initiatives", params={"q": "educacion"}).json()["items"][0]
    body = client.get(f"{API}/initiatives/{listed['id']}").json()

    assert body["camara_number"] == "001/2026C"
    assert body["camara_filed_on"] == "2026-07-20"
    assert body["authors_text"] == "H.R. Autora De Ejemplo, H.R. Autor De Prueba"
    assert body["epistemic_label"] == "hecho_documentado"
    assert body["provenance"]["source_name"] == "Proyectos de Ley"
    assert body["provenance"]["original_url"] == "https://www.camara.gov.co/proyecto-a"


def test_unknown_records_and_invalid_paging(client: TestClient, session: Session) -> None:
    missing = uuid.uuid4()
    assert client.get(f"{API}/institutions/{missing}").status_code == 404
    assert client.get(f"{API}/initiatives/{missing}").status_code == 404
    assert client.get(f"{API}/institutions", params={"limit": 1000}).status_code == 422
    assert client.get(f"{API}/initiatives", params={"offset": -1}).status_code == 422


def test_a_repaired_value_is_declared_in_the_provenance(
    client: TestClient, session: Session
) -> None:
    seed_registry(session)
    marker = "No Aplica"
    run_sync(
        session,
        bills.SPEC,
        [
            bill_row("proyecto-a"),
            bill_row("proyecto-reparado", no_senado=marker + marker.join("068/2012 S") + marker),
        ],
    )
    by_number = {}
    for item in client.get(f"{API}/initiatives").json()["items"]:
        body = client.get(f"{API}/initiatives/{item['id']}").json()
        by_number[body["senado_number"]] = body["provenance"]["processing_notes"]

    assert by_number[None] == []
    assert len(by_number["068/2012 S"]) == 1
    assert "reconstruyó" in by_number["068/2012 S"][0]
