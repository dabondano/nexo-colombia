"""Run a dataset synchronization.  Usage:  python -m app.ingestion.cli entities|bills|all"""

import sys

from sqlalchemy.orm import Session

from app.core.db import get_engine
from app.ingestion.datasets import bills, entities
from app.ingestion.pipeline import DatasetSpec, run_sync
from app.ingestion.socrata import SocrataClient
from app.sources.registry import seed_registry

DATASETS: dict[str, tuple[str, DatasetSpec]] = {
    "entities": (entities.DATASET_ID, entities.SPEC),
    "bills": (bills.DATASET_ID, bills.SPEC),
}


def main(argv: list[str]) -> int:
    names = list(DATASETS) if argv == ["all"] else argv
    if not names or any(name not in DATASETS for name in names):
        print(__doc__)
        return 2
    client = SocrataClient()
    with Session(get_engine()) as session:
        seed_registry(session)
        for name in names:
            dataset_id, spec = DATASETS[name]
            result = run_sync(session, spec, client.iter_rows(dataset_id))
            print(
                f"{name}: vistos={result.rows_seen} nuevos={result.rows_new} "
                f"modificados={result.rows_changed} sin_cambios={result.rows_unchanged} "
                f"rechazados={result.rows_rejected}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
