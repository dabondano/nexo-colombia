"""Reads the structure of a law from Función Pública's Gestor Normativo page.

Laws are printed like the Constitution (app/law/constitution.py) and the same
conventions apply to their wording: editor's notes are kept apart, wording
after the mark "TEXTO ANTERIOR" is never presented as wording in force, and
struck-through words keep their marks.

What differs is the structure, which varies from law to law:

- divisions are any of PARTE, LIBRO, TÍTULO, CAPÍTULO, SECCIÓN and SUBSECCIÓN,
  numbered with roman or arabic numerals or ordinal words, each followed by its
  name; some laws print the numeral without the word (Ley 80 de 1993:
  "I. DE LAS DISPOSICIONES GENERALES"), which is read as a chapter and declared;
- amending laws quote other laws' articles inside their own (Ley 1755 de 2015,
  article 1, quotes articles 13 to 33 of Ley 1437 de 2011, headings included).
  Article numbers of the law itself run 1, 2, 3...; a number out of that
  sequence starts quoted text, which belongs to the current article until the
  next number of the law appears;
- the page ends with the signatures and publication data, which are not loaded,
  nor is anything the page appends after them.

Whenever the page does not fit these rules the reader stops with a
StructureError instead of guessing.
"""

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date

from app.law.constitution import (
    _EDITORIAL_START,
    _LEADING_NOTE,
    _PREVIOUS_MARK,
    AFTER_PREVIOUS_MARK,
    ARTICLE,
    NOTE,
    TEXT,
    ParsedProvision,
    Segment,
    StructureError,
    _is_note,
    _key,
    roman_to_int,
)
from app.law.html_blocks import Block

PART = "parte"
BOOK = "libro"
TITLE = "titulo"
CHAPTER = "capitulo"
SECTION = "seccion"
SUBSECTION = "subseccion"
HEADING = "encabezado"
# Outer to inner. A heading printed without a label sits below the innermost division.
RANKS = {PART: 0, BOOK: 1, TITLE: 2, CHAPTER: 3, SECTION: 4, SUBSECTION: 5, HEADING: 6}
LABELS = {
    PART: "Parte",
    BOOK: "Libro",
    TITLE: "Título",
    CHAPTER: "Capítulo",
    SECTION: "Sección",
    SUBSECTION: "Subsección",
}
DIVISION_KINDS = tuple(RANKS)

_ORDINALS = {
    "primero": 1, "primera": 1, "segundo": 2, "segunda": 2, "tercero": 3, "tercera": 3,
    "cuarto": 4, "cuarta": 4, "quinto": 5, "quinta": 5, "sexto": 6, "sexta": 6,
    "septimo": 7, "septima": 7, "octavo": 8, "octava": 8, "noveno": 9, "novena": 9,
    "decimo": 10, "decima": 10, "unico": 1, "unica": 1,
}  # fmt: skip
# A roman numeral must stand alone: "CUARTO" is an ordinal word, not "C" + "UARTO".
_NUMERAL = r"(\d+|[IVXLC]+(?![A-Za-zÁÉÍÓÚáéíóú])|[A-Za-zÁÉÍÓÚáéíóú]+)\s?([A-Z](?![A-Za-z]))?"
_DIVISION = re.compile(
    r"^(PARTE|LIBRO|T[IÍ]TULO|CAP[IÍ]TULO|SECCI[OÓ]N|SUBSECCI[OÓ]N)\.?\s+"
    + _NUMERAL
    + r"[.:\-–]?\s*(.*)$",
    re.I,
)
_BARE_ROMAN = re.compile(r"^([IVXLC]+)\.?\s+(\S.*)$")
# "ARTÍOCULO 9" (sic, Ley 5 de 1992) is accepted too.
_ARTICLE = re.compile(
    r"^ART[IÍ]O?CULO\s+(TRANSITORIO\b\s*)?(\d+)?\s*(?:[oº°](?![a-z]))?"
    r"(?:\s?-?\s?([A-Z])(?=[.\s\-]))?\s*[.°º:\-–]*\s*",
    re.I,
)
# Where the law's own text ends: Congress's and the Government's signatures.
_END = re.compile(
    r"^(el presidente del honorable senado|el presidente de la honorable|"
    r"republica de colombia\s*-?\s*gobierno|publiquese|comuniquese|dada en|dado en)"
)
_ENACTING = re.compile(r"(^|\s)(decreta|resuelve):?$")
# Editor's lines printed without parentheses ("Sustituido por Art. 1, Ley 1755 de 2015.").
_LOOSE_NOTE = re.compile(
    r"^(ver\b|sustituid|modificad|adicionad|derogad|reglamentad|declarad|subrogad|corregid|"
    r"nota\b)",
    re.I,
)
_EDITOR_MARK = re.compile(r"^\*[^*]+\*$")


