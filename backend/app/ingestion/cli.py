"""Run a dataset synchronization.

Usage:  python -m app.ingestion.cli entities|bills|constitution|all
"""

import sys
from collections.abc import Callable, Iterable

from sqlalchemy.orm import Session

from app.core.db import get_engine
from app.ingestion.datasets import bills, constitution, entities
from app.ingestion.pipeline import DatasetSpec, Row, run_sync
from app.ingestion.socrata import SocrataClient
from app.sources.registry import seed_registry


def _socrata(dataset_id: str) -> Callable[[], Iterable[Row]]:
    return lambda: SocrataClient().iter_rows(dataset_id)


# Each dataset: its rules and the function that downloads its rows.
DATASETS: dict[str, tuple[DatasetSpec, Callable[[], Iterable[Row]]]] = {
    "entities": (entities.SPEC, _socrata(entities.DATASET_ID)),
    "bills": (bills.SPEC, _socrata(bills.DATASET_ID)),
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
            print(
                f"{name}: vistos={result.rows_seen} nuevos={result.rows_new} "
                f"modificados={result.rows_changed} sin_cambios={result.rows_unchanged} "
                f"rechazados={result.rows_rejected}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
