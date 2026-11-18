from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ingestion.datasets import constitution
from app.ingestion.pipeline import Row, run_sync
from app.law.constitution import (
    AFTER_PREVIOUS_MARK,
    NOTE,
    TEXT,
    ParsedProvision,
    StructureError,
    read_constitution,
)
from app.law.html_blocks import Block, extract_blocks, without_struck
from app.law.models import LegalProvision, ProvisionVersion
from app.search.reindex import reindex
from app.sources.models import SyncRun
from app.sources.registry import seed_registry
from tests.constitution_page import page

API = "/api/v1"


def _blocks(html: str) -> list[Block]:
    return extract_blocks(html, content_class="descripcion-contenido", skip_class="card")


def _by_path(html: str) -> dict[str, ParsedProvision]:
    return {p.path: p for p in read_constitution(_blocks(html)).provisions}


def _kinds(provision: ParsedProvision) -> list[tuple[str, str]]:
    return [(s.kind, s.text) for s in provision.segments]


# --- reading the HTML -----------------------------------------------------------


def test_blocks_keep_only_the_norm_and_its_typography() -> None:
    blocks = _blocks(page())
    texts = [b.text for b in blocks]
    assert "Menú del sitio" not in texts and "Pie de página" not in texts
    assert not any("C-000-00" in t or "Jurisprudencia" in t for t in texts)
    heading = next(b for b in blocks if b.text == "PREAMBULO")
    assert heading.centered and heading.bold
    article = next(b for b in blocks if b.text.startswith("ARTÍCULO 13."))
    assert not article.bold and article.struck
    assert article.text == "ARTÍCULO 13. Elegidos por el ⟦Consejo antiguo⟧ Consejo nuevo."
    assert without_struck(article.text) == "ARTÍCULO 13. Elegidos por el Consejo nuevo."


# --- reading the structure ------------------------------------------------------


def test_structure_numbers_titles_and_chapters_the_page_leaves_unlabelled() -> None:
    parsed = read_constitution(_blocks(page()))
    provisions = {p.path: p for p in parsed.provisions}
    assert parsed.title == "CONSTITUCIÓN POLITICA DE LA REPUBLICA DE COLOMBIA 1991"
    assert parsed.transitory_omitted
    assert parsed.latest_reform == (2025, 1)
    assert [p.position for p in parsed.provisions] == list(range(1, len(parsed.provisions) + 1))

    title_2 = provisions["titulo-2"]
    assert (title_2.label, title_2.heading) == ("Título II", "DE LOS DERECHOS")
    assert "TÍTULO II" in title_2.repairs[0]
    assert provisions["titulo-12"].repairs == []  # printed by the page

    chapter_1 = provisions["titulo-2/capitulo-1"]
    assert chapter_1.heading == "DE LOS DERECHOS FUNDAMENTALES" and chapter_1.repairs
    assert provisions["titulo-2/capitulo-2"].repairs == []
    # A name without label inside a title that already has chapters is its next chapter.
    chapter_3 = provisions["titulo-2/capitulo-3"]
    assert chapter_3.heading == "DE LAS JURISDICCIONES ESPECIALES" and chapter_3.repairs
    chapter_3a = provisions["titulo-2/capitulo-3-a"]
    assert chapter_3a.label == "Capítulo 3A"
    assert _kinds(chapter_3a)[0][0] == NOTE

    assert provisions["articulo-1"].parent_path == "titulo-1"
    assert provisions["articulo-11"].parent_path == "titulo-2/capitulo-1"
    assert provisions["articulo-14-a"].label == "Artículo 14A"
    assert provisions["articulo-14-a"].parent_path == "titulo-2/capitulo-3-a"
    # "ARTÍCULO 14. A falta de..." is article 14, not 14A.
    assert _kinds(provisions["articulo-14"]) == [(TEXT, "A falta de regla se aplicará la ley.")]
    assert "articulo-transitorio-1" not in provisions and len(provisions) == 46


