"""Dataset: Constitución Política de 1991, as published by Función Pública.

Source: Gestor Normativo, norm 4125 (one HTML page). robots.txt of the site
allowed every path on 2026-11-17. One request per synchronization.

Each row is one provision (preamble, title, chapter or article); the first row
describes the instrument itself. Only the permanent text is loaded; see
app/law/constitution.py for what is kept apart from the wording and why. The
editor's lists of cross-references "(Ver Ley ...)" are not loaded; notes about
reforms and court rulings on the article are.
"""

import ssl
import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.labels import DataQualityStatus
from app.ingestion.pipeline import PROCESSING_NOTES, DatasetSpec, Payload, Row, RowRejected
from app.law.constitution import (
    AFTER_PREVIOUS_MARK,
    ARTICLE,
    NOTE,
    TEXT,
    ParsedInstrument,
    Segment,
    read_constitution,
)
from app.law.html_blocks import STRUCK_CLOSE, STRUCK_OPEN, extract_blocks, without_struck
from app.law.models import LegalInstrument, LegalProvision, ProvisionVersion
from app.search.indexing import index_entry, provision_entry
from app.sources.registry import CONSTITUTION_REF

SOURCE_REF = CONSTITUTION_REF
PAGE_URL = "https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=4125"
SLUG = "constitucion-politica-1991"
INSTRUMENT_KEY = "instrumento"
USER_AGENT = "NEXO-Colombia/0.1 (plataforma civica de informacion publica)"
_CERTIFICATES = Path(__file__).resolve().parents[2] / "law" / "certs" / "letsencrypt-yr1-chain.pem"

