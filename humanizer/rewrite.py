"""Deterministic, offline rewrite pass.

Conservative by design: it only makes edits that cannot change meaning
(phrase swaps, punctuation, joining or splitting at safe boundaries) and never
touches quotations or citations.
"""
from __future__ import annotations

import random
import re
import statistics

from .rules import LOWERABLE, OPENERS, REPLACEMENTS
from .textutil import is_heading, mask, split_paragraphs, split_sentences, unmask, words

_A_SOUND = re.compile(r"^(?:use|uni|one|eu)", re.I)
_COMPILED = [
    (re.compile(r"(?<![\w-])(?:(?P<art>an?)\s+)?(?P<body>" + pat + r")(?![\w-])" if not pat.endswith(r"\s+")
                else r"(?<![\w-])(?:(?P<art>an?)\s+)?(?P<body>" + pat + ")", re.I), alts)
    for pat, alts in REPLACEMENTS
]
_OPENER_RX = re.compile(
    r"^(" + "|".join(sorted(map(re.escape, OPENERS), key=len, reverse=True)) + r")\b,?\s+", re.I
)
_CONTRACTIONS = [
    (r"\bcan't\b", "cannot"), (r"\bwon't\b", "will not"), (r"\bshan't\b", "shall not"),
    (r"\b(\w+)n't\b", r"\1 not"), (r"\b(\w+)'re\b", r"\1 are"), (r"\b(\w+)'ve\b", r"\1 have"),
    (r"\b(\w+)'ll\b", r"\1 will"), (r"\bI'm\b", "I am"),
    (r"\b(it|that|there|what|here)'s\b", r"\1 is"), (r"\blet's\b", "let us"),
]


def _cap(s: str) -> str:
    for i, ch in enumerate(s):
        if ch == "\x00":
            return s
        if ch.isalpha():
            return s[:i] + ch.upper() + s[i + 1:]
    return s


def _lower_first(s: str) -> str:
    return s[:1].lower() + s[1:]


def _swap_phrases(text: str, rng: random.Random) -> str:
    for rx, alts in _COMPILED:
        def repl(m: re.Match, alts=alts) -> str:
            new = rng.choice(alts)
            body, art = m.group("body"), m.group("art")
            if not new and not art and body[0].isupper():
                return "\x01"  # phrase opened a sentence: capitalise what follows
            if new and body[0].isupper() and not art:
                new = _cap(new)
            if not art:
                return new
            if not new or re.match(r"(?:many|various|numerous|much|the|a|an)\b", new):
                # Replacement carries its own determiner (or none is needed).
                return _cap(new) if art[0].isupper() and new else new
            fixed = "a" if (new[0].lower() not in "aeiou" or _A_SOUND.match(new)) else "an"
            if art[0].isupper():
                fixed = fixed.capitalize()
            return f"{fixed} {new}"
        text = rx.sub(repl, text)
    return re.sub(r"\x01(\s*)(\w?)", lambda m: m.group(2).upper(), text)


def _fix_dashes(sentence: str) -> str:
    parts = re.split(r"\s?—\s?|\s--\s|\s–\s", sentence)
    if len(parts) == 1:
        return sentence
    if len(parts) == 3:  # paired aside
        return f"{parts[0]} ({parts[1]}){'' if parts[2][:1] in '.,;:!?' else ' '}{parts[2]}"
    out = parts[0]
    for nxt in parts[1:]:
        appositive = re.match(r"(?:an?|the|which|who|and|but|or)\b", nxt, re.I)
        out += (", " if appositive or len(words(nxt)) < 5 else ": ") + nxt
    return out


def _fix_opener(sentence: str, rng: random.Random, keep: bool) -> str:
    m = _OPENER_RX.match(sentence)
    if not m or keep:
        return sentence
    new = rng.choice(OPENERS[m.group(1).lower()])
    rest = sentence[m.end():]
    return f"{new} {rest}" if new else _cap(rest)


def _vary_rhythm(sents: list[str], rng: random.Random) -> list[str]:
    lengths = [len(words(s)) for s in sents]
    if len(sents) < 3:
        return sents
    mean = statistics.fmean(lengths)
    if mean and statistics.pstdev(lengths) / mean >= 0.5:
        return sents
    out: list[str] = []
    i = 0
    while i < len(sents):
        s, n = sents[i], lengths[i]
        nxt = sents[i + 1] if i + 1 < len(sents) else None
        first = nxt.split(" ", 1)[0] if nxt else ""
        if (nxt and n <= 12 and lengths[i + 1] <= 12 and s.endswith(".")
                and first in LOWERABLE and not first.endswith(",") and "," not in nxt[:14] and ";" not in s and ";" not in nxt and rng.random() < 0.7):
            out.append(s[:-1] + "; " + _lower_first(nxt))
            i += 2
            continue
        if n >= 28:
            m = re.search(r";\s+(?=\w)", s)
            if m and min(len(words(s[:m.start()])), len(words(s[m.end():]))) >= 6:
                out += [s[:m.start()] + ".", _cap(s[m.end():])]
                i += 1
                continue
            m = re.search(r",\s+but\s+(?!also\b)", s)
            if m and "not only" not in s[:m.start()].lower() \
                    and min(len(words(s[:m.start()])), len(words(s[m.end():]))) >= 8:
                out += [s[:m.start()] + ".", "Yet " + s[m.end():]]
                i += 1
                continue
        out.append(s)
        i += 1
    return out


def _tidy(text: str) -> str:
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r",\s*,", ",", text)
    return text


def rule_rewrite(text: str, seed: int | None = None) -> str:
    """Rewrite ``text`` with the offline rule engine. Same seed, same output."""
    rng = random.Random(seed)
    masked, spans = mask(text.replace("’", "'"))
    parts = split_paragraphs(masked)
    for idx in range(0, len(parts), 2):
        para = parts[idx]
        if not para.strip() or is_heading(para):
            continue
        lead = para[: len(para) - len(para.lstrip())]
        trail = para[len(para.rstrip()):]
        body = para.strip()
        for pat, sub in _CONTRACTIONS:
            body = re.sub(pat, sub, body, flags=re.I)
        sents = split_sentences(_swap_phrases(body, rng))
        fixed: list[str] = []
        kept_transition = False
        for s in sents:
            s = _fix_dashes(s)
            # Allow at most one signpost transition per paragraph to survive.
            had = bool(_OPENER_RX.match(s))
            keep = had and not kept_transition and rng.random() < 0.25
            s = _fix_opener(s, rng, keep)
            kept_transition = kept_transition or keep
            fixed.append(_cap(s))
        fixed = _vary_rhythm(fixed, rng)
        parts[idx] = lead + _tidy(" ".join(fixed)) + trail
    return unmask("".join(parts), spans)
