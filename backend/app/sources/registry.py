"""Initial source registry: sources verified against the datos.gov.co API.

Each entry was checked on the date in VERIFIED_ON (dataset metadata, row count
and sample rows). Details and limitations are documented in
docs/04-source-registry.md. Run with:  python -m app.sources.registry
"""

from datetime import UTC, datetime
from typing import TypedDict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_engine
from app.core.labels import AcquisitionMethod, VerificationStatus
from app.sources.models import Source

VERIFIED_ON = datetime(2026, 11, 17, 5, 10, tzinfo=UTC)  # 00:10 in Bogotá
PORTAL = "https://www.datos.gov.co"
LICENCE = "CC BY-SA 4.0"
# Position in the source hierarchy of the brief (section 11.1): official databases.
OFFICIAL_DATABASE = 3


class RegistryEntry(TypedDict):
    dataset_id: str
    name: str
    institution: str
    category: str
    update_frequency: str | None
    access_restrictions: str | None
    known_limitations: str | None


REGISTRY: list[RegistryEntry] = [
    {
        "dataset_id": "h7zv-k39x",
        "name": "Universo de entidades",
        "institution": "Departamento Administrativo de la Función Pública",
        "category": "instituciones",
        "update_frequency": None,
        "access_restrictions": None,
        "known_limitations": None,
    },
    {
        "dataset_id": "kcxp-nxum",
        "name": "Proyectos de Ley",
        "institution": "Cámara de Representantes",
        "category": "legislación",
        "update_frequency": None,
        "access_restrictions": None,
        "known_limitations": (
            "Autores en texto libre; contiene filas de relleno; no incluye historial "
            "de debates ni votaciones."
        ),
    },
    {
        "dataset_id": "xjxk-qhsc",
        "name": "Ejecución Presupuestal del Presupuesto General de la Nación",
        "institution": "Ministerio de Hacienda y Crédito Público",
        "category": "recursos públicos",
        "update_frequency": None,
        "access_restrictions": None,
        "known_limitations": "Parece corresponder solo a la vigencia actual.",
    },
    {
        "dataset_id": "jbjy-vk9h",
        "name": "SECOP II - Contratos Electrónicos",
        "institution": "Agencia Nacional de Contratación Pública - Colombia Compra Eficiente",
        "category": "recursos públicos",
        "update_frequency": "Diaria",
        "access_restrictions": (
            "Contiene datos personales (documentos de identidad de personas naturales, "
            "datos bancarios). NEXO no incorpora esos campos."
        ),
        "known_limitations": (
            "Las entidades estatales son responsables de la veracidad de lo que publican."
        ),
    },
]


def seed_registry(session: Session) -> int:
    """Insert registry entries that are not yet present. Returns how many were added."""
    added = 0
    for entry in REGISTRY:
        external_ref = f"datos.gov.co:{entry['dataset_id']}"
        exists = session.scalar(select(Source.id).where(Source.external_ref == external_ref))
        if exists is not None:
            continue
        session.add(
            Source(
                external_ref=external_ref,
                name=entry["name"],
                institution=entry["institution"],
                url=f"{PORTAL}/d/{entry['dataset_id']}",
                category=entry["category"],
                acquisition_method=AcquisitionMethod.API.value,
                update_frequency=entry["update_frequency"],
                reliability_class=OFFICIAL_DATABASE,
                licence=LICENCE,
                access_restrictions=entry["access_restrictions"],
                known_limitations=entry["known_limitations"],
                verification_status=VerificationStatus.VERIFIED.value,
                last_verified_at=VERIFIED_ON,
            )
        )
        added += 1
    session.commit()
    return added


if __name__ == "__main__":
    with Session(get_engine()) as _session:
        print(f"Fuentes agregadas: {seed_registry(_session)}")
