"""Shared text helpers: masking protected spans, sentence and paragraph splitting."""
from __future__ import annotations

import re

# Spans the rewriter must never alter: direct quotations, parenthetical
# citations such as (Smith et al., 2020, p. 4), and bracketed references [12].
_PROTECTED = re.compile(
    r"""
    "[^"\n]{1,400}"                      # straight double quotes
    | “[^”\n]{1,400}”      # curly double quotes
    | \([^()\n]*\b(?:1[5-9]|20)\d\d[a-z]?\b[^()\n]*\)   # (Author, 2020)
    | \[[\d,;\s–-]+\]               # [1], [2, 3], [4-6]
    """,
    re.VERBOSE,
)
_TOKEN = re.compile(r"\x00(\d+)\x00")

_ABBREV = (
    "e.g.", "i.e.", "et al.", "etc.", "cf.", "vs.", "Fig.", "fig.", "Eq.", "eq.",
    "Dr.", "Prof.", "Mr.", "Mrs.", "Ms.", "No.", "no.", "vol.", "Vol.", "pp.",
    "p.", "ca.", "approx.", "St.", "U.S.", "U.K.", "Ph.D.",
)
_SENT_BOUNDARY = re.compile(r"(?<=[.!?])[\"”')\]]?\s+(?=[A-Z\x00\"“(\[])")
_WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9'’-]*")


def mask(text: str) -> tuple[str, list[str]]:
    """Replace protected spans with opaque tokens. Returns (masked, spans)."""
    spans: list[str] = []

    def repl(m: re.Match) -> str:
        spans.append(m.group(0))
        return f"\x00{len(spans) - 1}\x00"

    return _PROTECTED.sub(repl, text), spans


def unmask(text: str, spans: list[str]) -> str:
    return _TOKEN.sub(lambda m: spans[int(m.group(1))], text)


def words(text: str) -> list[str]:
    return _WORD.findall(_TOKEN.sub(" ", text))


def split_paragraphs(text: str) -> list[str]:
    """Split on blank lines, keeping the separators as odd-indexed items."""
    return re.split(r"(\n\s*\n)", text)


def split_sentences(paragraph: str) -> list[str]:
    parts: list[str] = []
    start = 0
    for m in _SENT_BOUNDARY.finditer(paragraph):
        head = paragraph[start:m.start()]
        if head.endswith(_ABBREV) or re.search(r"\b[A-Z]\.$", head):
            continue  # abbreviation or initial, not a sentence end
        parts.append(head.strip())
        start = m.end()
    tail = paragraph[start:].strip()
    if tail:
        parts.append(tail)
    return parts


def is_heading(paragraph: str) -> bool:
    p = paragraph.strip()
    return bool(p) and "\n" not in p and len(words(p)) <= 12 and p[-1] not in ".!?:;"
