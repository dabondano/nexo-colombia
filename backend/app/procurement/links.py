"""Links each contract to the contracting entity in the institutions directory.

Usage:  python -m app.procurement.links   (also run after a contracts sync)

Rule (assumption A-016): SECOP II and Función Pública's directory both publish
the entity's NIT, an official tax identifier. A contract is linked when its
entity NIT, as digits, equals the NIT of exactly one directory entry. The
directory stores nine digits without the check digit; SECOP sometimes adds it,
so a tenth digit is dropped only when it is the correct DIAN check digit.
Bodies that share one legal person's NIT (several Defense units, for example)
cannot be told apart this way and stay unlinked. Measured on 2026-11-24: 352
of 841 entity names in scope linked, covering about 64,500 of 84,727 contracts.
"""

import re
import uuid
from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.catalog.models import Institution
from app.core.db import get_engine
from app.procurement.models import Contract

LINK_RULE = (
    "Entidad identificada por NEXO con el NIT: el NIT que publica SECOP II para el contrato es el "
    "mismo de una sola entidad del directorio de Función Pública. Si varias entidades comparten "
    "el NIT (por ejemplo, dependencias de un mismo ministerio), el contrato no se enlaza."
)
_WEIGHTS = (3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71)


def check_digit(nit: str) -> int:
    """DIAN verification digit of a NIT given as digits only."""
    total = sum(int(digit) * weight for digit, weight in zip(reversed(nit), _WEIGHTS, strict=False))
    remainder = total % 11
    return remainder if remainder < 2 else 11 - remainder


def nit_key(value: str | None) -> str | None:
    """The NIT without its check digit, or None when it cannot be read."""
    digits = re.sub(r"\D", "", value or "")
    if len(digits) == 10 and check_digit(digits[:9]) == int(digits[9]):
        return digits[:9]
    return digits or None


@dataclass(frozen=True)
class ContractLinkResult:
    entity_nits: int
    linked_nits: int
    ambiguous_nits: int
    linked_contracts: int


def link_contract_institutions(session: Session) -> ContractLinkResult:
    by_nit: dict[str, list[uuid.UUID]] = defaultdict(list)
    for institution_id, nit in session.execute(
        select(Institution.id, Institution.nit).where(Institution.nit.is_not(None))
    ):
        key = nit_key(nit)
        if key:
            by_nit[key].append(institution_id)

    session.execute(update(Contract).values(institution_id=None))
    nits = [nit for (nit,) in session.execute(select(Contract.entity_nit).distinct()) if nit]
    linked = ambiguous = contracts = 0
    for nit in nits:
        key = nit_key(nit)
        matches = by_nit.get(key, []) if key else []
        if len(matches) > 1:
            ambiguous += 1
        if len(matches) != 1:
            continue
        linked += 1
        result = session.execute(
            update(Contract).where(Contract.entity_nit == nit).values(institution_id=matches[0])
        )
        contracts += result.rowcount  # type: ignore[attr-defined]
    session.commit()
    return ContractLinkResult(
        entity_nits=len(nits),
        linked_nits=linked,
        ambiguous_nits=ambiguous,
        linked_contracts=contracts,
    )


if __name__ == "__main__":
    with Session(get_engine()) as _session:
        print(link_contract_institutions(_session))
