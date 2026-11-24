"""Load invented sample records for the web interface tests.

Usage:  python -m tests.seed_ui   (against the database in NEXO_DATABASE_URL)

Every record is a "dato de ejemplo" from tests/samples.py and
tests/constitution_page.py; nothing is downloaded. The database is emptied
first, so never point this at a database with real data.
"""

import os
import sys
from datetime import date
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth.models import Role, UserAccount
from app.auth.security import hash_password
from app.budget.history import record_snapshots
from app.budget.links import index_budget_entities, link_budget_institutions
from app.budget.models import BudgetSnapshot
from app.core.db import CORE_SCHEMA, SEARCH_SCHEMA, get_engine
from app.ingestion.datasets import (
    bills,
    budget,
    constitution,
    contracts,
    entities,
    laws,
    representatives,
)
from app.ingestion.pipeline import run_sync
from app.law.statute_catalog import StatuteSpec
from app.legislation.authors import link_authors
from app.procurement.links import link_contract_institutions
from app.sources.registry import seed_registry
from tests import statute_page
from tests.constitution_page import page
from tests.samples import (
    bill_row,
    budget_row,
    company_contract,
    contract_row,
    entity_row,
    representative_row,
)

OPPOSITION_BASIS = "C.P. Art. 112 y Ley 1909 de 2018 Art. 24 (ejemplo)"

# Sample staff accounts for the interface tests; the passwords exist only here.
STAFF_PASSWORD = "clave-de-ejemplo-para-pruebas"  # noqa: S105 (sample data)
STAFF = [
    ("admin@nexo.example", "Administración de ejemplo", Role.ADMIN),
    ("datos@nexo.example", "Gestión de datos de ejemplo", Role.DATA_STEWARD),
    ("revision@nexo.example", "Revisión jurídica de ejemplo", Role.LEGAL_REVIEWER),
]


def seed(session: Session) -> None:
    session.execute(
        text(
            f"TRUNCATE {SEARCH_SCHEMA}.document, {CORE_SCHEMA}.relationship, "
            f"{CORE_SCHEMA}.content_review, {CORE_SCHEMA}.auth_session, {CORE_SCHEMA}.audit_event, "
            f"{CORE_SCHEMA}.budget_execution, {CORE_SCHEMA}.budget_snapshot, "
            f"{CORE_SCHEMA}.contract, {CORE_SCHEMA}.entity_mapping, "
            f"{CORE_SCHEMA}.user_account, "
            f"{CORE_SCHEMA}.position_holding, {CORE_SCHEMA}.person, "
            f"{CORE_SCHEMA}.provision_version, {CORE_SCHEMA}.legal_provision, "
            f"{CORE_SCHEMA}.legal_instrument, {CORE_SCHEMA}.institution, "
            f"{CORE_SCHEMA}.legislative_initiative, {CORE_SCHEMA}.sync_reject, "
            f"{CORE_SCHEMA}.source_record, {CORE_SCHEMA}.sync_run, {CORE_SCHEMA}.source CASCADE"
        )
    )
    session.commit()
    seed_registry(session)
    run_sync(
        session,
        entities.SPEC,
        [
            entity_row("9001"),
            entity_row(
                "9002",
                nombre="MINISTERIO DE EJEMPLO Y PROTECCIÓN SOCIAL",
                orden="NACIONAL",
                sector="SALUD Y PROTECCIÓN SOCIAL",
                departamento="BOGOTÁ D.C",
            ),
            # Same name as a budget entity: linked by rule A-014.
            # Also the contracting entity of the sample contracts (same NIT, A-016).
            entity_row("9003", nombre="Agencia de Ejemplo", ccb_nit_inst="900000001"),
            *(entity_row(str(9100 + n), nombre=f"ENTIDAD DE EJEMPLO {n:02d}") for n in range(30)),
        ],
    )
    run_sync(
        session,
        representatives.SPEC,
        [
            representative_row(),
            representative_row(
                "Autor De Prueba",
                "autor.prueba@camara.gov.co",
                apelidos_y_nombre="OPOSICIÓN",
                partido_o_movimiento=OPPOSITION_BASIS,
            ),
        ],
    )
    run_sync(
        session,
        bills.SPEC,
        [
            bill_row(
                "proyecto-de-ejemplo-1",
                autores="H.R. Autora De Ejemplo, H.R. Autor De Prueba, y otras firmas",
            ),
            # A placeholder row of the source system: rejected, so the panel lists a reject.
            bill_row("fila-de-relleno", t_tulo="FALLA EN EL APLICATIVO"),
            bill_row(
                "proyecto-de-ejemplo-2",
                no_c_mara="002/2026C",
                proyecto="Salud mental (ejemplo)",
                t_tulo="Por medio de la cual se dictan disposiciones de ejemplo sobre salud mental",
            ),
        ],
    )
    run_sync(session, constitution.SPEC, constitution.rows_from_html(page()))
    run_sync(
        session,
        budget.SPEC,
        [
            budget_row(),
            budget_row(recurso_presupuestal="DONACIONES", situacion_de_fondos="SSF"),
            budget_row(
                "98-01-00", nombre_entidad="MINISTERIO DE EJEMPLO", nombre_del_sector="OTRO SECTOR"
            ),
        ],
    )
    run_sync(
        session,
        contracts.SPEC,
        [
            contracts.minimize(row)
            for row in (
                contract_row(),
                company_contract(),
                contract_row(
                    "CO1.PCCNTR.1000003",
                    nombre_entidad="MINISTERIO DE EJEMPLO",
                    nit_entidad="900000002",
                    objeto_del_contrato="Servicio de vigilancia de ejemplo para la sede central",
                    tipo_de_contrato="Otro",
                    fecha_de_firma="2026-10-15T10:00:00.000",
                ),
            )
        ],
    )
    link_contract_institutions(session)
    # A sample law (invented text, not in the catalog): number 9999 of 2020.
    sample_law = StatuteSpec(1, "9999", 2020)
    run_sync(session, laws.SPEC, laws.rows_for(sample_law, statute_page.SAMPLE_LAW))
    link_authors(session)
    link_budget_institutions(session)
    index_budget_entities(session)
    record_snapshots(session)
    # An earlier source update, so the history table has a change to show.
    session.add(
        BudgetSnapshot(
            entity_code="99-01-00",
            entity_name="AGENCIA DE EJEMPLO",
            published_on=date(2026, 10, 7),
            appropriation=Decimal(2000000),
            commitments=Decimal(1200000),
            obligations=Decimal(700000),
            payments=Decimal(500000),
            line_count=2,
        )
    )
    for email, name, role in STAFF:
        session.add(
            UserAccount(
                email=email,
                display_name=name,
                role=role.value,
                password_hash=hash_password(STAFF_PASSWORD),
                must_change_password=False,
            )
        )
    session.commit()


if __name__ == "__main__":
    if (
        "nexo_ui" not in os.environ.get("NEXO_DATABASE_URL", "")
        and "nexo_test" not in os.environ.get("NEXO_DATABASE_URL", "")
        and "--force" not in sys.argv
    ):
        print("Refusing to seed: NEXO_DATABASE_URL does not name a test database (use --force).")
        raise SystemExit(2)
    with Session(get_engine()) as _session:
        seed(_session)
    print("Datos de ejemplo cargados.")
