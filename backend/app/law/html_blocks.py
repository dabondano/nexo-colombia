"""Turns the HTML of a published norm into a flat list of text blocks.

A block is one paragraph or list item, with the three facts about its
typography that the structure reader needs: whether it is centred, whether all
of it is in bold type, and whether part of it is struck through. Struck-through
words stay in the text between STRUCK_OPEN and STRUCK_CLOSE, so that they are
never mistaken for wording in force.
"""

import re
from dataclasses import dataclass
from html.parser import HTMLParser

_BLOCK_TAGS = frozenset({"p", "li", "h1", "h2", "h3", "h4", "h5", "h6"})
_BOLD_TAGS = frozenset({"strong", "b"})
_STRIKE_TAGS = frozenset({"s", "strike", "del"})
_SILENT_TAGS = frozenset({"script", "style", "button"})
_SPACE = re.compile(r"[ \t\r\n\xa0]+")

STRUCK_OPEN = "⟦"
STRUCK_CLOSE = "⟧"
_MARKS = re.compile(f"[{STRUCK_OPEN}{STRUCK_CLOSE} ]")


@dataclass(frozen=True)
class Block:
    text: str
    centered: bool = False
    bold: bool = False
    struck: bool = False


class _Reader(HTMLParser):
    def __init__(self, content_class: str, skip_class: str) -> None:
        super().__init__(convert_charrefs=True)
        self._content_class = content_class
        self._skip_class = skip_class
        self.blocks: list[Block] = []
        self._content_depth = 0  # open <div>s inside the content container
        self._skip_depth = 0  # open <div>s inside a skipped container
        self._silent: str | None = None
        self._bold = 0
        self._strike = 0
        self._parts: list[str] | None = None
        self._centered = False
        self._bold_chars = 0
        self._struck = False

    def _open_block(self, centered: bool) -> None:
        self._close_block()
        # A strike-through that began in an earlier block continues in this one.
        self._parts = [STRUCK_OPEN] if self._strike else []
        self._centered = centered
        self._bold_chars = 0
        self._struck = False

    def _close_block(self) -> None:
        if self._parts is None:
            return
        if self._strike:
            self._parts.append(STRUCK_CLOSE)
        text = _SPACE.sub(" ", "".join(self._parts)).strip()
        if text:
            visible = len(_MARKS.sub("", text))
            self.blocks.append(
                Block(
                    text=text,
                    centered=self._centered,
                    bold=self._bold_chars >= visible,
                    struck=self._struck,
                )
            )
        self._parts = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        classes = (attributes.get("class") or "").split()
        if self._content_depth == 0:
            if tag == "div" and self._content_class in classes:
                self._content_depth = 1
            return
        if self._skip_depth:
            if tag == "div":
                self._skip_depth += 1
            return
        if self._silent:
            return
        if tag == "div":
            if self._skip_class in classes:
                self._skip_depth = 1
            else:
                self._content_depth += 1
        elif tag in _SILENT_TAGS:
            self._silent = tag
        elif tag in _BLOCK_TAGS:
            self._open_block((attributes.get("align") or "").lower() == "center")
        elif tag == "br" and self._parts is not None:
            self._parts.append(" ")
        elif tag in _BOLD_TAGS:
            self._bold += 1
        elif tag in _STRIKE_TAGS:
            self._strike += 1
            if self._strike == 1 and self._parts is not None:
                self._parts.append(STRUCK_OPEN)

    def handle_endtag(self, tag: str) -> None:
        if self._content_depth == 0:
            return
        if self._skip_depth:
            if tag == "div":
                self._skip_depth -= 1
            return
        if self._silent:
            if tag == self._silent:
                self._silent = None
            return
        if tag == "div":
            self._content_depth -= 1
            if self._content_depth == 0:
                self._close_block()
        elif tag in _BLOCK_TAGS:
            self._close_block()
        elif tag in _BOLD_TAGS:
            self._bold = max(0, self._bold - 1)
        elif tag in _STRIKE_TAGS and self._strike:
            self._strike -= 1
            if self._strike == 0 and self._parts is not None:
                self._parts.append(STRUCK_CLOSE)

    def handle_data(self, data: str) -> None:
        if self._content_depth == 0 or self._skip_depth or self._silent:
            return
        if self._parts is None:
            if not data.strip():
                return
            self._open_block(centered=False)
        assert self._parts is not None  # noqa: S101 (narrowing for the type checker)
        self._parts.append(data)
        visible = len(_SPACE.sub("", data))
        if self._bold:
            self._bold_chars += visible
        if self._strike and visible:
            self._struck = True


def extract_blocks(html: str, *, content_class: str, skip_class: str) -> list[Block]:
    """Blocks inside the first `<div class="content_class">`, in reading order.

    Containers with `skip_class` (for example collapsed lists of case law) and
    scripts, styles and buttons are left out.
    """
    reader = _Reader(content_class, skip_class)
    reader.feed(html)
    reader.close()
    return reader.blocks


_STRUCK = re.compile(f"{STRUCK_OPEN}[^{STRUCK_CLOSE}]*{STRUCK_CLOSE}")


def without_struck(text: str) -> str:
    """The text without its struck-through words."""
    return _SPACE.sub(" ", _STRUCK.sub(" ", text)).strip()
