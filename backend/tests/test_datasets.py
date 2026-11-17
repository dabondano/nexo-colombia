from datetime import date

import pytest

from app.ingestion.datasets import bills, entities
from app.ingestion.pipeline import RowRejected
from tests.samples import bill_row, entity_row


def minimized(row: dict[str, object], allowed: frozenset[str]) -> dict[str, object]:
    return {k: v for k, v in row.items() if k in allowed}


def test_entity_allow_list_excludes_contact_and_personal_fields() -> None:
    excluded = {
        "direccion",
        "fax",
        "email",
        "ccb_telefono",
        "nombre_representante",
        "cargo_representante",
    }
    assert excluded.isdisjoint(entities.ALLOWED_FIELDS)
    assert excluded <= set(entity_row())


def test_entity_mapping() -> None:
    values = entities.map_row(minimized(entity_row(), entities.ALLOWED_FIELDS))
    assert values["name"] == "ALCALDÍA DE EJEMPLO - PRUEBA"
    assert values["name_normalized"] == "alcaldia de ejemplo - prueba"
    assert values["nit"] == "800123456"
    assert values["order"] == "TERRITORIAL"
    assert values["sector"] is None  # "NO APLICA" is a missing value, not a sector
    assert values["website"] == "http://www.ejemplo-prueba.gov.co"
    assert values["longitude"] == pytest.approx(-73.70375)
    assert values["data_quality_status"] == "acceptable"


def test_entity_without_nit_is_incomplete_and_bad_values_are_dropped() -> None:
    row = entity_row(
        ccb_nit_inst="No disponible en la fuente",
        ccb_pagina_web="no tiene pagina",
        longitud="0",
        latitud="123.4",
    )
    values = entities.map_row(minimized(row, entities.ALLOWED_FIELDS))
    assert values["nit"] is None
    assert values["website"] is None
    assert values["longitude"] is None
    assert values["latitude"] is None
    assert values["data_quality_status"] == "incomplete"


def test_entity_without_name_is_rejected() -> None:
    with pytest.raises(RowRejected):
        entities.map_row(minimized(entity_row(nombre="  "), entities.ALLOWED_FIELDS))


def test_bill_mapping() -> None:
    payload = minimized(bill_row(), bills.ALLOWED_FIELDS)
    assert "no_" not in payload  # the list position is not stored
    values = bills.map_row(payload)
    assert values["camara_number"] == "001/2026C"
    assert values["senado_number"] is None
    assert values["camara_filed_on"] == date(2026, 7, 20)
    assert values["senado_filed_on"] is None
    assert values["observations"] is None
    assert values["authors_text"] == "H.R. Autora De Ejemplo, H.R. Autor De Prueba"
    assert values["authors_normalized"] == "h.r. autora de ejemplo, h.r. autor de prueba"
    assert values["title_normalized"].endswith("sobre educacion rural")
    assert values["data_quality_status"] == "acceptable"
    assert bills.SPEC.external_id(payload) == "https://www.camara.gov.co/proyecto-de-ejemplo-1"


def test_bill_without_legislature_is_incomplete() -> None:
    values = bills.map_row(minimized(bill_row(legislatura="No Aplica"), bills.ALLOWED_FIELDS))
    assert values["legislature"] is None
    assert values["data_quality_status"] == "incomplete"


def test_placeholder_bill_rows_are_rejected() -> None:
    row = bill_row(t_tulo=".. FALLA EN EL APLICATIVO...")
    with pytest.raises(RowRejected, match="relleno"):
        bills.map_row(minimized(row, bills.ALLOWED_FIELDS))


def test_bill_link_must_be_a_web_address() -> None:
    payload = minimized(bill_row(link_del_proyecto={"url": "No Aplica"}), bills.ALLOWED_FIELDS)
    assert bills.SPEC.external_id(payload) is None


def test_interleaved_senate_number_is_recovered_only_when_unambiguous() -> None:
    def mapped(value: str) -> dict[str, object]:
        return bills.map_row(minimized(bill_row(no_senado=value), bills.ALLOWED_FIELDS))

    def senado_number(value: str) -> object:
        return mapped(value)["senado_number"]

    marker = "No Aplica"
    interleaved = marker + marker.join("068/2012 S") + marker
    assert senado_number(interleaved) == "068/2012 S"
    # The repair is declared, so it can be shown with the record.
    notes = mapped(interleaved)["processing_notes"]
    assert isinstance(notes, list) and len(notes) == 1 and "Senado" in notes[0]
    assert mapped("068/2012 S")["processing_notes"] == []
    # Not the exact defect pattern, or not a bill number: nothing is assumed.
    assert senado_number(f"{marker}06{marker}8/2012 S{marker}") is None
    assert senado_number(marker + marker.join("texto") + marker) is None
    assert senado_number(f"068/2012 S {marker}") is None
    assert senado_number("x" * 150) is None
