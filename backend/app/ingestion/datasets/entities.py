"""Dataset: "Universo de entidades" (Función Pública), datos.gov.co h7zv-k39x.

Fields deliberately NOT ingested (data minimization): fax, email, ccb_telefono,
direccion, and the representative's name and position. The representative is
public-office information and will be modelled as a dated position holding in
a later milestone, not as a column on the institution.
"""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.catalog.models import Institution
from app.core.labels import DataQualityStatus
from app.ingestion.pipeline import DatasetSpec, Payload, RowRejected
from app.ingestion.text import clean, normalize_for_search
from app.search.indexing import index_entry, institution_entry

DATASET_ID = "h7zv-k39x"
SOURCE_REF = f"datos.gov.co:{DATASET_ID}"

ALLOWED_FIELDS = frozenset(
    {
        "dm_institucion_cod_institucion",
        "nombre",
        "ccb_nit_inst",
        "orden",
        "suborden",
        "nivel_institucion",
        "clasificacion_organica",
        "sector",
        "naturaleza_juridica",
        "tipo_institucion",
        "municipio",
        "departamento",
        "ccb_pagina_web",
        "longitud",
        "latitud",
        "estado_ins",
    }
)


def _coordinate(value: object, limit: float) -> float | None:
    text = clean(value)
    if text is None:
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    return number if -limit <= number <= limit and number != 0 else None


def _website(value: object) -> str | None:
    text = clean(value)
    if text is None or " " in text:
        return None
    if not text.lower().startswith(("http://", "https://")):
        text = f"http://{text}"
    return text


def _nit(value: object) -> str | None:
    text = clean(value)
    if text is None:
        return None
    digits = text.replace(".", "").replace("-", "").replace(" ", "")
    return digits if digits.isdigit() and 8 <= len(digits) <= 12 else None


def map_row(payload: Payload) -> dict[str, Any]:
    name = clean(payload.get("nombre"))
    if name is None:
        raise RowRejected("La entidad no tiene nombre")
    nit = _nit(payload.get("ccb_nit_inst"))
    order = clean(payload.get("orden"))
    return {
        "name": name,
        "name_normalized": normalize_for_search(name),
        "nit": nit,
        "order": order,
        "suborder": clean(payload.get("suborden")),
        "level": clean(payload.get("nivel_institucion")),
        "organic_classification": clean(payload.get("clasificacion_organica")),
        "sector": clean(payload.get("sector")),
        "legal_nature": clean(payload.get("naturaleza_juridica")),
        "institution_type": clean(payload.get("tipo_institucion")),
        "department": clean(payload.get("departamento")),
        "municipality": clean(payload.get("municipio")),
        "website": _website(payload.get("ccb_pagina_web")),
        "longitude": _coordinate(payload.get("longitud"), 180),
        "latitude": _coordinate(payload.get("latitud"), 90),
        "status": clean(payload.get("estado_ins")),
        # Documented criterion: an entity record is complete when it has a NIT and an order.
        "data_quality_status": (
            DataQualityStatus.ACCEPTABLE.value
            if nit and order
            else DataQualityStatus.INCOMPLETE.value
        ),
    }


def upsert(
    session: Session, external_id: str, values: dict[str, Any], source_record_id: uuid.UUID
) -> bool:
    institution = session.scalar(
        select(Institution).where(Institution.official_code == external_id)
    )
    inserted = institution is None
    if institution is None:
        institution = Institution(
            id=uuid.uuid4(), official_code=external_id, source_record_id=source_record_id, **values
        )
        session.add(institution)
    else:
        for key, value in values.items():
            setattr(institution, key, value)
        institution.source_record_id = source_record_id
    session.flush()
    index_entry(session, institution_entry(institution))
    return inserted


SPEC = DatasetSpec(
    source_ref=SOURCE_REF,
    extraction_method="socrata-soda-api",
    allowed_fields=ALLOWED_FIELDS,
    external_id=lambda payload: clean(payload.get("dm_institucion_cod_institucion")),
    original_url=lambda _payload: f"https://www.datos.gov.co/d/{DATASET_ID}",
    map_row=map_row,
    upsert=upsert,
)
