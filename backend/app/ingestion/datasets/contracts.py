"""Dataset: "SECOP II - Contratos Electrónicos" (Colombia Compra Eficiente),
datos.gov.co jbjy-vk9h (source S-001).

Scope (A-015, owner decision of 2026-11-24): contracts of entities the source
classifies as national order, signed in the last `settings.secop_window_days`
days (90 by default): about 45,000 of the dataset's 5.7 million rows. Each
contract costs about 3.7 KB with its raw copy; the window keeps the database
within the free plan. Contracts that leave the window are removed from NEXO
(app/procurement/retention.py); SECOP keeps them.

Data minimization (brief 5.5, source registry S-001): only the columns in
FIELDS are requested from the portal, so names and ID numbers of spending
officers, supervisors and legal representatives, and the bank fields, are
never downloaded. Before anything is stored, the supplier's name and document
number are removed unless the supplier is identified by a NIT (a company or
other legal person): natural persons are not named (A-015).

Checked on 2026-11-24 against the rows in scope: in no row do payments exceed
the contract value or invoices; one row has invoices above the value; 860 have
a value of 0 (loans of use, agreements without funds), kept as published.
"""

import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.labels import DataQualityStatus
from app.ingestion.pipeline import DatasetSpec, Payload, RowRejected
from app.ingestion.socrata import Row
from app.ingestion.text import clean, normalize_for_search
from app.procurement.models import Contract
from app.search.indexing import contract_entry, index_entry

DATASET_ID = "jbjy-vk9h"
SOURCE_REF = f"datos.gov.co:{DATASET_ID}"
DATASET_URL = f"https://www.datos.gov.co/d/{DATASET_ID}"

COMPANY_DOCUMENT = "NIT"
SUPPLIER_IDENTITY = ("proveedor_adjudicado", "documento_proveedor")

AMOUNTS = {
    "valor_del_contrato": "value",
    "valor_facturado": "invoiced",
    "valor_pagado": "paid",
    "valor_pendiente_de_pago": "pending_payment",
    "valor_pendiente_de_ejecucion": "pending_execution",
}
FIELDS = (
    "id_contrato",
    "proceso_de_compra",
    "referencia_del_contrato",
    "nombre_entidad",
    "nit_entidad",
    "departamento",
    "ciudad",
    "orden",
    "sector",
    "rama",
    "estado_contrato",
    "tipo_de_contrato",
    "modalidad_de_contratacion",
    "justificacion_modalidad_de",
    "objeto_del_contrato",
    "fecha_de_firma",
    "fecha_de_inicio_del_contrato",
    "fecha_de_fin_del_contrato",
    "duraci_n_del_contrato",
    "dias_adicionados",
    "tipodocproveedor",
    *SUPPLIER_IDENTITY,
    "es_pyme",
    "origen_de_los_recursos",
    "destino_gasto",
    *AMOUNTS,
    "urlproceso",
    "ultima_actualizacion",
)
ALLOWED_FIELDS = frozenset(FIELDS)


def window_start(today: date | None = None) -> date:
    return (today or date.today()) - timedelta(days=get_settings().secop_window_days)


def where_clause(today: date | None = None) -> str:
    return f"orden = 'Nacional' AND fecha_de_firma >= '{window_start(today).isoformat()}T00:00:00'"


def minimize(row: Row) -> Row:
    """Drops the supplier's name and number unless the supplier has a NIT."""
    if clean(row.get("tipodocproveedor")) == COMPANY_DOCUMENT:
        return row
    return {key: value for key, value in row.items() if key not in SUPPLIER_IDENTITY}


def _amount(value: object, field: str, *, required: bool = False) -> Decimal | None:
    text = clean(value)
    if text is None:
        if required:
            raise RowRejected(f"Falta el valor de «{field}»")
        return None
    try:
        amount = Decimal(text)
    except InvalidOperation:
        raise RowRejected(f"El valor de «{field}» no es un número") from None
    if not amount.is_finite() or amount < 0:
        raise RowRejected(f"El valor de «{field}» es negativo o no es válido")
    return amount


def _date(value: object, field: str, *, required: bool = False) -> date | None:
    text = clean(value)
    if text is None:
        if required:
            raise RowRejected(f"Falta la fecha «{field}»")
        return None
    try:
        return datetime.fromisoformat(text[:19]).date()
    except ValueError:
        raise RowRejected(f"La fecha «{field}» no es válida") from None


def _timestamp(value: object) -> datetime | None:
    text = clean(value)
    if text is None:
        return None
    try:
        return datetime.fromisoformat(text[:19])
    except ValueError:
        return None