def test_structure_keeps_notes_and_earlier_wording_apart_from_the_wording() -> None:
    provisions = _by_path(page())
    assert _kinds(provisions["preambulo"]) == [
        (TEXT, "EL PUEBLO DE COLOMBIA,"),
        (TEXT, "En ejercicio de su poder soberano decreta la siguiente:"),
        (TEXT, "CONSTITUCIÓN POLITICA DE COLOMBIA"),
        (NOTE, "Ver la Constitución Política de 1886"),
    ]
    assert _kinds(provisions["articulo-12"]) == [
        (NOTE, "(Modificado por el Art. 1, Acto legislativo 01 de 2025)"),
        (TEXT, "Nadie será sometido."),
        (TEXT, "Segundo inciso del artículo doce."),
        (NOTE, "(Artículo modificado por el artículo 2 del Acto Legislativo 3 de 2011)"),
        (AFTER_PREVIOUS_MARK, "TEXTO ANTERIOR: Redacción anterior del artículo doce."),
        (AFTER_PREVIOUS_MARK, "Inciso que la fuente imprime después de la marca."),
    ]
    assert _kinds(provisions["articulo-12-a"]) == [(NOTE, "(Artículo INEXEQUIBLE)")]
    # Bold capitals inside an article are wording, not a division.
    assert _kinds(provisions["articulo-13"])[1:] == [
        (TEXT, "PARÁGRAFO ."),
        (TEXT, "Texto del parágrafo."),
    ]
    # The editor's clarification about the headings of Title VII is a note on the title.
    title_7 = provisions["titulo-7"]
    assert title_7.heading == "DE LA RAMA EJECUTIVA"
    assert provisions["titulo-7/capitulo-1"].heading == "DEL PRESIDENTE"
    assert _kinds(title_7) == [
        (NOTE, 'NOTA ACLARATORIA Los epigrafes fueron corregidos. "LA RAMA EJECUTIVA" CAPÍTULO I.')
    ]


def test_structure_stops_when_the_headings_do_not_fit() -> None:
    with pytest.raises(StructureError, match="Título XII"):
        read_constitution(_blocks(page(twelfth="XIV")))
    with pytest.raises(StructureError, match="Inicio inesperado"):
        read_constitution(_blocks('<div class="descripcion-contenido"><p>Otra cosa</p></div>'))


# --- loading ---------------------------------------------------------------------


@pytest.fixture
def loaded(session: Session) -> None:
    seed_registry(session)
    run_sync(session, constitution.SPEC, constitution.rows_from_html(page()))


def _provision(session: Session, path: str) -> LegalProvision:
    return session.scalars(select(LegalProvision).where(LegalProvision.path == path)).one()


def test_load_is_repeatable_and_a_new_wording_adds_a_version(
    session: Session, loaded: None
) -> None:
    again = run_sync(session, constitution.SPEC, constitution.rows_from_html(page()))
    assert (again.rows_new, again.rows_changed, again.rows_unchanged) == (0, 0, 47)

    changed = page(article_1="Colombia es una República unitaria.")
    result = run_sync(session, constitution.SPEC, constitution.rows_from_html(changed))
    assert (result.rows_new, result.rows_changed, result.rows_unchanged) == (0, 1, 46)

    article = _provision(session, "articulo-1")
    versions = session.scalars(
        select(ProvisionVersion)
        .where(ProvisionVersion.provision_id == article.id)
        .order_by(ProvisionVersion.recorded_at)
    ).all()
    assert [v.text for v in versions] == [
        "Colombia es un Estado social de derecho.",
        "Colombia es una República unitaria.",
    ]
    assert versions[0].superseded_at is not None and versions[1].superseded_at is None
    assert session.scalar(select(func.count()).select_from(LegalProvision)) == 46


def test_load_marks_uncertain_articles_and_leaves_out_cross_references(
    session: Session, loaded: None
) -> None:
    def version(path: str) -> ProvisionVersion:
        provision = _provision(session, path)
        return session.scalars(
            select(ProvisionVersion).where(ProvisionVersion.provision_id == provision.id)
        ).one()

    assert _provision(session, "articulo-11").data_quality_status == "acceptable"
    assert version("articulo-11").segments == [
        {"kind": "text", "text": "El derecho a la vida es inviolable. No habrá pena de muerte."}
    ]
    # Earlier wording after the source's mark, struck-through words, or no wording at all.
    for path in ("articulo-12", "articulo-13", "articulo-12-a"):
        assert _provision(session, path).data_quality_status == "incomplete"
    assert (
        version("articulo-12").text == "Nadie será sometido.\n\nSegundo inciso del artículo doce."
    )
    assert version("articulo-13").text.startswith("Elegidos por el Consejo nuevo.")
    assert version("articulo-12-a").text == ""


