import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.congress.models import Person, PositionHolding
from app.core.relationships import Relationship
from app.ingestion.datasets import bills, representatives
from app.ingestion.pipeline import RowRejected, run_sync
from app.legislation.authors import link_authors, split_authors
from app.sources.models import SyncReject
from app.sources.registry import seed_registry
from tests.samples import bill_row, representative_row

API = "/api/v1"
OPPOSITION_BASIS = (
    "C.P. Art. 112, A.L. 02 de 2015 Art. 1 y Est. de Oposición Ley, 1909 de 2018 Art. 24"
)


def test_shifted_columns_are_mapped_by_content() -> None:
    values = representatives.map_row(
        representative_row(comision_legal="+(57) (601) 0000000 Ext: 1234")
    )
    assert values["full_name"] == "Autora De Ejemplo"
    assert values["constituency"] == "BOYACÁ"
    assert values["party"] == "Partido De Ejemplo"
    assert values["email"] == "autora.ejemplo@camara.gov.co"
    assert values["office"] == "000B - Edificio de ejemplo"
    assert values["phone"] == "+(57) (601) 0000000 Ext: 1234"
    assert values["period"] == "2026-2027"
    assert values["processing_notes"] == [representatives.SHIFT_NOTE]


def test_opposition_seat_keeps_its_legal_basis_apart_from_the_party() -> None:
    values = representatives.map_row(
        representative_row(apelidos_y_nombre="OPOSICIÓN", partido_o_movimiento=OPPOSITION_BASIS)
    )
    assert values["party"] is None
    assert values["seat_basis"] == OPPOSITION_BASIS
    assert representatives.OPPOSITION_NOTE in values["processing_notes"]


def test_a_row_in_another_layout_is_rejected() -> None:
    # As if the source fixed its column names: the mapping must stop, not guess.
    fixed = {
        "apelidos_y_nombre": "Autora De Ejemplo",
        "circunscripcion": "BOYACÁ",
        "partido_o_movimiento": "Partido De Ejemplo",
    }
    with pytest.raises(RowRejected):
        representatives.map_row(fixed)
    with pytest.raises(RowRejected):
        representatives.map_row(representative_row(apelidos_y_nombre="otra@camara.gov.co"))


def test_the_most_complete_row_of_each_member_comes_first() -> None:
    short = representative_row()
    short.pop("comision_const")
    full = representative_row()
    other = representative_row("Autor De Prueba", "autor.prueba@camara.gov.co")
    ordered = representatives.order_rows([short, other, full])
    assert ordered == [full, short, other]


def test_split_authors() -> None:
    text = "H.R. Ana Pérez Gómez, Juan Ruiz Díaz,  H.S. Luz Mar, y otras firmas."
    assert split_authors(text) == ["Ana Pérez Gómez", "Juan Ruiz Díaz", "Luz Mar"]
    assert split_authors("Ministerio de Ejemplo") == ["Ministerio de Ejemplo"]


@pytest.fixture
def loaded(session: Session) -> None:
    seed_registry(session)
    short = representative_row()
    short.pop("comision_const")
    run_sync(
        session,
        representatives.SPEC,
        representatives.order_rows(
            [
                short,
                representative_row(),
                representative_row(
                    "Autor De Prueba",
                    "autor.prueba@camara.gov.co",
                    apelidos_y_nombre="OPOSICIÓN",
                    partido_o_movimiento=OPPOSITION_BASIS,
                ),
                # Two members with the same name: never linked.
                representative_row("Nombre Repetido", "repetido.uno@camara.gov.co"),
                representative_row("Nombre Repetido", "repetido.dos@camara.gov.co"),
            ]
        ),
    )
    run_sync(
        session,
        bills.SPEC,
        [
            # Filed in the term; one author written without accents and capitals.
            bill_row(
                "proyecto-en-el-periodo",
                autores="H.R. autora de ejemplo, Autor de Prueba, Nombre Repetido, y otras firmas",
            ),
            # Filed before the term: a namesake may be another person.
            bill_row(
                "proyecto-anterior",
                fecha_c_mara="2025 Aug 01 12:00:00 AM",
                legislatura="2025-2026",
                autores="H.R. Autora De Ejemplo",
            ),
        ],
    )


