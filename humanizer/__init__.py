"""Academic-register humanizer: analysis, offline rule rewrite, optional Claude rewrite."""
from __future__ import annotations

from .analyze import Report, analyze
from .rewrite import rule_rewrite

__all__ = ["Report", "analyze", "rule_rewrite", "humanize"]
__version__ = "0.1.0"

MODES = ("rules", "llm", "both")


def humanize(text: str, mode: str = "rules", seed: int | None = 0, model: str | None = None,
             on_progress=None) -> str:
    """Rewrite ``text``.

    mode="rules": offline rule engine only (no network, deterministic).
    mode="llm":   Claude rewrite only.
    mode="both":  Claude rewrite, then the rule engine as a final clean-up.
    """
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    if mode in ("llm", "both"):
        from .llm import DEFAULT_MODEL, llm_rewrite
        text = llm_rewrite(text, model=model or DEFAULT_MODEL, on_progress=on_progress)
    if mode in ("rules", "both"):
        text = rule_rewrite(text, seed=seed)
    return text