@dataclass
class ParsedStatute:
    heading: str
    # "Por la cual..." as the page prints it.
    summary: str | None
    provisions: list[ParsedProvision]
    article_count: int
    notes: list[str] = field(default_factory=list)
    # From the date line under the heading, "(Marzo 6)", with the law's year.
    issued_on: date | None = None
    # The page's note after the signatures, e.g. "Publicada en el Diario Oficial 49.084 ...".
    publication: str | None = None

    @property
    def instrument_type(self) -> str:
        """ "ley", "ley estatutaria" or "ley orgánica", as the heading says."""
        plain = _plain(self.heading)
        for kind in ("ley estatutaria", "ley organica"):
            if plain.startswith(kind):
                return "ley orgánica" if kind == "ley organica" else kind
        return "ley"


_MONTHS = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7,
    "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}  # fmt: skip
_DATE_LINE = re.compile(r"^\(?\s*([a-z]+)\s+(\d{1,2})\s*\)?\.?$")
_PUBLICATION = re.compile(r"diario oficial", re.I)


def _issued_on(text: str, year: int) -> date | None:
    match = _DATE_LINE.match(_plain(text).strip())
    if not match or match.group(1) not in _MONTHS:
        return None
    try:
        return date(year, _MONTHS[match.group(1)], int(match.group(2)))
    except ValueError:
        return None


def _plain(text: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFD", text) if unicodedata.category(ch) != "Mn"
    ).lower()


def _number(raw: str) -> int | None:
    if raw.isdigit():
        return int(raw)
    if re.fullmatch(r"[IVXLC]+", raw):
        return roman_to_int(raw)
    return _ORDINALS.get(_plain(raw))


def _shown(raw: str) -> str:
    """The numeral as shown: "IV", "2", or an ordinal word as "Primera"."""
    if raw.isdigit() or re.fullmatch(r"[IVXLC]+", raw):
        return raw
    return raw.capitalize()


def _division_kind(word: str) -> str:
    return _plain(word).rstrip(".")


@dataclass
class _Open:
    kind: str
    path: str
    provision: ParsedProvision
    has_articles: bool = False