def test_failed_download_is_recorded_and_changes_nothing(session: Session, loaded: None) -> None:
    def rows() -> Iterator[Row]:
        yield from constitution.rows_from_html(page(twelfth="XIV"))

    with pytest.raises(StructureError):
        run_sync(session, constitution.SPEC, rows())
    statuses = session.scalars(select(SyncRun.status).order_by(SyncRun.started_at)).all()
    assert statuses == ["succeeded", "failed"]
    assert session.scalar(select(func.count()).select_from(LegalProvision)) == 46


# --- API -------------------------------------------------------------------------


def test_api_instrument_outline(client: TestClient, loaded: None) -> None:
    listing = client.get(f"{API}/instruments").json()
    assert [item["slug"] for item in listing] == ["constitucion-politica-1991"]

    body = client.get(f"{API}/instruments/constitucion-politica-1991").json()
    assert body["article_count"] == 18 and body["articles_needing_review"] == 3
    assert "Acto Legislativo 01 de 2025" in body["edition_note"]
    assert "disposiciones transitorias" in body["edition_note"]
    assert body["provenance"]["source_institution"].endswith("Función Pública")
    outline = {item["path"]: item for item in body["outline"]}
    assert outline["articulo-11"]["excerpt"].startswith("El derecho a la vida")
    assert outline["articulo-11"]["parent_id"] == outline["titulo-2/capitulo-1"]["id"]
    assert outline["titulo-2"]["excerpt"] is None
    assert client.get(f"{API}/instruments/no-existe").status_code == 404


def test_api_provision(client: TestClient, session: Session, loaded: None) -> None:
    article = _provision(session, "articulo-12")
    body = client.get(f"{API}/provisions/{article.id}").json()
    assert body["label"] == "Artículo 12" and body["data_quality_status"] == "incomplete"
    assert [a["label"] for a in body["ancestors"]] == ["Título II", "Capítulo 1"]
    assert [s["kind"] for s in body["segments"]] == [
        "note",
        "text",
        "text",
        "note",
        "after_previous_mark",
        "after_previous_mark",
    ]
    assert body["previous"]["label"] == "Artículo 11" and body["next"]["label"] == "Artículo 12A"
    assert body["instrument"]["slug"] == "constitucion-politica-1991"
    assert body["provenance"]["original_url"] == constitution.PAGE_URL

    title = client.get(f"{API}/provisions/{_provision(session, 'titulo-2').id}").json()
    assert title["provenance"]["processing_notes"][0].startswith("La fuente no imprime")
    first = client.get(f"{API}/provisions/{_provision(session, 'preambulo').id}").json()
    assert first["previous"] is None and first["next"]["label"] == "Artículo 1"
    by_path = client.get(f"{API}/instruments/constitucion-politica-1991/provisions/articulo-12")
    assert by_path.json()["id"] == body["id"]
    assert by_path.json()["next"]["path"] == "articulo-12-a"
    no_path = client.get(f"{API}/instruments/constitucion-politica-1991/provisions/articulo-999")
    assert no_path.status_code == 404
    head_url = f"{API}/instruments/constitucion-politica-1991/provisions"
    assert client.head(f"{head_url}/articulo-12").status_code == 200
    assert client.head(f"{head_url}/articulo-999").status_code == 404
    missing = "00000000-0000-0000-0000-000000000000"
    assert client.get(f"{API}/provisions/{missing}").status_code == 404
    assert client.head(f"{API}/provisions/{missing}").status_code == 404
    assert client.head(f"{API}/provisions/{body['id']}").status_code == 200


def test_search_finds_articles_by_number_and_by_wording(
    client: TestClient, session: Session, loaded: None
) -> None:
    def titles(query: str) -> list[str]:
        response = client.get(f"{API}/search", params={"q": query, "type": "legal_provision"})
        return [hit["title"] for hit in response.json()["items"]]

    assert titles("articulo 11")[0] == "Artículo 11"
    assert titles("pena de muerte") == ["Artículo 11"]
    # Earlier wording and editor's notes are not searched.
    assert titles("redacción anterior") == [] and titles("inexequible") == []
    assert reindex(session) == 18  # 17 articles with wording and the preamble
    assert titles("subsuelo") == ["Artículo 332"]
