"""Initial source registry.

The datos.gov.co entries were checked against its API on the date in
VERIFIED_ON (dataset metadata, row count and sample rows); the others as noted
on each entry. Details and limitations are documented in
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
# Positions in the source hierarchy of the brief (section 11.1).
OFFICIAL_INSTITUTIONAL_RECORD = 2
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
            "de debates ni votaciones; en algunas filas el número de Senado llega con "
            "el texto «No Aplica» intercalado entre sus caracteres."
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

CONSTITUTION_REF = "funcionpublica.gov.co:gestor-normativo:4125"


def _constitution_source() -> Source:
    """Checked on 2026-11-17: page read in full, robots.txt allows every path."""
    return Source(
        external_ref=CONSTITUTION_REF,
        name="Gestor Normativo: Constitución Política de 1991",
        institution="Departamento Administrativo de la Función Pública",
        url="https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=4125",
        category="normas",
        acquisition_method=AcquisitionMethod.HTML.value,
        update_frequency="Permanente, según la fuente",
        reliability_class=OFFICIAL_INSTITUTIONAL_RECORD,
        licence=(
            "Texto normativo de reproducción permitida (Ley 23 de 1982, artículo 41). "
            "Condiciones de uso del sitio no verificadas."
        ),
        access_restrictions=None,
        known_limitations=(
            "Edición informativa: la fuente advierte que no responde por la vigencia de la "
            "norma. Mezcla texto vigente con texto anterior o tachado sin marcar siempre "
            "dónde termina. Omite los rótulos de la mayoría de los títulos y algunos "
            "encabezados: no imprime el Capítulo 3 del Título IV («Del estatuto de la "
            "oposición»), por lo que el artículo 112 aparece bajo el Capítulo 2, ni el "
            "nombre del Capítulo 4 del Título III («Del territorio»), según la edición "
            "del Senado de 2005. NEXO no incorpora las listas de concordancias «(Ver …)» "
            "ni, por ahora, las disposiciones transitorias."
        ),
        verification_status=VerificationStatus.VERIFIED.value,
        last_verified_at=datetime(2026, 11, 17, 12, 46, tzinfo=UTC),  # 07:46 in Bogotá
    )


def seed_registry(session: Session) -> int:
    """Insert registry entries that are not yet present. Returns how many were added."""
    added = 0
    if session.scalar(select(Source.id).where(Source.external_ref == CONSTITUTION_REF)) is None:
        session.add(_constitution_source())
        added += 1
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
