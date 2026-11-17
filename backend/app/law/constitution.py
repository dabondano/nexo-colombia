"""Reads the structure of the Constitution from Función Pública's published page.

The page (Gestor Normativo, norm 4125) prints the Constitution as a run of
paragraphs. This module turns them into a preamble, titles, chapters and
articles, and keeps apart three things the page mixes with the wording:

- editor's notes (cross-references, which reform changed an article);
- wording printed after the mark "TEXTO ANTERIOR". The page does not say where
  earlier wording ends, so everything after the mark in that article is kept
  as "after the mark" and never presented as wording in force;
- struck-through words, kept between the marks of `app.law.html_blocks`.

The page leaves out the labels "TÍTULO I" to "TÍTULO XI" and "CAPÍTULO 1". The
numbers are deduced from the order of the headings and declared as repairs.
Whenever the headings do not fit the expected pattern the reader stops with a
StructureError instead of guessing.

Only the permanent text is read. The transitory provisions restart their
numbering several times on the page and are left for a later milestone.
"""

import re
from dataclasses import dataclass, field

from app.ingestion.text import normalize_for_search
from app.law.html_blocks import Block

PREAMBLE = "preambulo"
TITLE = "titulo"
CHAPTER = "capitulo"
ARTICLE = "articulo"

TEXT = "text"
NOTE = "note"
AFTER_PREVIOUS_MARK = "after_previous_mark"

EXPECTED_TITLES = 13
MAX_HEADING_LENGTH = 200