def test_duplicate_rows_are_listed_and_the_complete_one_is_published(
    session: Session, loaded: None
) -> None:
    assert session.scalar(select(func.count()).select_from(PositionHolding)) == 4
    reject = session.scalars(select(SyncReject)).one()
    assert reject.external_id == "autora.ejemplo@camara.gov.co"
    assert "comision_const" not in reject.payload
    holding = session.scalars(
        select(PositionHolding).where(PositionHolding.source_key == reject.external_id)
    ).one()
    assert holding.office == "000B - Edificio de ejemplo"


def test_authors_link_only_on_a_single_exact_match_within_the_term(
    session: Session, loaded: None
) -> None:
    result = link_authors(session)
    assert result.initiatives_considered == 1
    assert result.links == 2
    assert result.ambiguous == 1
    names = set(session.scalars(select(Relationship.evidence)))
    assert names == {"autora de ejemplo", "Autor de Prueba"}
    # Running again replaces the links instead of adding to them.
    assert link_authors(session).links == 2
    assert session.scalar(select(func.count()).select_from(Relationship)) == 2
    link = session.scalars(select(Relationship)).first()
    assert link is not None
    assert (link.subject_type, link.predicate, link.object_type) == (
        "person",
        "author_of",
        "legislative_initiative",
    )
    assert link.confidence_class == "analytical_association"
    assert link.epistemic_label == "hipotesis_analitica"
    assert link.source_record_id is not None and link.method_note


def test_representatives_api(client: TestClient, session: Session, loaded: None) -> None:
    link_authors(session)
    page = client.get(f"{API}/representatives", params={"q": "autora"}).json()
    assert page["total"] == 1
    item = page["items"][0]
    assert item["full_name"] == "Autora De Ejemplo" and item["constituency"] == "BOYACÁ"

    body = client.get(f"{API}/representatives/{item['id']}").json()
    assert body["email"] == "autora.ejemplo@camara.gov.co"
    assert body["epistemic_label"] == "hecho_documentado"
    assert body["provenance"]["source_name"] == "Representantes período 2026-2027"
    assert body["provenance"]["processing_notes"] == [representatives.SHIFT_NOTE]
    assert [bill["author_name"] for bill in body["authored_initiatives"]] == ["autora de ejemplo"]
    assert body["authored_initiatives_label"] == "hipotesis_analitica"
    assert client.head(f"{API}/representatives/{item['id']}").status_code == 200
    assert client.head(f"{API}/representatives/{uuid.uuid4()}").status_code == 404
    assert client.get(f"{API}/representatives/{uuid.uuid4()}").status_code == 404

    opposition = client.get(f"{API}/representatives", params={"constituency": "OPOSICIÓN"})
    assert opposition.json()["items"][0]["seat_basis"] == OPPOSITION_BASIS
    filters = client.get(f"{API}/representatives/filters").json()
    assert {"value": "BOYACÁ", "count": 3} in filters["constituency"]

    bill_id = body["authored_initiatives"][0]["id"]
    bill = client.get(f"{API}/initiatives/{bill_id}").json()
    assert {author["full_name"] for author in bill["linked_authors"]} == {
        "Autora De Ejemplo",
        "Autor De Prueba",
    }
    assert bill["linked_authors_label"] == "hipotesis_analitica"

    found = client.get(f"{API}/search", params={"q": "autor de prueba"}).json()
    assert found["items"][0]["record_type"] == "representative"
    person = session.scalars(select(Person).where(Person.full_name == "Autor De Prueba")).one()
    assert person.name_normalized == "autor de prueba"
