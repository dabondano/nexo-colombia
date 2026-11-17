"""Dataset: "Proyectos de Ley" (Cámara de Representantes), datos.gov.co kcxp-nxum.

The dataset's own sequence number ("no_") is a position in the list and changes
when bills are added, so the initiative's page URL at the Cámara is used as the
stable identifier.
"""

import re
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.labels import DataQualityStatus
from app.ingestion.pipeline import PROCESSING_NOTES, DatasetSpec, Payload, RowRejected
from app.ingestion.text import clean, normalize_for_search, parse_socrata_date
from app.legislation.models import LegislativeInitiative

DATASET_ID = "kcxp-nxum"
SOURCE_REF = f"datos.gov.co:{DATASET_ID}"

ALLOWED_FIELDS = frozenset(
    {
        "no_c_mara",
        "no_senado",
        "fecha_c_mara",
        "fecha_senado",
        "proyecto",
        "t_tulo",
        "objeto_del_proyecto",
        "observaciones",
        "tipo_de_ley",
        "autores",
        "estado_de_ley",
        "origen_de_ley",
        "comisi_n_es_",
        "legislatura",
        "link_del_proyecto",
    }
)

# Text the source system writes into rows when its own loading process fails.
PLACEHOLDER_MARKERS = ("falla en el aplicativo",)


# What a bill number looks like, e.g. "343/2013 C", "068/2012 S", "151/2026C".
BILL_NUMBER = re.compile(r"\d{1,4}/\d{2,4} ?[A-Za-z]{0,2}")
MAX_NUMBER_LENGTH = 100
_INTERLEAVED_MARKER = "No Aplica"


def _undo_interleaving(text: str) -> str | None:
    """Reverse a known defect of the source.

    In some rows the Senate number arrives with the text "No Aplica" inserted
    before, after and between every character: "068/2012 S" is published as
    "No Aplica0No Aplica6No Aplica8No Aplica/...". The original value is
    recovered only when every piece between markers is exactly one character
    and the result looks like a bill number; otherwise nothing is assumed.
    The value as published stays in the raw source record.
    """
    parts = text.split(_INTERLEAVED_MARKER)
    if len(parts) < 3 or parts[0] or parts[-1]:
        return None
    inner = parts[1:-1]
    if any(len(piece) != 1 for piece in inner):
        return None
    candidate = "".join(inner).strip()
    return candidate if BILL_NUMBER.fullmatch(candidate) else None


def _bill_number(value: object, chamber: str, notes: list[str]) -> str | None:
    if isinstance(value, str) and _INTERLEAVED_MARKER in value:
        if value.strip().casefold() == _INTERLEAVED_MARKER.casefold():
            return None
        recovered = _undo_interleaving(value.strip())
        if recovered is not None:
            notes.append(
                f"El número de {chamber} llegó de la fuente con el texto «No Aplica» "
                "intercalado entre sus caracteres. NEXO lo reconstruyó quitando ese texto; "
                "el valor tal como se publicó se conserva en el registro original."
            )
        return recovered
    text = clean(value)
    if text is None or len(text) > MAX_NUMBER_LENGTH:
        return None
    return text


def _link(payload: Payload) -> str | None:
    link = payload.get("link_del_proyecto")
    url = link.get("url") if isinstance(link, dict) else link
    text = clean(url)
    return text if text and text.lower().startswith(("http://", "https://")) else None


def map_row(payload: Payload) -> dict[str, Any]:
    title = clean(payload.get("t_tulo"))
    if title is None:
        raise RowRejected("El proyecto no tiene título")
    if any(marker in title.casefold() for marker in PLACEHOLDER_MARKERS):
        raise RowRejected("Fila de relleno del sistema de origen (falla en el aplicativo)")

    notes: list[str] = []
    camara_number = _bill_number(payload.get("no_c_mara"), "Cámara", notes)
    senado_number = _bill_number(payload.get("no_senado"), "Senado", notes)
    legislature = clean(payload.get("legislatura"))
    authors = clean(payload.get("autores"))
    has_number = camara_number is not None or senado_number is not None
    return {
        "camara_number": camara_number,
        "senado_number": senado_number,
        "camara_filed_on": parse_socrata_date(payload.get("fecha_c_mara")),
        "senado_filed_on": parse_socrata_date(payload.get("fecha_senado")),
        "short_title": clean(payload.get("proyecto")),
        "title": title,
        "title_normalized": normalize_for_search(title),
        "purpose": clean(payload.get("objeto_del_proyecto")),
        "observations": clean(payload.get("observaciones")),
        "law_type": clean(payload.get("tipo_de_ley")),
        "authors_text": authors,
        "authors_normalized": normalize_for_search(authors) if authors else None,
        "status": clean(payload.get("estado_de_ley")),
        "origin_chamber": clean(payload.get("origen_de_ley")),
        "commission": clean(payload.get("comisi_n_es_")),
        "legislature": legislature,
        # Documented criterion: complete when it has a number and a legislature.
        "data_quality_status": (
            DataQualityStatus.ACCEPTABLE.value
            if has_number and legislature
            else DataQualityStatus.INCOMPLETE.value
        ),
        PROCESSING_NOTES: notes,
    }


def upsert(
    session: Session, external_id: str, values: dict[str, Any], source_record_id: uuid.UUID
) -> bool:
    existing = session.scalar(
        select(LegislativeInitiative).where(LegislativeInitiative.source_key == external_id)
    )
    if existing is None:
        session.add(
            LegislativeInitiative(
                source_key=external_id, source_record_id=source_record_id, **values
            )
        )
        return True
    for key, value in values.items():
        setattr(existing, key, value)
    existing.source_record_id = source_record_id
    return False


SPEC = DatasetSpec(
    source_ref=SOURCE_REF,
    extraction_method="socrata-soda-api",
    allowed_fields=ALLOWED_FIELDS,
    external_id=_link,
    original_url=_link,
    map_row=map_row,
    upsert=upsert,
)
