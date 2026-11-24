"""Small, pure helpers for cleaning values that arrive from official datasets."""

import re
import unicodedata
from datetime import date, datetime

# Markers that sources use instead of leaving a value empty.
MISSING_MARKERS = frozenset(
    {"", "no aplica", "no disponible en la fuente", "n/a", "na", "null", "none", "sin información"}
)


def clean(value: object) -> str | None:
    """Return a trimmed string, or None when the source marks the value as missing."""
    if value is None:
        return None
    text = " ".join(str(value).split())
    if text.casefold() in MISSING_MARKERS:
        return None
    return text


def normalize_for_search(value: str) -> str:
    """Lower-case and strip accents, so 'Bogotá' and 'bogota' match."""
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def normalize_name(name: str) -> str:
    """Case, accents, punctuation and spacing removed: the form used to compare names."""
    text = re.sub(r"[^\w\s]", " ", normalize_for_search(name))
    return " ".join(text.split())


def parse_socrata_date(value: object) -> date | None:
    """Parse the date formats seen in datos.gov.co datasets; None if unparseable."""
    text = clean(value)
    if text is None:
        return None
    for fmt in ("%Y %b %d %I:%M:%S %p", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()  # noqa: DTZ007 (date only)
        except ValueError:
            continue
    return None
