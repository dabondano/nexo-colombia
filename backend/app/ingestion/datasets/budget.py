"""Dataset: "Ejecución Presupuestal del Presupuesto General de la Nación"
(MinHacienda), datos.gov.co xjxk-qhsc.

Each row gives, for one national entity, one funding source, funds situation
(CSF/SSF) and budget resource: the current appropriation, commitments,
obligations and payments, in pesos. The dataset has no column for the fiscal
year or the cut-off date; NEXO does not assert either.

Checked on 2026-11-18 against all 600 rows: the four descriptive columns plus
the entity code identify a row; values are whole pesos, never negative, and
payments <= obligations <= commitments <= appropriation in every row. A row
breaking that order is published but marked "conflicting".
"""

import uuid
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.budget.models import BudgetExecution
from app.core.labels import DataQualityStatus
from app.ingestion.pipeline import DatasetSpec, Payload, RowRejected
from app.ingestion.text import clean, normalize_for_search

DATASET_ID = "xjxk-qhsc"
SOURCE_REF = f"datos.gov.co:{DATASET_ID}"
DATASET_URL = f"https://www.datos.gov.co/d/{DATASET_ID}"

AMOUNTS = {
    "apropiaci_n_vigente": "appropriation",
    "compromisos": "commitments",
    "obligaciones": "obligations",
    "pagos": "payments",
}
DESCRIPTIVE = (
    "codigo_entidad",
    "fuente_de_financiaci_n",
    "situacion_de_fondos",
    "recurso_presupuestal",
)
ALLOWED_FIELDS = frozenset(
    {*AMOUNTS, *DESCRIPTIVE, "codigo_del_sector", "nombre_del_sector", "nombre_entidad"}
)


def _external_id(payload: Payload) -> str | None:
    parts = [clean(payload.get(field)) for field in DESCRIPTIVE]
    if parts[0] is None:
        return None
    return "|".join(part or "" for part in parts)


def _amount(value: object, field: str) -> Decimal:
    text = clean(value)
    if text is None:
        raise RowRejected(f"Falta el valor de «{field}»")
    try:
        amount = Decimal(text)
    except InvalidOperation:
        raise RowRejected(f"El valor de «{field}» no es un número") from None
    if not amount.is_finite() or amount < 0:
        raise RowRejected(f"El valor de «{field}» es negativo o no es válido")
    return amount


def map_row(payload: Payload) -> dict[str, Any]:
    name = clean(payload.get("nombre_entidad"))
    if name is None:
        raise RowRejected("La fila no tiene nombre de entidad")
    amounts = {target: _amount(payload.get(field), field) for field, target in AMOUNTS.items()}
    ordered = (
        amounts["payments"]
        <= amounts["obligations"]
        <= amounts["commitments"]
        <= amounts["appropriation"]
    )
    return {
        "entity_code": clean(payload.get("codigo_entidad")),
        "entity_name": name,
        "entity_name_normalized": normalize_for_search(name),
        "sector_code": clean(payload.get("codigo_del_sector")),
        "sector_name": clean(payload.get("nombre_del_sector")),
        "funding_source": clean(payload.get("fuente_de_financiaci_n")),
        "funds_situation": clean(payload.get("situacion_de_fondos")),
        "budget_resource": clean(payload.get("recurso_presupuestal")),
        **amounts,
        # Documented criterion: the stages of execution cannot exceed the previous stage.
        "data_quality_status": (
            DataQualityStatus.ACCEPTABLE.value if ordered else DataQualityStatus.CONFLICTING.value
        ),
    }


def upsert(
    session: Session, external_id: str, values: dict[str, Any], source_record_id: uuid.UUID
) -> bool:
    record = session.scalar(
        select(BudgetExecution).where(BudgetExecution.source_key == external_id)
    )
    inserted = record is None
    if record is None:
        session.add(
            BudgetExecution(
                id=uuid.uuid4(), source_key=external_id, source_record_id=source_record_id, **values
            )
        )
    else:
        for key, value in values.items():
            setattr(record, key, value)
        record.source_record_id = source_record_id
    session.flush()
    return inserted


SPEC = DatasetSpec(
    source_ref=SOURCE_REF,
    extraction_method="socrata-soda-api",
    allowed_fields=ALLOWED_FIELDS,
    external_id=_external_id,
    original_url=lambda _payload: DATASET_URL,
    map_row=map_row,
    upsert=upsert,
)
