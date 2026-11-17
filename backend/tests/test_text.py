from datetime import date

import pytest

from app.ingestion.text import clean, normalize_for_search, parse_socrata_date


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, None),
        ("", None),
        ("  ", None),
        ("No Aplica", None),
        ("NO APLICA", None),
        ("No disponible en la fuente", None),
        ("  Ministerio   de  Salud ", "Ministerio de Salud"),
        (151, "151"),
    ],
)
def test_clean(value: object, expected: str | None) -> None:
    assert clean(value) == expected


def test_normalize_for_search_removes_accents_and_case() -> None:
    assert normalize_for_search("Bogotá D.C. – ÑANDÚ") == "bogota d.c. – nandu"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2026 Sep 11 12:00:00 AM", date(2026, 9, 11)),
        ("2024-07-20T00:00:00.000", date(2024, 7, 20)),
        ("2024-07-20", date(2024, 7, 20)),
        ("No Aplica", None),
        ("20 de julio", None),
        (None, None),
    ],
)
def test_parse_socrata_date(value: object, expected: date | None) -> None:
    assert parse_socrata_date(value) == expected