ALLOWED_FIELDS = frozenset(
    {
        "key",
        "record",
        "title",
        "latest_reform",
        "transitory_omitted",
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


def fetch_page() -> str:
    """Download the page, verifying the server's certificate (app/law/certs/README.md)."""
    context = ssl.create_default_context()
    context.load_verify_locations(cafile=str(_CERTIFICATES))
    response = httpx.get(PAGE_URL, verify=context, timeout=120, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    return response.text


def _is_cross_reference(segment: Segment) -> bool:
    """Lists "(Ver Ley ...)" compiled by the editor: not loaded (data minimization)."""
    return segment.kind == NOTE and segment.text.lstrip("( ").casefold().startswith("ver")


def to_rows(parsed: ParsedInstrument) -> list[Row]:
    reform = parsed.latest_reform
    rows: list[Row] = [
        {
            "key": INSTRUMENT_KEY,
            "record": "instrument",
            "title": parsed.title,
            "latest_reform": f"Acto Legislativo {reform[1]:02d} de {reform[0]}" if reform else None,
            "transitory_omitted": parsed.transitory_omitted,
        }
    ]
    rows.extend(
        {
            "key": provision.path,
            "record": "provision",
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
        }
        for provision in parsed.provisions
    )
    return rows


def rows_from_html(html: str) -> list[Row]:
    blocks = extract_blocks(html, content_class="descripcion-contenido", skip_class="card")
    return to_rows(read_constitution(blocks))


def fetch_rows() -> Iterator[Row]:
    """Rows are produced lazily, so a failed download or an unexpected page
    structure is recorded by the pipeline as a failed synchronization."""
    yield from rows_from_html(fetch_page())


def _edition_note(payload: Payload) -> str:
    parts = [
        "Edición informativa publicada por Función Pública, que advierte que no se hace "
        "responsable de la vigencia de la norma y que actualiza sus contenidos de forma "
        "permanente. El texto con valor oficial es el publicado en la Gaceta Constitucional "
        "y en el Diario Oficial."
    ]
    if payload.get("latest_reform"):
        parts.append(
            f"La reforma más reciente que menciona esta edición es el {payload['latest_reform']}. "
            "NEXO no ha comprobado si existen reformas posteriores."
        )
    if payload.get("transitory_omitted"):
        parts.append("NEXO todavía no carga las disposiciones transitorias.")
    return " ".join(parts)


def map_row(payload: Payload) -> dict[str, Any]:
    if payload.get("record") == "instrument":
        title = payload.get("title")
        if not title:
            raise RowRejected("La página no trae el título de la norma")
        return {"record": "instrument", "title": title, "edition_note": _edition_note(payload)}

    segments: list[dict[str, str]] = payload.get("segments") or []
    wording = [without_struck(s["text"]) for s in segments if s["kind"] == TEXT]
    text = "\n\n".join(part for part in wording if part)
    uncertain = any(
        s["kind"] == AFTER_PREVIOUS_MARK or STRUCK_OPEN in s["text"] or STRUCK_CLOSE in s["text"]
        for s in segments
    )
    notes: list[str] = list(payload.get("repairs") or [])
    quality = DataQualityStatus.ACCEPTABLE
    if payload["kind"] == ARTICLE and (uncertain or not text):
        # Documented criterion: an article is incomplete when the source mixes its
        # wording with earlier or struck-through wording, or prints no wording.
        quality = DataQualityStatus.INCOMPLETE
    return {
        "record": "provision",
        "parent": payload.get("parent"),
        "kind": payload["kind"],
        "label": payload["label"],
        "number": payload.get("number"),
        "heading": payload.get("heading"),
        "position": payload["position"],
        "text": text,
        "segments": segments,
        "data_quality_status": quality.value,
        PROCESSING_NOTES: notes,
    }


def _instrument(session: Session) -> LegalInstrument | None:
    return session.scalar(select(LegalInstrument).where(LegalInstrument.slug == SLUG))


def _upsert_instrument(
    session: Session, values: dict[str, Any], source_record_id: uuid.UUID
) -> bool:
    instrument = _instrument(session)
    inserted = instrument is None
    if instrument is None:
        instrument = LegalInstrument(
            id=uuid.uuid4(),
            slug=SLUG,
            instrument_type="constitución",
            year=1991,
            hierarchy_level=1,
            title=values["title"],
            source_record_id=source_record_id,
        )
        session.add(instrument)
    instrument.title = values["title"]
    instrument.edition_note = values["edition_note"]
    instrument.source_record_id = source_record_id
    session.flush()
    return inserted


def upsert(
    session: Session, external_id: str, values: dict[str, Any], source_record_id: uuid.UUID
) -> bool:
    values = dict(values)
    if values.pop("record") == "instrument":
        return _upsert_instrument(session, values, source_record_id)

    instrument = _instrument(session)
    if instrument is None:
        raise LookupError("La norma debe cargarse antes que sus disposiciones")
    parent_path = values.pop("parent")
    text, segments = values.pop("text"), values.pop("segments")
    parent_id = None
    if parent_path:
        parent_id = session.scalar(
            select(LegalProvision.id).where(
                LegalProvision.instrument_id == instrument.id, LegalProvision.path == parent_path
            )
        )
        if parent_id is None:
            raise LookupError(f"No se encontró la división {parent_path!r} de {external_id!r}")

    provision = session.scalar(
        select(LegalProvision).where(
            LegalProvision.instrument_id == instrument.id, LegalProvision.path == external_id
        )
    )
    inserted = provision is None
    if provision is None:
        provision = LegalProvision(
            id=uuid.uuid4(),
            instrument_id=instrument.id,
            path=external_id,
            source_record_id=source_record_id,
            **values,
        )
        session.add(provision)
    else:
        for key, value in values.items():
            setattr(provision, key, value)
        provision.source_record_id = source_record_id
    provision.parent_id = parent_id
    session.flush()

    current = session.scalar(
        select(ProvisionVersion).where(
            ProvisionVersion.provision_id == provision.id, ProvisionVersion.superseded_at.is_(None)
        )
    )
    if current is None or current.segments != segments:
        if current is not None:
            current.superseded_at = session.scalar(select(func.now()))
            session.flush()  # before the new version: only one may be current
        session.add(
            ProvisionVersion(
                provision_id=provision.id,
                text=text,
                segments=segments,
                source_record_id=source_record_id,
            )
        )
        session.flush()
    if text:
        index_entry(session, provision_entry(provision, instrument, text))
    return inserted


SPEC = DatasetSpec(
    source_ref=SOURCE_REF,
    extraction_method="html-page",
    allowed_fields=ALLOWED_FIELDS,
    external_id=lambda payload: payload.get("key"),
    original_url=lambda _payload: PAGE_URL,
    map_row=map_row,
    upsert=upsert,
)
