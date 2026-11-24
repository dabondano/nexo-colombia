"""Dataset: key laws, as published by Función Pública's Gestor Normativo.

One page per law (app/law/statute_catalog.py), read by app/law/statutes.py;
one request per law and synchronization, a second apart. Rows are like the
Constitution's (app/ingestion/datasets/constitution.py), with the law's slug
in each key. A law whose page no longer fits the reader is recorded as a
rejected row with the reason, and the other laws still load.
"""

import ssl
import time
import uuid
from collections.abc import Iterator
from datetime import date
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ingestion.datasets.constitution import (
    _CERTIFICATES,
    USER_AGENT,
    _is_cross_reference,
    map_provision,
    upsert_provision,
)
from app.ingestion.pipeline import DatasetSpec, Payload, Row, RowRejected
from app.law.constitution import StructureError
from app.law.html_blocks import extract_blocks
from app.law.models import LegalInstrument
from app.law.statute_catalog import STATUTES, StatuteSpec
from app.law.statutes import ParsedStatute, read_compilation, read_statute
from app.sources.registry import LAWS_REF

SOURCE_REF = LAWS_REF
GESTOR_URL = "https://www.funcionpublica.gov.co/eva/gestornormativo/"
SEPARATOR = ":"
PAUSE_SECONDS = 1.0
# Laws sit just below the Constitution in the hierarchy shown to readers, decrees below laws.
HIERARCHY_LEVEL = 2
DECREE_LEVEL = 3

ALLOWED_FIELDS = frozenset(
    {
        "key",
        "record",
        "law",
        "law_number",
        "law_year",
        "title",
        "summary",
        "instrument_type",
        "issued_on",
        "publication",
        "page_url",
        "reason",
        "parent",
        "kind",
        "label",
        "number",
        "heading",
        "position",
        "segments",
        "repairs",
    }
)


def fetch_page(spec: StatuteSpec) -> str:
    context = ssl.create_default_context()
    context.load_verify_locations(cafile=str(_CERTIFICATES))
    response = httpx.get(
        spec.page_url, verify=context, timeout=120, headers={"User-Agent": USER_AGENT}
    )
    response.raise_for_status()
    return response.text


def to_rows(spec: StatuteSpec, parsed: ParsedStatute) -> list[Row]:
    rows: list[Row] = [
        {
            "key": spec.slug,
            "record": "instrument",
            "law": spec.slug,
            "law_number": spec.number,
            "law_year": spec.year,
            "title": parsed.heading,
            "summary": parsed.summary,
            "instrument_type": parsed.instrument_type,
            "issued_on": parsed.issued_on.isoformat() if parsed.issued_on else None,
            "publication": parsed.publication,
            "page_url": spec.page_url,
        }
    ]
    rows.extend(
        {
            "key": f"{spec.slug}{SEPARATOR}{provision.path}",
            "record": "provision",
            "law": spec.slug,
            "parent": provision.parent_path,
            "kind": provision.kind,
            "label": provision.label,
            "number": provision.number,
            "heading": provision.heading,
            "position": provision.position,
            "segments": [
                {"kind": s.kind, "text": s.text}
                for s in provision.segments
                if not _is_cross_reference(s)
            ],
            "repairs": provision.repairs,
            "page_url": spec.page_url,
        }
        for provision in parsed.provisions
    )
    return rows


def rows_for(spec: StatuteSpec, html: str) -> list[Row]:
    blocks = extract_blocks(html, content_class="descripcion-contenido", skip_class="card")
    if spec.compiled:
        parsed = read_compilation(
            blocks, spec.number, spec.year, spec.compiled.name, spec.compiled.articles
        )
    else:
        parsed = read_statute(blocks, spec.number, spec.year)
    return to_rows(spec, parsed)


def fetch_rows() -> Iterator[Row]:
    for index, spec in enumerate(STATUTES):
        if index:
            time.sleep(PAUSE_SECONDS)
        try:
            rows = rows_for(spec, fetch_page(spec))
        except (StructureError, httpx.HTTPError) as error:
            yield {
                "key": spec.slug,
                "record": "error",
                "law": spec.slug,
                "page_url": spec.page_url,
                "reason": f"{type(error).__name__}: {error}",
            }
            continue
        yield from rows


EDITION_NOTE = (
    "Edición informativa publicada por Función Pública, que advierte que no se hace responsable "
    "de la vigencia de la norma y que actualiza sus contenidos de forma permanente. El texto con "
    "valor oficial es el publicado en el Diario Oficial. NEXO no ha comprobado si hay reformas "
    "posteriores a las que menciona esta edición."
)


def map_row(payload: Payload) -> dict[str, Any]:
    record = payload.get("record")
    if record == "error":
        raise RowRejected(f"La página de la ley no se pudo leer: {payload.get('reason')}")
    if record == "instrument":
        if not payload.get("title"):
            raise RowRejected("La página no trae el título de la ley")
        return {
            "record": "instrument",
            "law": payload["law"],
            "number": str(payload["law_number"]),
            "year": int(payload["law_year"]),
            "title": payload["title"],
            "summary": payload.get("summary"),
            "instrument_type": payload.get("instrument_type") or "ley",
            "issued_on": payload.get("issued_on"),
            "publication": payload.get("publication"),
        }
    return {"law": payload["law"], **map_provision(payload)}


def _instrument(session: Session, slug: str) -> LegalInstrument | None:
    return session.scalar(select(LegalInstrument).where(LegalInstrument.slug == slug))


def upsert(
    session: Session, external_id: str, values: dict[str, Any], source_record_id: uuid.UUID
) -> bool:
    values = dict(values)
    slug = values.pop("law")
    if values.get("record") == "instrument":
        values.pop("record")
        instrument = _instrument(session, slug)
        inserted = instrument is None
        if instrument is None:
            instrument = LegalInstrument(
                id=uuid.uuid4(),
                slug=slug,
                instrument_type=values["instrument_type"],
                number=values["number"],
                year=values["year"],
                hierarchy_level=(
                    DECREE_LEVEL if values["instrument_type"] == "decreto" else HIERARCHY_LEVEL
                ),
                title=values["title"],
                source_record_id=source_record_id,
            )
            session.add(instrument)
        name = f"{values['instrument_type'].capitalize()} {values['number']} de {values['year']}"
        instrument.title = _title(name, values.get("summary"))
        instrument.instrument_type = values["instrument_type"]
        issued = values.get("issued_on")
        instrument.promulgated_on = date.fromisoformat(issued) if issued else None
        instrument.official_publication_ref = values.get("publication")
        instrument.edition_note = EDITION_NOTE
        instrument.source_record_id = source_record_id
        session.flush()
        return inserted
    instrument = _instrument(session, slug)
    if instrument is None:
        raise LookupError("La ley debe cargarse antes que sus disposiciones")
    path = external_id.split(SEPARATOR, 1)[1]
    values.pop("record", None)
    return upsert_provision(session, instrument, path, values, source_record_id)


def _title(name: str, summary: str | None) -> str:
    """ "Ley 1712 de 2014, por medio de la cual se crea..." as one line."""
    if not summary:
        return name
    text = " ".join(summary.split())
    if text.isupper():
        text = text.capitalize()
    return f"{name}, {text[0].lower()}{text[1:]}".rstrip(" .\"”'")


SPEC = DatasetSpec(
    source_ref=SOURCE_REF,
    extraction_method="html-page",
    allowed_fields=ALLOWED_FIELDS,
    external_id=lambda payload: payload.get("key"),
    original_url=lambda payload: payload.get("page_url") or GESTOR_URL,
    map_row=map_row,
    upsert=upsert,
)