class _Reader:
    def __init__(self) -> None:
        self.provisions: list[ParsedProvision] = []
        self.stack: list[_Open] = []
        self.current: ParsedProvision | None = None
        self.last_article = 0
        self.quoting = False
        self.after_mark = False
        self.awaiting_name: ParsedProvision | None = None
        self.repeated_name: str | None = None
        self.headings = 0
        self.transitory = 0
        self.leading_notes: list[str] = []
        # Since the last article of the law: where the provisions list stood, the
        # open divisions, and the blocks read, to undo divisions that turn out to
        # be quoted from another law.
        self.mark = 0
        self.stack_at_article: list[_Open] = []
        self.since_article: list[tuple[str, str]] = []

    def _add(self, provision: ParsedProvision) -> ParsedProvision:
        if any(p.path == provision.path for p in self.provisions):
            raise StructureError(f"Disposición repetida en la página: {provision.label}")
        provision.position = len(self.provisions) + 1
        self.provisions.append(provision)
        return provision

    # --- wording ---------------------------------------------------------

    def _segment(self, kind: str, text: str) -> None:
        target = self.current
        if target is None:
            if kind == NOTE and not self.stack:
                self.leading_notes.append(text)
                return
            if kind != NOTE:
                raise StructureError(f"Texto antes del primer artículo: {text[:80]!r}")
            target = self.stack[-1].provision
        target.segments.append(Segment(kind, text))

    def _wording(self, text: str) -> None:
        if _PREVIOUS_MARK.match(text):
            self.after_mark = True
        self._segment(AFTER_PREVIOUS_MARK if self.after_mark else TEXT, text)

    # --- divisions -------------------------------------------------------

    def _open_division(
        self, kind: str, number: str | None, name: str | None, repair: str | None
    ) -> None:
        rank = RANKS[kind]
        while self.stack and RANKS[self.stack[-1].kind] >= rank:
            self.stack.pop()
        parent = self.stack[-1].path if self.stack else None
        if kind == HEADING:
            self.headings += 1
            slug = f"{HEADING}-{self.headings}"
            label = name or "Encabezado"
        else:
            slug = f"{kind}-{(number or '').lower()}"
            label = f"{LABELS[kind]} {number}"
        path = f"{parent}/{slug}" if parent else slug
        previous = next((p for p in self.provisions if p.path == path), None)
        if previous is not None:
            # A law has one division of each number at each level: the page prints
            # this one again (Ley 1474 de 2011 repeats «CAPÍTULO I» after article 4).
            previous.repairs.append(
                f"La fuente vuelve a imprimir «{label}» más adelante; NEXO lo cuenta como "
                "la misma división."
            )
            self.stack.append(_Open(kind, path, previous))
            self.awaiting_name = None
            self.repeated_name = previous.heading
            self.current = None
            return
        provision = self._add(
            ParsedProvision(path, parent, kind, label, number, name if kind != HEADING else None)
        )
        if repair:
            provision.repairs.append(repair)
        self.stack.append(_Open(kind, path, provision))
        self.awaiting_name = provision if (name is None and kind != HEADING) else None
        self.current = None

    def _try_division(self, block: Block) -> bool:
        text = block.text.strip()
        match = _DIVISION.match(text)
        if match:
            kind = _division_kind(match.group(1))
            raw, letter, rest = match.group(2), match.group(3) or "", match.group(4).strip()
            value = _number(raw)
            if value is None:
                return False
            number = _shown(raw) + letter.upper()
            self._open_division(kind, number, rest or None, None)
            return True
        bare = _BARE_ROMAN.match(text)
        if block.bold and bare and text == text.upper():
            self._open_division(
                CHAPTER,
                bare.group(1),
                bare.group(2).strip(),
                f"La fuente imprime «{bare.group(1)}» sin la palabra «CAPÍTULO»; NEXO lo lee "
                "como un capítulo.",
            )
            return True
        return False

    # --- articles --------------------------------------------------------

    def _article(self, block: Block, match: re.Match[str]) -> bool:
        """Starts an article of this law; False when the label belongs to quoted text."""
        transitory, letter = match.group(1), (match.group(3) or "")
        if match.group(2) is None and not transitory:
            return False  # "ARTÍCULO" with no number: not a label
        digits = int(match.group(2)) if match.group(2) else 0
        if transitory:
            expected = True
            in_sequence = bool(digits) and digits == self.last_article + 1 and not letter
        elif letter:
            expected = digits == self.last_article
        else:
            expected = digits == self.last_article + 1
        if not expected:
            return False
        self.quoting = False
        if not transitory or in_sequence:
            self.last_article = digits
        number = f"{digits}{letter.upper()}" if digits else ""
        slug = re.sub(r"(\d+)([A-Z])", r"\1-\2", number).lower()
        if transitory and not digits:
            # Unnumbered transitory articles are told apart by their order.
            self.transitory += 1
            slug, label = f"transitorio-{self.transitory}", "Artículo transitorio"
        elif transitory:
            slug, label = f"transitorio-{slug}", f"Artículo transitorio {number}"
        else:
            label = f"Artículo {number}"
        parent = self.stack[-1].path if self.stack else None
        for opened in self.stack:
            opened.has_articles = True
        self.current = self._add(
            ParsedProvision(f"{ARTICLE}-{slug}", parent, ARTICLE, label, number or None, None)
        )
        self.mark = len(self.provisions)
        self.stack_at_article = list(self.stack)
        self.since_article = []
        self.awaiting_name = None
        self.repeated_name = None
        self.after_mark = False
        rest = block.text[match.end() :].strip()
        while rest:
            note = _LEADING_NOTE.match(rest)
            if not note or not _EDITORIAL_START.match(note.group(1).strip()):
                break
            self._segment(NOTE, f"({note.group(1)})")
            rest = rest[note.end() :].strip()
        if rest:
            self._wording(rest)
        return True

    # --- reading ---------------------------------------------------------

    def _undo_quoted_divisions(self) -> None:
        """Divisions opened since the last article were the quoted law's: give them back."""
        if self.last_article == 0 or self.mark == 0:
            raise StructureError("Artículo fuera de orden antes del primer artículo de la ley")
        del self.provisions[self.mark :]
        self.stack = list(self.stack_at_article)
        self.current = self.provisions[self.mark - 1]
        for kind, text in self.since_article:
            if kind == NOTE:
                self._segment(NOTE, text)
            else:
                self._wording(text)
        self.since_article = []
        self.awaiting_name = None

    def _body(self, block: Block) -> None:
        text = block.text.strip()
        if _EDITOR_MARK.match(text):
            return  # "*jurisprudencia*": an editor's marker, not part of the law
        article = _ARTICLE.match(text)
        if article and self._article(block, article):
            return
        if article:
            # A label out of this law's sequence: quoted text of another law.
            if self.current is None:
                self._undo_quoted_divisions()
            self.quoting = True
            self._wording(text)
            return
        is_note = _is_note(text) or (_LOOSE_NOTE.match(text) is not None and len(text) < 400)
        self.since_article.append((NOTE if is_note else TEXT, text))
        if is_note:
            self._segment(NOTE, text)
            return
        if self.quoting:
            self._wording(text)
            return
        if self._try_division(block):
            return
        if self.awaiting_name is not None and len(text) <= 300:
            # The division's name, usually bold (Ley 152 de 1994 prints it plain).
            self.awaiting_name.heading = text
            self.awaiting_name = None
            return
        if self.repeated_name is not None and _key(text) == _key(self.repeated_name):
            self.repeated_name = None
            return
        if self.current is None and (block.bold or len(text) <= 200):
            # Between a division and its first article only headings can stand.
            # A second unlabelled line under a division: shown as a heading of its own.
            self._open_division(HEADING, None, text, None)
            self.provisions[-1].repairs.append(
                "La fuente imprime este encabezado sin rótulo ni número; NEXO lo muestra tal "
                "cual, como un encabezado."
            )
            return
        if self.current is None:
            raise StructureError(f"Texto fuera de todo artículo: {text[:80]!r}")
        self._wording(text)

    def read(self, blocks: list[Block], number: str, year: int) -> ParsedStatute:
        heading_pattern = re.compile(rf"^(ley|decreto)\b.*\b0*{number}\s+de\s+{year}\b")
        heading = ""
        summary: str | None = None
        issued_on: date | None = None
        publication: str | None = None
        front_notes: list[str] = []
        phase = "front"
        for index, block in enumerate(blocks):
            text = block.text.strip()
            key = _key(text)
            if phase == "front":
                if not heading and heading_pattern.match(_plain(text)):
                    heading = text
                elif not heading:
                    raise StructureError(f"Inicio inesperado de la página: {text[:80]!r}")
                elif issued_on is None and _issued_on(text, year):
                    issued_on = _issued_on(text, year)
                elif _ENACTING.search(key):
                    phase = "body"
                elif summary is None and _plain(text).lstrip("\"“'").startswith("por "):
                    summary = text.strip("\"“”' ")
                elif _is_note(text) or key.startswith(("nota", "ver")):
                    front_notes.append(text)
                # Date line, "El Congreso de Colombia": not loaded.
            elif block.bold and _END.match(key):
                publication = next(
                    (
                        re.sub(r"^nota\s*:\s*", "", b.text.strip(), flags=re.I)
                        for b in blocks[index:]
                        if _PUBLICATION.search(b.text)
                    ),
                    None,
                )
                break
            else:
                self._body(block)
        if phase == "front":
            raise StructureError("La página no trae la fórmula «DECRETA» antes del articulado")
        if self.quoting:
            raise StructureError(
                f"Después del artículo {self.last_article} la página no vuelve a la numeración "
                "de la ley"
            )
        articles = sum(1 for p in self.provisions if p.kind == ARTICLE)
        if articles == 0:
            raise StructureError("La página no trae artículos")
        return ParsedStatute(
            heading,
            summary,
            self.provisions,
            articles,
            front_notes + self.leading_notes,
            issued_on,
            publication,
        )


def read_statute(blocks: list[Block], number: str, year: int) -> ParsedStatute:
    """Reads the page of law `number` of `year`; its first line must name that law."""
    return _Reader().read(blocks, number, year)