def _int(value: object) -> int | None:
    text = clean(value)
    return int(text) if text is not None and text.isdigit() else None


def _yes_no(value: object) -> bool | None:
    text = (clean(value) or "").lower()
    return {"si": True, "sí": True, "no": False}.get(text)


def _url(value: object) -> str | None:
    if isinstance(value, dict):
        value = value.get("url")
    text = clean(value)
    return text if text and text.startswith("https://") else None


def _supplier(payload: Payload) -> dict[str, Any]:
    document_type = clean(payload.get("tipodocproveedor"))
    if document_type == COMPANY_DOCUMENT:
        return {
            "supplier_kind": "empresa",
            "supplier_name": clean(payload.get("proveedor_adjudicado")),
            "supplier_nit": clean(payload.get("documento_proveedor")),
        }
    kind = "sin_definir" if document_type in (None, "No Definido", "Otro") else "persona_natural"
    return {"supplier_kind": kind, "supplier_name": None, "supplier_nit": None}


def map_row(payload: Payload) -> dict[str, Any]:
    entity = clean(payload.get("nombre_entidad"))
    if entity is None:
        raise RowRejected("La fila no tiene nombre de entidad")
    purpose = clean(payload.get("objeto_del_contrato"))
    if purpose is None:
        raise RowRejected("La fila no tiene objeto del contrato")
    amounts = {
        target: _amount(payload.get(field), field, required=target == "value")
        for field, target in AMOUNTS.items()
    }
    value, invoiced, paid = amounts["value"], amounts["invoiced"], amounts["paid"]
    # Documented criterion: what was paid cannot exceed what was invoiced, nor
    # what was invoiced the contract value.
    consistent = not (
        (invoiced is not None and value is not None and invoiced > value)
        or (paid is not None and invoiced is not None and paid > invoiced)
    )
    return {
        "process_id": clean(payload.get("proceso_de_compra")),
        "reference": clean(payload.get("referencia_del_contrato")),
        "entity_name": entity,
        "entity_nit": clean(payload.get("nit_entidad")),
        "department": clean(payload.get("departamento")),
        "city": clean(payload.get("ciudad")),
        "sector": clean(payload.get("sector")),
        "branch": clean(payload.get("rama")),
        "status": clean(payload.get("estado_contrato")),
        "contract_type": clean(payload.get("tipo_de_contrato")),
        "modality": clean(payload.get("modalidad_de_contratacion")),
        "modality_reason": clean(payload.get("justificacion_modalidad_de")),
        "purpose": purpose,
        "purpose_normalized": normalize_for_search(purpose),
        "signed_on": _date(payload.get("fecha_de_firma"), "fecha_de_firma", required=True),
        "start_on": _date(payload.get("fecha_de_inicio_del_contrato"), "fecha de inicio"),
        "end_on": _date(payload.get("fecha_de_fin_del_contrato"), "fecha de fin"),
        "duration_text": clean(payload.get("duraci_n_del_contrato")),
        "days_added": _int(payload.get("dias_adicionados")),
        **_supplier(payload),
        "supplier_is_sme": _yes_no(payload.get("es_pyme")),
        "resource_origin": clean(payload.get("origen_de_los_recursos")),
        "spending_type": clean(payload.get("destino_gasto")),
        **amounts,
        "process_url": _url(payload.get("urlproceso")),
        "source_updated_at": _timestamp(payload.get("ultima_actualizacion")),
        "data_quality_status": (
            DataQualityStatus.ACCEPTABLE.value
            if consistent
            else DataQualityStatus.CONFLICTING.value
        ),
    }


def upsert(
    session: Session, external_id: str, values: dict[str, Any], source_record_id: uuid.UUID
) -> bool:
    record = session.scalar(select(Contract).where(Contract.source_key == external_id))
    inserted = record is None
    if record is None:
        record = Contract(
            id=uuid.uuid4(), source_key=external_id, source_record_id=source_record_id, **values
        )
        session.add(record)
    else:
        for key, value in values.items():
            setattr(record, key, value)
        record.source_record_id = source_record_id
    session.flush()
    index_entry(session, contract_entry(record))
    return inserted


SPEC = DatasetSpec(
    source_ref=SOURCE_REF,
    extraction_method="socrata-soda-api",
    allowed_fields=ALLOWED_FIELDS,
    external_id=lambda payload: clean(payload.get("id_contrato")),
    original_url=lambda payload: _url(payload.get("urlproceso")) or DATASET_URL,
    map_row=map_row,
    upsert=upsert,
)
