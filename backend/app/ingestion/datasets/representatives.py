"""Dataset: "Representantes período 2026-2027" (Cámara), datos.gov.co 5pt5-nxdp.

The source publishes its columns shifted by one position (checked on
2026-11-18 against all 362 rows):

    column in the source      what it holds
    "_"                       name of the representative
    "apelidos_y_nombre"       constituency (department, C.I.T.R.E.P, Oposición...)
    "partido_o_movimiento"    party, movement or organization; for the opposition
                              seat, the legal basis of the seat
    "circunscripcion"         institutional e-mail address
    "comision_const"          office
    "comision_legal"          phone and extension

NEXO maps the columns by what they hold and says so on every record. A row
that does not follow this layout is rejected, so a change at the source stops
the mapping instead of putting values in the wrong fields.

Each member is published in two rows; the second usually adds the office.
`order_rows` puts the most complete row of each member first, so it is the one
published; the other is listed among the run's rejects as a duplicate.
"""

import re
import uuid
from collections import defaultdict
from collections.abc import Iterable
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.congress.models import Person, PositionHolding
from app.core.labels import DataQualityStatus
from app.ingestion.pipeline import PROCESSING_NOTES, DatasetSpec, Payload, Row, RowRejected
from app.ingestion.text import clean, normalize_for_search, normalize_name
from app.search.indexing import index_entry, representative_entry

DATASET_ID = "5pt5-nxdp"
SOURCE_REF = f"datos.gov.co:{DATASET_ID}"
DATASET_URL = f"https://www.datos.gov.co/d/{DATASET_ID}"

POSITION = "Representante a la Cámara"
CORPORATION = "Cámara de Representantes"
PERIOD = "2026-2027"  # as the dataset names it

NAME = "_"
CONSTITUENCY = "apelidos_y_nombre"
PARTY = "partido_o_movimiento"
EMAIL = "circunscripcion"
OFFICE = "comision_const"
PHONE = "comision_legal"
ALLOWED_FIELDS = frozenset({NAME, CONSTITUENCY, PARTY, EMAIL, OFFICE, PHONE})

EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+\.[a-z]{2,}", re.IGNORECASE)
OPPOSITION = "oposicion"

SHIFT_NOTE = (
    "La fuente publica las columnas desplazadas una posición (por ejemplo, la columna "
    "«circunscripcion» trae el correo y la columna «apelidos_y_nombre» trae la "
    "circunscripción). NEXO asigna cada valor según su contenido; la fila tal como se "
    "publicó se conserva en el registro original."
)
OPPOSITION_NOTE = (
    "Para esta curul la fuente publica, en lugar de un partido, el fundamento jurídico "
    "de la curul de oposición. NEXO lo muestra como fundamento de la curul."
)


def _email(payload: Payload) -> str | None:
    text = clean(payload.get(EMAIL))
    return text.lower() if text and EMAIL_PATTERN.fullmatch(text) else None


def order_rows(rows: Iterable[Row]) -> list[Row]:
    """Put, for each member, the row with the most fields first; keep the rest after it."""
    groups: dict[str, list[Row]] = defaultdict(list)
    order: list[str] = []
    for index, row in enumerate(rows):
        key = _email({k: v for k, v in row.items() if k in ALLOWED_FIELDS}) or f"#{index}"
        if key not in groups:
            order.append(key)
        groups[key].append(row)
    result: list[Row] = []
    for key in order:
        members = groups[key]
        best = max(members, key=lambda row: sum(1 for k in ALLOWED_FIELDS if clean(row.get(k))))
        result.append(best)
        result.extend(row for row in members if row is not best)
    return result


def map_row(payload: Payload) -> dict[str, Any]:
    name = clean(payload.get(NAME))
    email = _email(payload)
    constituency = clean(payload.get(CONSTITUENCY))
    if name is None or email is None or constituency is None or "@" in constituency:
        raise RowRejected(
            "La fila no sigue la estructura de columnas conocida de esta fuente; "
            "hay que revisar el mapeo antes de cargarla"
        )

    notes = [SHIFT_NOTE]
    party = clean(payload.get(PARTY))
    seat_basis = None
    if normalize_for_search(constituency) == OPPOSITION:
        seat_basis, party = party, None
        notes.append(OPPOSITION_NOTE)

    return {
        "full_name": name,
        "position": POSITION,
        "corporation": CORPORATION,
        "period": PERIOD,
        "constituency": constituency,
        "party": party,
        "seat_basis": seat_basis,
        "email": email,
        "office": clean(payload.get(OFFICE)),
        "phone": clean(payload.get(PHONE)),
        "data_quality_status": (
            DataQualityStatus.ACCEPTABLE.value
            if party or seat_basis
            else DataQualityStatus.INCOMPLETE.value
        ),
        PROCESSING_NOTES: notes,
    }


def upsert(
    session: Session, external_id: str, values: dict[str, Any], source_record_id: uuid.UUID
) -> bool:
    full_name = values.pop("full_name")
    holding = session.scalar(
        select(PositionHolding).where(PositionHolding.source_key == external_id)
    )
    inserted = holding is None
    if holding is None:
        person = Person(full_name=full_name, name_normalized=normalize_name(full_name))
        session.add(person)
        session.flush()
        holding = PositionHolding(
            id=uuid.uuid4(),
            source_key=external_id,
            person_id=person.id,
            source_record_id=source_record_id,
            **values,
        )
        session.add(holding)
    else:
        person = session.get_one(Person, holding.person_id)
        person.full_name = full_name
        person.name_normalized = normalize_name(full_name)
        for key, value in values.items():
            setattr(holding, key, value)
        holding.source_record_id = source_record_id
    session.flush()
    index_entry(session, representative_entry(holding, person))
    return inserted


SPEC = DatasetSpec(
    source_ref=SOURCE_REF,
    extraction_method="socrata-soda-api",
    allowed_fields=ALLOWED_FIELDS,
    external_id=_email,
    original_url=lambda _payload: DATASET_URL,
    map_row=map_row,
    upsert=upsert,
)
