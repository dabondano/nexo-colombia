"""Reading laws from Gestor Normativo pages (app/law/statutes.py) and loading them."""

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.ingestion.datasets import laws
from app.ingestion.pipeline import run_sync
from app.law.constitution import StructureError
from app.law.html_blocks import extract_blocks
from app.law.statute_catalog import StatuteSpec
from app.law.statutes import ParsedStatute, read_statute
from app.search.reindex import reindex
from app.sources.registry import seed_registry
from tests.statute_page import article, bold, page, plain

SPEC = StatuteSpec(1, "9999", 2020)


def read(html: str) -> ParsedStatute:
    blocks = extract_blocks(html, content_class="descripcion-contenido", skip_class="card")
    return read_statute(blocks, "9999", 2020)


def paths(parsed: ParsedStatute) -> list[str]:
    return [p.path for p in parsed.provisions]


def test_front_matter_divisions_and_end() -> None:
    parsed = read(
        page(
            bold("TÍTULO I"),
            bold("DISPOSICIONES GENERALES"),
            article("ARTÍCULO 1", "Objeto de la ley."),
            plain("(Modificado por el art. 2 de la Ley 1 de 2021.)"),
            bold("CAPÍTULO 1"),
            bold("DE LOS PRINCIPIOS"),
            article("ARTÍCULO 2o", "Principios."),
            plain("PARÁGRAFO. Un parágrafo del artículo."),
            bold("TÍTULO. II"),
            bold("OTRAS DISPOSICIONES"),
            article("ARTÍCULO 2A", "Artículo agregado después."),
            article("ARTÍCULO 3", "Vigencia."),
        )
    )
    assert parsed.heading == "LEY 9999 DE 2020"
    assert parsed.summary == "Por medio de la cual se dictan normas de ejemplo"
    assert parsed.issued_on == date(2020, 3, 6)
    assert parsed.publication and "Diario Oficial 99.999" in parsed.publication
    assert parsed.article_count == 4  # the page's text after the signatures is not read
    assert paths(parsed) == [
        "titulo-i",
        "articulo-1",
        "titulo-i/capitulo-1",
        "articulo-2",
        "titulo-ii",
        "articulo-2-a",
        "articulo-3",
    ]
    by_path = {p.path: p for p in parsed.provisions}
    assert by_path["titulo-i"].heading == "DISPOSICIONES GENERALES"
    assert by_path["articulo-2"].parent_path == "titulo-i/capitulo-1"
    assert [s.kind for s in by_path["articulo-1"].segments] == ["text", "note"]
    assert [s.kind for s in by_path["articulo-2"].segments] == ["text", "text"]


def test_quoted_articles_of_another_law_stay_in_the_amending_article() -> None:
    parsed = read(
        page(
            article("ARTÍCULO 1", "Sustitúyase el Título II de la Ley 1 de 2000, así:"),
            bold("CAPÍTULO I"),
            bold("REGLAS GENERALES"),
            article("ARTÍCULO 13", "Texto citado de la otra ley."),
            article("ARTÍCULO 14", "Más texto citado."),
            article("ARTÍCULO 2", "Vigencia."),
        )
    )
    assert paths(parsed) == ["articulo-1", "articulo-2"]
    wording = [s.text for s in parsed.provisions[0].segments]
    assert wording[1:3] == ["CAPÍTULO I", "REGLAS GENERALES"]
    assert wording[3].startswith("ARTÍCULO 13")


def test_page_irregularities_are_declared() -> None:
    parsed = read(
        page(
            bold("I. DE LAS DISPOSICIONES GENERALES"),
            article("ARTÍCULO 1", "Uno."),
            bold("*jurisprudencia*"),
            bold("CAPÍTULO CUARTO"),
            plain("DE LAS COMISIONES"),
            plain("Comisiones especiales."),
            article("ARTÍOCULO 2", "Dos (sic en la fuente)."),
            bold("CAPÍTULO CUARTO"),
            plain("DE LAS COMISIONES"),
            article("ARTÍCULO 3", "Tres."),
            article("ARTÍCULO TRANSITORIO", "Sin número."),
        )
    )
    by_path = {p.path: p for p in parsed.provisions}
    assert "sin la palabra «CAPÍTULO»" in by_path["capitulo-i"].repairs[0]
    assert by_path["capitulo-cuarto"].heading == "DE LAS COMISIONES"
    assert by_path["capitulo-cuarto"].label == "Capítulo Cuarto"
    assert "vuelve a imprimir" in by_path["capitulo-cuarto"].repairs[0]
    heading = by_path["capitulo-cuarto/encabezado-1"]
    assert heading.label == "Comisiones especiales." and heading.repairs
    assert by_path["articulo-2"].parent_path == "capitulo-cuarto/encabezado-1"
    assert "articulo-transitorio-1" in by_path
    assert not any("jurisprudencia" in s.text for p in parsed.provisions for s in p.segments)


@pytest.mark.parametrize(
    ("html", "message"),
    [
        (page(article("ARTÍCULO 1", "Uno."), enacting="EL CONGRESO"), "DECRETA"),
        (page(article("ARTÍCULO 1", "Uno."), heading="LEY 1 DE 2020"), "Inicio inesperado"),
        (
            page(article("ARTÍCULO 1", "Uno."), article("ARTÍCULO 7", "Citado sin vuelta.")),
            "no vuelve a la numeración",
        ),
        (page(), "no trae artículos"),
    ],
)
def test_pages_that_do_not_fit_stop(html: str, message: str) -> None:
    with pytest.raises(StructureError, match=message):
        read(html)


SAMPLE = page(
    bold("TÍTULO I"),
    bold("DISPOSICIONES GENERALES"),
    article("ARTÍCULO 1", "El derecho de acceso a la información pública de ejemplo."),
    article("ARTÍCULO 2", "Vigencia."),
)


def test_load_and_read_through_the_api(
    client: TestClient, session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    seed_registry(session)
    monkeypatch.setattr(laws, "STATUTES", (SPEC, StatuteSpec(2, "8888", 2019)))
    monkeypatch.setattr(laws, "PAUSE_SECONDS", 0)
    pages = {SPEC.page_url: SAMPLE, StatuteSpec(2, "8888", 2019).page_url: "<html></html>"}
    monkeypatch.setattr(laws, "fetch_page", lambda spec: pages[spec.page_url])
    result = run_sync(session, laws.SPEC, laws.fetch_rows())
    # The second law's page does not fit the reader: rejected with the reason, not loaded.
    assert result.rows_rejected == 1
    reindex(session)

    listed = client.get("/api/v1/instruments").json()
    law = next(item for item in listed if item["slug"] == "ley-9999-de-2020")
    assert law["title"] == ("Ley 9999 de 2020, por medio de la cual se dictan normas de ejemplo")
    assert law["promulgated_on"] == "2020-03-06"
    assert client.head("/api/v1/instruments/ley-9999-de-2020").status_code == 200
    assert client.head("/api/v1/instruments/ley-1-de-1900").status_code == 404
    detail = client.get("/api/v1/instruments/ley-9999-de-2020").json()
    assert detail["article_count"] == 2
    provision = client.get("/api/v1/instruments/ley-9999-de-2020/provisions/articulo-1").json()
    assert provision["ancestors"][0]["label"] == "Título I"
    hits = client.get(
        "/api/v1/search", params={"q": "acceso informacion", "type": "legal_provision"}
    ).json()["items"]
    assert hits[0]["title"] == "Artículo 1 · Ley 9999 de 2020"
    assert hits[0]["record_key"] == "leyes/ley-9999-de-2020/articulo-1"
