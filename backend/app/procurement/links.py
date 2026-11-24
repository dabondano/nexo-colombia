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

from sqlalchemy import func, or_, select, update
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


NIT_METHOD = "nit"
REVIEW_METHOD = "revision"


@dataclass(frozen=True)
class ContractLinkResult:
    entity_nits: int
    linked_nits: int
    ambiguous_nits: int
    linked_contracts: int
    reviewed_entities: int = 0


def link_contract_institutions(session: Session) -> ContractLinkResult:
    """Sets each contract's entity: a reviewed mapping first (A-017), else the NIT rule.

    Only rows whose link changes are written, so running it after every sync or
    after a single reviewed mapping is cheap.
    """
    # Imported here: app.catalog.mappings imports this module's nit_key.
    from app.catalog.mappings import EntityMapping, MappingKind, contract_key

    by_nit: dict[str, list[uuid.UUID]] = defaultdict(list)
    for institution_id, nit in session.execute(
        select(Institution.id, Institution.nit).where(Institution.nit.is_not(None))
    ):
        key = nit_key(nit)
        if key:
            by_nit[key].append(institution_id)
    reviewed = {
        mapping.source_value: mapping.institution_id
        for mapping in session.scalars(
            select(EntityMapping).where(EntityMapping.kind == MappingKind.CONTRACT_ENTITY.value)
        )
    }

    nits: set[str] = set()
    linked_nits: set[str] = set()
    ambiguous_nits: set[str] = set()
    reviewed_pairs = 0
    pairs = session.execute(select(Contract.entity_nit, Contract.entity_name).distinct()).all()
    for nit, name in pairs:
        key = nit_key(nit)
        if nit:
            nits.add(nit)
        target: uuid.UUID | None = None
        method: str | None = None
        mapped = reviewed.get(contract_key(nit, name))
        if mapped is not None:
            target, method = mapped, REVIEW_METHOD
            reviewed_pairs += 1
        else:
            matches = by_nit.get(key, []) if key else []
            if len(matches) == 1 and nit:
                target, method = matches[0], NIT_METHOD
                linked_nits.add(nit)
            elif len(matches) > 1 and nit:
                ambiguous_nits.add(nit)
        session.execute(
            update(Contract)
            .where(
                Contract.entity_nit.is_not_distinct_from(nit),
                Contract.entity_name == name,
                or_(
                    Contract.institution_id.is_distinct_from(target),
                    Contract.institution_link_method.is_distinct_from(method),
                ),
            )
            .values(institution_id=target, institution_link_method=method)
        )
    session.commit()
    linked_contracts = session.scalar(
        select(func.count()).where(Contract.institution_id.is_not(None))
    )
    return ContractLinkResult(
        entity_nits=len(nits),
        linked_nits=len(linked_nits),
        ambiguous_nits=len(ambiguous_nits),
        linked_contracts=linked_contracts or 0,
        reviewed_entities=reviewed_pairs,
    )


if __name__ == "__main__":
    with Session(get_engine()) as _session:
        print(link_contract_institutions(_session))