_ARTICLE = re.compile(r"^ART[IÍ]CULO\s+(\d+)(?:\s?-?\s?([A-Z])(?=[.\s]))?\s*[.°º]*\s*", re.I)
_TITLE_LABEL = re.compile(r"^T[IÍ]TULO\s+([IVXLC]+)\.?$", re.I)
_CHAPTER_LABEL = re.compile(r"^CAP[IÍ]TULO\s+(\d+|[IVXLC]+)\s?([A-Z])?\.?$", re.I)
_PREVIOUS_MARK = re.compile(r"^TEXTO\s+ANTERIOR", re.I)
_NOT_A_HEADING = re.compile(r"^(PAR[AÁ]GRAFO|TEXTO|ART[IÍ]CULO|NOTA|\d)", re.I)
_LEADING_NOTE = re.compile(r"^\(([^()]{3,})\)[.,;]?\s*")
_EDITORIAL_START = re.compile(
    r"^(ver|modificad|adicionad|derogad|art[ií]culo|inciso|numeral|par[aá]grafo|literal|"
    r"aparte|expresi|declarad|corregid|reglamentad|sustitu|encabezado|cap[ií]tulo|nota)",
    re.I,
)
_REFORM = re.compile(r"Acto\s+Legislativo\s+0?(\d+)\s+de\s+(\d{4})", re.I)
_ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}
_ROMAN_NUMERALS = (
    (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
)  # fmt: skip


class StructureError(ValueError):
    """The page no longer has the structure this reader was written for."""


@dataclass(frozen=True)
class Segment:
    kind: str
    text: str


@dataclass
class ParsedProvision:
    path: str
    parent_path: str | None
    kind: str
    label: str
    number: str | None
    heading: str | None
    position: int = 0
    segments: list[Segment] = field(default_factory=list)
    # Repairs NEXO made to what the page prints, in plain Spanish.
    repairs: list[str] = field(default_factory=list)


@dataclass
class ParsedInstrument:
    title: str
    provisions: list[ParsedProvision]
    # The most recent constitutional reform the page mentions, e.g. (2025, 1).
    latest_reform: tuple[int, int] | None
    transitory_omitted: bool


def roman_to_int(value: str) -> int:
    total = 0
    digits = [_ROMAN[ch] for ch in value.upper()]
    for index, digit in enumerate(digits):
        smaller = index + 1 < len(digits) and digit < digits[index + 1]
        total += -digit if smaller else digit
    return total


def int_to_roman(value: int) -> str:
    result = ""
    for amount, numeral in _ROMAN_NUMERALS:
        while value >= amount:
            result += numeral
            value -= amount
    return result


def _key(text: str) -> str:
    return normalize_for_search(text).strip(' .,"')


def _is_note(text: str) -> bool:
    """Whole paragraphs in parentheses are the editor's, as are "(Ver ..." lists."""
    if text.startswith("(") and (
        text.rstrip(" .;,").endswith(")") or _key(text[1:]).startswith("ver")
    ):
        return True
    return _key(text).startswith("ver la constitucion")


def _is_heading(block: Block) -> bool:
    text = block.text
    return (
        block.bold
        and len(text) <= MAX_HEADING_LENGTH
        and text == text.upper()
        and any(ch.isalpha() for ch in text)
        and not _NOT_A_HEADING.match(text)
    )


class _Reader:
    def __init__(self) -> None:
        self.title = ""
        self.provisions: list[ParsedProvision] = []
        self.latest_reform: tuple[int, int] | None = None
        self._title_number = 0
        self._title_path: str | None = None
        self._chapters_in_title: list[str] = []
        self._division_path: str | None = None
        self._current: ParsedProvision | None = None
        self._after_mark = False
        self._pending: list[Block] = []
        self._pending_is_note = False

    # --- building blocks -------------------------------------------------

    def _add(self, provision: ParsedProvision) -> ParsedProvision:
        if any(p.path == provision.path for p in self.provisions):
            raise StructureError(f"Disposición repetida en la página: {provision.label}")
        provision.position = len(self.provisions) + 1
        self.provisions.append(provision)
        return provision

    def _note_reforms(self, text: str) -> None:
        for number, year in _REFORM.findall(text):
            reform = (int(year), int(number))
            if self.latest_reform is None or reform > self.latest_reform:
                self.latest_reform = reform

    def _segment(self, kind: str, text: str) -> None:
        if self._current is None:
            raise StructureError(f"Texto fuera de toda disposición: {text[:80]!r}")
        self._current.segments.append(Segment(kind, text))
        if kind == NOTE:
            self._note_reforms(text)

    def _wording(self, text: str) -> None:
        if _PREVIOUS_MARK.match(text):
            self._after_mark = True
        self._segment(AFTER_PREVIOUS_MARK if self._after_mark else TEXT, text)

    # --- divisions -------------------------------------------------------

    def _open_title(self, number: int, heading: str | None, *, deduced: bool) -> None:
        if number != self._title_number + 1:
            raise StructureError(
                f"Se esperaba el Título {int_to_roman(self._title_number + 1)} "
                f"y la página trae el Título {int_to_roman(number)}"
            )
        self._title_number = number
        roman = int_to_roman(number)
        provision = self._add(
            ParsedProvision(f"{TITLE}-{number}", None, TITLE, f"Título {roman}", roman, heading)
        )
        if deduced:
            provision.repairs.append(
                f"La fuente no imprime el rótulo «TÍTULO {roman}»; NEXO dedujo el número "
                "por el orden de los títulos."
            )
        self._title_path = self._division_path = provision.path
        self._chapters_in_title = []

    def _open_chapter(self, number: str | None, heading: str | None) -> None:
        if self._title_path is None:
            raise StructureError("Capítulo antes del primer título")
        whole = len({re.sub(r"\D", "", n) for n in self._chapters_in_title})
        deduced = number is None
        if number is None:
            number = str(whole + 1)
        digits = int(re.sub(r"\D", "", number))
        lettered = not number.isdigit()
        if digits != (whole if lettered else whole + 1) or number in self._chapters_in_title:
            raise StructureError(
                f"Capítulo {number} fuera de orden en el Título {int_to_roman(self._title_number)}"
            )
        self._chapters_in_title.append(number)
        slug = re.sub(r"(\d+)([A-Z])", r"\1-\2", number).lower()
        provision = self._add(
            ParsedProvision(
                f"{self._title_path}/{CHAPTER}-{slug}",
                self._title_path,
                CHAPTER,
                f"Capítulo {number}",
                number,
                heading,
            )
        )
        if deduced:
            provision.repairs.append(
                f"La fuente no imprime el rótulo «CAPÍTULO {number}»; NEXO dedujo el número "
                "por su posición dentro del título."
            )
        self._division_path = provision.path

    def _open_divisions(self) -> None:
        """Interpret the headings gathered since the last article."""
        blocks, self._pending, self._pending_is_note = self._pending, [], False
        notes: list[str] = []
        headings: list[str] = []
        for index, block in enumerate(blocks):
            if _key(block.text) == "nota aclaratoria":
                notes.append(" ".join(b.text for b in blocks[index:]))
                break
            if _is_note(block.text):
                notes.append(block.text)
            else:
                headings.append(block.text.strip())
        if not headings:
            # Only notes: they belong to the article that precedes them.
            for note in notes:
                self._segment(NOTE, note)
            return

        opened_from = len(self.provisions)
        rest = list(headings)
        first = rest[0]
        title_label = _TITLE_LABEL.match(first)
        chapter_label = _CHAPTER_LABEL.match(first)
        lone_name = len(rest) == 1 and not title_label and not chapter_label
        if title_label:
            rest.pop(0)
            name = rest.pop(0) if rest and not _CHAPTER_LABEL.match(rest[0]) else None
            self._open_title(roman_to_int(title_label.group(1)), name, deduced=False)
        elif not chapter_label and not (lone_name and self._chapters_in_title):
            self._open_title(self._title_number + 1, rest.pop(0), deduced=True)
        if rest:
            chapter_label = _CHAPTER_LABEL.match(rest[0])
            if chapter_label:
                rest.pop(0)
                raw, letter = chapter_label.group(1), chapter_label.group(2) or ""
                number = str(roman_to_int(raw)) if not raw.isdigit() else raw
                self._open_chapter(number + letter.upper(), rest.pop(0) if rest else None)
            else:
                self._open_chapter(None, rest.pop(0))
        if rest:
            raise StructureError(f"Encabezados que no se pudieron interpretar: {rest}")
        for note in notes:
            self.provisions[opened_from].segments.append(Segment(NOTE, note))
            self._note_reforms(note)

    # --- reading ---------------------------------------------------------

    def _start_article(self, block: Block, match: re.Match[str]) -> None:
        if self._pending:
            self._open_divisions()
        if self._division_path is None:
            raise StructureError("Artículo antes del primer título")
        number = match.group(1) + (match.group(2) or "").upper()
        slug = re.sub(r"(\d+)([A-Z])", r"\1-\2", number).lower()
        self._current = self._add(
            ParsedProvision(
                f"{ARTICLE}-{slug}",
                self._division_path,
                ARTICLE,
                f"Artículo {number}",
                number,
                None,
            )
        )
        self._after_mark = False
        rest = block.text[match.end() :].strip()
        while rest:
            note = _LEADING_NOTE.match(rest)
            if not note or not _EDITORIAL_START.match(note.group(1).strip()):
                break
            self._segment(NOTE, f"({note.group(1)})")
            rest = rest[note.end() :].strip()
        if rest:
            self._wording(rest)

    def _body(self, block: Block) -> None:
        article = _ARTICLE.match(block.text)
        if article:
            self._start_article(block, article)
        elif self._pending_is_note:
            self._pending.append(block)
        elif self._pending and _key(block.text) == "nota aclaratoria":
            # An editor's clarification about the headings: it runs to the next article.
            self._pending.append(block)
            self._pending_is_note = True
        elif _is_heading(block):
            self._pending.append(block)
        elif _is_note(block.text):
            if self._pending:
                self._pending.append(block)
            else:
                self._segment(NOTE, block.text)
        else:
            # Bold capitals inside an article (not a division): give them back.
            for held in self._pending:
                self._wording(held.text)
            self._pending = []
            self._wording(block.text)

    def read(self, blocks: list[Block]) -> ParsedInstrument:
        phase = "front"
        transitory_omitted = False
        for block in blocks:
            key = _key(block.text)
            if phase == "front":
                if key == PREAMBLE:
                    self._current = self._add(
                        ParsedProvision(PREAMBLE, None, PREAMBLE, "Preámbulo", None, None)
                    )
                    phase = "preamble"
                elif key.startswith("constitucion politica") and not self.title:
                    self.title = block.text
                else:
                    raise StructureError(f"Inicio inesperado de la página: {block.text[:80]!r}")
            elif phase == "preamble":
                if _is_note(block.text):
                    self._segment(NOTE, block.text)
                else:
                    self._segment(TEXT, block.text)
                    if key == "constitucion politica de colombia":
                        phase = "body"
            elif block.bold and key == "disposiciones transitorias":
                transitory_omitted = True
                break
            else:
                self._body(block)
        if self._pending and not transitory_omitted:
            raise StructureError("La página termina con encabezados sin artículos")
        if self._title_number != EXPECTED_TITLES:
            raise StructureError(
                f"Se esperaban {EXPECTED_TITLES} títulos y la página trae {self._title_number}"
            )
        return ParsedInstrument(self.title, self.provisions, self.latest_reform, transitory_omitted)


def read_constitution(blocks: list[Block]) -> ParsedInstrument:
    return _Reader().read(blocks)
