"""Heuristic analysis of machine-sounding prose.

This is NOT an AI detector and does not reproduce any commercial detector's
model. It measures surface features that readers (and, loosely, detectors)
associate with generated text, so that a rewrite can be checked for progress.
"""
from __future__ import annotations

import re
import statistics
from dataclasses import dataclass, field

from .rules import FLAG_ONLY, OPENERS, REPLACEMENTS
from .textutil import is_heading, mask, split_paragraphs, split_sentences, words

_STOCK = [re.compile(r"\b(?:" + pat.strip().replace(r"\s+", "") + r")\b", re.I) for pat, _ in REPLACEMENTS]
_FLAG = [(re.compile(pat, re.I | re.S), label) for pat, label in FLAG_ONLY]
_OPENER = re.compile(
    r"^(?:" + "|".join(sorted(map(re.escape, OPENERS), key=len, reverse=True))
    + r"|however|therefore|thus|hence|nevertheless|nonetheless|similarly|conversely|likewise|accordingly|specifically)\b,?",
    re.I,
)
_TRICOLON = re.compile(r"\b[\w-]+(?: [\w-]+){0,3}, [\w-]+(?: [\w-]+){0,3},? and [\w-]+")
_DASH = re.compile(r"\s?[—–]\s?|\s--\s")
_CONTRACTION = re.compile(r"\b\w+(?:n't|'re|'ve|'ll|'d|'m)\b|\b(?:it|that|there|what|who|here|let)'s\b", re.I)


@dataclass
class Report:
    word_count: int = 0
    sentence_count: int = 0
    mean_sentence_len: float = 0.0
    burstiness: float = 0.0          # coefficient of variation of sentence length
    stock_phrases: list[str] = field(default_factory=list)
    constructions: list[str] = field(default_factory=list)
    em_dashes: int = 0
    transition_openers: int = 0
    repeated_openers: int = 0
    tricolons: int = 0
    contractions: int = 0            # academic-register check, not an AI signal
    components: dict[str, float] = field(default_factory=dict)
    score: int = 0                   # 0 (reads naturally) .. 100 (formulaic)

    def issues(self) -> list[str]:
        """Plain-language findings, most significant first."""
        out: list[tuple[float, str]] = []
        c = self.components
        if c.get("stock", 0) >= 3:
            uniq = sorted(set(p.lower() for p in self.stock_phrases))
            out.append((c["stock"], "Stock phrases: " + ", ".join(uniq[:12])))
        if c.get("rhythm", 0) >= 5:
            out.append((c["rhythm"], f"Sentence lengths are uniform (variation {self.burstiness:.2f}; aim above 0.50). Mix short sentences with long ones."))
        if c.get("openers", 0) >= 3:
            out.append((c["openers"], f"{self.transition_openers} of {self.sentence_count} sentences open with a signpost transition (Moreover, However, ...)."))
        if c.get("dashes", 0) >= 3:
            out.append((c["dashes"], f"{self.em_dashes} dash asides; use commas, parentheses or a new sentence."))
        if c.get("constructions", 0) >= 3:
            out.append((c["constructions"], "Formulaic constructions: " + ", ".join(sorted(set(self.constructions)))))
        if c.get("tricolons", 0) >= 3:
            out.append((c["tricolons"], f"{self.tricolons} lists of exactly three; vary the count."))
        if c.get("repeats", 0) >= 3:
            out.append((c["repeats"], f"{self.repeated_openers} consecutive sentences start with the same word."))
        if self.contractions:
            out.append((0.5, f"{self.contractions} contraction(s); expand them for an academic register."))
        return [msg for _, msg in sorted(out, key=lambda t: -t[0])]

    def to_dict(self) -> dict:
        d = {k: v for k, v in self.__dict__.items()}
        d["issues"] = self.issues()
        return d


def analyze(text: str) -> Report:
    masked, _ = mask(text)
    r = Report()
    sentences: list[str] = []
    for para in split_paragraphs(masked)[::2]:
        if not para.strip() or is_heading(para):
            continue
        sents = split_sentences(para)
        sentences.extend(sents)
        prev = None
        for s in sents:
            w = words(s)
            first = w[0].lower() if w else None
            if first and first == prev and first not in {"the", "a", "an"}:
                r.repeated_openers += 1
            elif first == prev and first == "the" and len(sents) > 3:
                r.repeated_openers += 0  # "The ... The ..." is ordinary
            prev = first
            if _OPENER.match(s):
                r.transition_openers += 1

    lengths = [len(words(s)) for s in sentences if words(s)]
    r.word_count = len(words(masked))
    r.sentence_count = len(lengths)
    if not lengths:
        return r
    r.mean_sentence_len = statistics.fmean(lengths)
    if len(lengths) >= 2 and r.mean_sentence_len:
        r.burstiness = statistics.pstdev(lengths) / r.mean_sentence_len

    for rx in _STOCK:
        r.stock_phrases.extend(m.group(0).strip() for m in rx.finditer(masked))
    for rx, label in _FLAG:
        r.constructions.extend(label for _ in rx.finditer(masked))
    r.em_dashes = len(_DASH.findall(masked))
    r.tricolons = len(_TRICOLON.findall(masked))
    r.contractions = len(_CONTRACTION.findall(masked.replace("’", "'")))

    per100 = 100.0 / max(r.word_count, 1)
    n = r.sentence_count
    c = r.components
    c["stock"] = min(35.0, len(r.stock_phrases) * per100 * 9)
    # Uniform rhythm only means something with enough sentences to judge.
    c["rhythm"] = 0.0 if n < 5 else min(25.0, max(0.0, (0.55 - r.burstiness) / 0.35) * 25)
    c["openers"] = min(15.0, max(0.0, r.transition_openers / n - 0.12) * 60)
    c["dashes"] = min(10.0, r.em_dashes * per100 * 8)
    c["constructions"] = min(10.0, len(r.constructions) * per100 * 12)
    c["tricolons"] = min(8.0, max(0.0, r.tricolons / n - 0.15) * 20)
    c["repeats"] = min(7.0, r.repeated_openers / n * 30)
    r.score = round(min(100.0, sum(c.values())))
    return r
