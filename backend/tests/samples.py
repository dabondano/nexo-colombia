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


def representative_row(
    name: str = "Autora De Ejemplo",
    email: str = "autora.ejemplo@camara.gov.co",
    **overrides: Any,
) -> Row:
    """A row in the shifted layout of the real dataset: each column holds the next one's value."""
    row: Row = {
        ":id": f"row-{email}",
        ":updated_at": "2026-11-11T15:00:00.000Z",
        "_": name,
        "apelidos_y_nombre": "BOYACÁ",
        "partido_o_movimiento": "Partido De Ejemplo",
        "circunscripcion": email,
        "comision_const": "000B - Edificio de ejemplo",
    }
    row.update(overrides)
    return row


def budget_row(code: str = "99-01-00", **overrides: Any) -> Row:
    row: Row = {
        ":id": f"row-{code}-{overrides.get('recurso_presupuestal', 'RECURSOS CORRIENTES')}",
        ":updated_at": "2026-11-07T18:52:34.078Z",
        "fuente_de_financiaci_n": "Nación",
        "situacion_de_fondos": "CSF",
        "recurso_presupuestal": "RECURSOS CORRIENTES",
        "codigo_del_sector": "99",
        "nombre_del_sector": "SECTOR DE EJEMPLO",
        "codigo_entidad": code,
        "nombre_entidad": "AGENCIA DE EJEMPLO",
        "apropiaci_n_vigente": "1000000",
        "compromisos": "800000",
        # Not on the allow-list: never stored.
        "obligations_ignored": "x",
        "obligaciones": "500000",
        "pagos": "400000",
    }
    row.update(overrides)
    return row


def contract_row(contract_id: str = "CO1.PCCNTR.1000001", **overrides: Any) -> Row:
    row: Row = {
        ":id": f"row-{contract_id}",
        ":updated_at": "2026-11-23T10:53:49.534Z",
        "id_contrato": contract_id,
        "proceso_de_compra": "CO1.BDOS.2000001",
        "referencia_del_contrato": "001-2026",
        "nombre_entidad": "AGENCIA DE EJEMPLO",
        "nit_entidad": "900000001",
        "departamento": "Distrito Capital de Bogotá",
        "ciudad": "Bogotá",
        "orden": "Nacional",
        "sector": "Sector de ejemplo",
        "rama": "Ejecutivo",
        "estado_contrato": "En ejecución",
        "tipo_de_contrato": "Prestación de servicios",
        "modalidad_de_contratacion": "Contratación directa",
        "justificacion_modalidad_de": "Servicios profesionales y apoyo a la gestión",
        "objeto_del_contrato": "Prestar servicios profesionales de ejemplo en gestión documental",
        "fecha_de_firma": "2026-11-02T09:00:00.000",
        "fecha_de_inicio_del_contrato": "2026-11-03T00:00:00.000",
        "fecha_de_fin_del_contrato": "2026-12-31T00:00:00.000",
        "duraci_n_del_contrato": "58 Dia(s)",
        "dias_adicionados": "0",
        "tipodocproveedor": "Cédula de Ciudadanía",
        "proveedor_adjudicado": "PERSONA DE EJEMPLO",
        "documento_proveedor": "1000000001",
        "es_pyme": "No",
        "origen_de_los_recursos": "Distribuido",
        "destino_gasto": "Funcionamiento",
        "valor_del_contrato": "12000000",
        "valor_facturado": "4000000",
        "valor_pagado": "3000000",
        "valor_pendiente_de_pago": "1000000",
        "valor_pendiente_de_ejecucion": "8000000",
        "urlproceso": {"url": "https://community.secop.gov.co/Public/Tendering/ejemplo"},
        "ultima_actualizacion": "2026-11-20T12:00:00.000",
        # Never requested from the portal; listed to prove they are not stored.
        "n_mero_de_cuenta": "000-ejemplo",
        "nombre_supervisor": "SUPERVISORA DE EJEMPLO",
    }
    row.update(overrides)
    return row


def company_contract(contract_id: str = "CO1.PCCNTR.1000002", **overrides: Any) -> Row:
    return contract_row(
        contract_id,
        tipodocproveedor="NIT",
        proveedor_adjudicado="EMPRESA DE EJEMPLO S.A.S.",
        documento_proveedor="900000099",
        tipo_de_contrato="Compraventa",
        modalidad_de_contratacion="Mínima cuantía",
        objeto_del_contrato="Compra de elementos de aseo de ejemplo",
        **overrides,
    )
