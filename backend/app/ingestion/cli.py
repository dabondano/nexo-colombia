"""Run a dataset synchronization.

Usage:  python -m app.ingestion.cli entities|bills|representatives|budget|constitution|all

`all` also rebuilds the links from bills to their authors (app/legislation/authors.py).
"""

import sys
from collections.abc import Callable, Iterable

from sqlalchemy.orm import Session

from app.core import audit
from app.core.db import get_engine
from app.ingestion.datasets import bills, budget, constitution, entities, representatives
from app.ingestion.pipeline import DatasetSpec, Row, run_sync
from app.ingestion.socrata import SocrataClient
from app.legislation.authors import link_authors
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
            session.commit()
            print(
                f"{name}: vistos={result.rows_seen} nuevos={result.rows_new} "
                f"modificados={result.rows_changed} sin_cambios={result.rows_unchanged} "
                f"rechazados={result.rows_rejected}"
            )
        if argv == ["all"]:
            links = link_authors(session)
            print(
                f"autores: proyectos={links.initiatives_considered} nombres={links.authors_seen} "
                f"vínculos={links.links} ambiguos={links.ambiguous}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
