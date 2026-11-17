"""Sample rows for tests.

These are invented examples in the shape of the real datasets ("datos de
ejemplo"). They are never loaded outside the test database.
"""

from typing import Any

Row = dict[str, Any]


def entity_row(code: str = "9001", **overrides: Any) -> Row:
    row: Row = {
        ":id": f"row-{code}",
        ":updated_at": "2026-10-09T14:37:53.529Z",
        "dm_institucion_cod_institucion": code,
        "nombre": "ALCALDÍA DE EJEMPLO - PRUEBA",
        "ccb_nit_inst": "800123456",
        "orden": "TERRITORIAL",
        "suborden": "MUNICIPAL",
        "nivel_institucion": "CENTRAL",
        "clasificacion_organica": "RAMA EJECUTIVA",
        "sector": "NO APLICA",
        "naturaleza_juridica": "ALCALDÍA",
        "tipo_institucion": "ADSCRITAS",
        "municipio": "EJEMPLO",
        "departamento": "BOYACÁ",
        "ccb_pagina_web": "www.ejemplo-prueba.gov.co",
        "longitud": "-73.70375",
        "latitud": "3.536562",
        "estado_ins": "ACTIVA",
        # Fields that must never be stored (data minimization):
        "direccion": "Calle de ejemplo 1 # 2 - 3",
        "fax": "0000000",
        "email": "contacto@ejemplo-prueba.gov.co",
        "ccb_telefono": "3000000000",
        "nombre_representante": "PERSONA DE EJEMPLO",
        "cargo_representante": "Alcalde",
    }
    row.update(overrides)
    return row


def bill_row(slug: str = "proyecto-de-ejemplo-1", **overrides: Any) -> Row:
    row: Row = {
        ":id": f"row-{slug}",
        ":updated_at": "2026-09-17T17:09:26.503Z",
        "no_": "1",
        "no_c_mara": "001/2026C",
        "no_senado": "No aplica",
        "fecha_c_mara": "2026 Jul 20 12:00:00 AM",
        "fecha_senado": "No Aplica",
        "proyecto": "Educación rural (ejemplo)",
        "t_tulo": "Por medio de la cual se dictan disposiciones de ejemplo sobre educación rural",
        "objeto_del_proyecto": "Objeto de ejemplo.",
        "observaciones": "No Aplica",
        "tipo_de_ley": "Ley Ordinaria",
        "autores": "H.R. Autora De Ejemplo, H.R. Autor De Prueba",
        "estado_de_ley": "Trámite en Comisión",
        "origen_de_ley": "Cámara",
        "comisi_n_es_": "Comisión Sexta Constitucional Permanente",
        "legislatura": "2026-2027",
        "link_del_proyecto": {"url": f"https://www.camara.gov.co/{slug}"},
    }
    row.update(overrides)
    return row
