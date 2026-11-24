"""Run a dataset synchronization.

Usage:  python -m app.ingestion.cli DATASET|all

DATASET: entities, bills, representatives, budget, constitution, laws or contracts.

`all` also rebuilds the links from bills to their authors (app/legislation/authors.py).
"""

import sys
from collections.abc import Callable, Iterable

from sqlalchemy.orm import Session

from app.budget.history import record_snapshots
from app.budget.links import index_budget_entities, link_budget_institutions
from app.core import audit
from app.core.db import get_engine
from app.ingestion.datasets import (
    bills,
    budget,
    constitution,
    contracts,
    entities,
    laws,
    representatives,
)
from app.ingestion.pipeline import DatasetSpec, Row, run_sync
from app.ingestion.socrata import SocrataClient
from app.legislation.authors import link_authors
from app.procurement.links import link_contract_institutions
from app.procurement.retention import prune_contracts
from app.sources.registry import seed_registry


def _socrata(dataset_id: str) -> Callable[[], Iterable[Row]]:
    return lambda: SocrataClient().iter_rows(dataset_id)


# Each dataset: its rules and the function that downloads its rows.
DATASETS: dict[str, tuple[DatasetSpec, Callable[[], Iterable[Row]]]] = {
    "entities": (entities.SPEC, _socrata(entities.DATASET_ID)),
    "bills": (bills.SPEC, _socrata(bills.DATASET_ID)),
    "representatives": (
        representatives.SPEC,
        lambda: representatives.order_rows(SocrataClient().iter_rows(representatives.DATASET_ID)),
    ),
    "budget": (budget.SPEC, _socrata(budget.DATASET_ID)),
    "constitution": (constitution.SPEC, constitution.fetch_rows),
    "laws": (laws.SPEC, laws.fetch_rows),
    "contracts": (
        contracts.SPEC,
        lambda: map(
            contracts.minimize,
            SocrataClient().iter_rows(
                contracts.DATASET_ID, where=contracts.where_clause(), fields=contracts.FIELDS
            ),
        ),
    ),
}


def main(argv: list[str]) -> int:
    names = list(DATASETS) if argv == ["all"] else argv
    if not names or any(name not in DATASETS for name in names):
        print(__doc__)
        return 2
    with Session(get_engine()) as session:
        seed_registry(session)
        for name in names:
            spec, download = DATASETS[name]
            result = run_sync(session, spec, download())
            audit.record(
                session,
                "sync_run",
                target_type="sync_run",
                target_id=str(result.sync_run_id),
                details={
                    "dataset": name,
                    "via": "command_line",
                    "seen": result.rows_seen,
                    "new": result.rows_new,
                    "changed": result.rows_changed,
                    "rejected": result.rows_rejected,
                },
            )
            snapshots = record_snapshots(session) if name == "budget" else None
            if name == "contracts":
                pruned = prune_contracts(session)
                print(
                    f"contratos: ventana desde {pruned.window_start}; "
                    f"retirados={pruned.contracts} copias_crudas={pruned.raw_records}"
                )
                contract_links = link_contract_institutions(session)
                print(
                    f"contratos: NIT={contract_links.entity_nits} "
                    f"enlazados={contract_links.linked_nits} "
                    f"compartidos={contract_links.ambiguous_nits} "
                    f"contratos_enlazados={contract_links.linked_contracts}"
                )
            session.commit()
            print(
                f"{name}: vistos={result.rows_seen} nuevos={result.rows_new} "
                f"modificados={result.rows_changed} sin_cambios={result.rows_unchanged} "
                f"rechazados={result.rows_rejected}"
                + (f" historial={snapshots}" if snapshots is not None else "")
            )
        if argv == ["all"]:
            links = link_authors(session)
            print(
                f"autores: proyectos={links.initiatives_considered} nombres={links.authors_seen} "
                f"vínculos={links.links} ambiguos={links.ambiguous}"
            )
            budget_links = link_budget_institutions(session)
            indexed = index_budget_entities(session)
            session.commit()
            print(
                f"presupuesto: entidades={budget_links.budget_entities} "
                f"enlazadas={budget_links.linked} indexadas={indexed}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
