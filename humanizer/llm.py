"""Model-backed rewrite pass using the Claude API.

Requires ``pip install anthropic`` and credentials in the environment
(``ANTHROPIC_API_KEY``, or an ``ant auth login`` profile).
"""
from __future__ import annotations

from .analyze import analyze
from .textutil import split_paragraphs, words

DEFAULT_MODEL = "claude-opus-5-5"
CHUNK_WORDS = 1200

SYSTEM_PROMPT = """\
You are revising a passage of academic writing the way a careful human editor \
in the author's field would. The draft reads as formulaic, and the goal is \
prose that a specialist reader would take for the work of a practised \
academic writer.

What must not change:
- Every claim, finding, number, date, name, technical term and hedge. Do not \
add facts, examples, sources or opinions, and do not drop any.
- Citations and references, exactly as written, e.g. (Smith et al., 2020) or [12].
- Direct quotations, word for word.
- The paragraph structure: return the same number of paragraphs in the same \
order, with headings left untouched.
- The register: formal academic English. No contractions, no colloquialisms, \
no rhetorical questions, no addressing the reader, and no first person unless \
the draft already uses it. Keep the draft's spelling convention (British or \
American).

What should change:
- Rhythm. Formulaic prose keeps every sentence near the same length and \
shape. Let length follow content: a short declarative sentence where a point \
is simple, a long subordinated one where the reasoning needs it. Vary how \
sentences open, and do not begin consecutive sentences with the same word.
- Wording. Prefer the plain, specific word a subject expert would use over \
an impressive general one. Remove inflated vocabulary (delve, pivotal, \
crucial, multifaceted, tapestry, landscape, realm, robust, leverage, foster, \
underscore, showcase, testament, comprehensive, nuanced, seamless) wherever \
a plainer word carries the same meaning.
- Connectives. Most sentences need no signpost. Drop openers such as \
Moreover, Furthermore, Additionally, Notably, Importantly, and let the logic \
of the sentences carry the link. Keep a connective only where the relation \
would otherwise be unclear.
- Constructions. Rework "not only X but also Y", "it is important to note \
that", "plays a ... role in", "highlights the importance of", and sentences \
that end by restating what was just said. Do not default to lists of exactly \
three. Use no em dashes; use commas, parentheses, a colon or a new sentence.
- Paragraph endings. Cut closing sentences that only summarise or moralise.

Reply with the revised passage only: no preface, no notes, no markdown \
formatting that the draft did not have."""


class RefusedError(RuntimeError):
    pass


def _chunks(text: str) -> list[str]:
    """Group whole paragraphs into chunks of roughly CHUNK_WORDS words."""
    parts = split_paragraphs(text)
    chunks: list[str] = []
    cur, count = "", 0
    for i in range(0, len(parts), 2):
        para = parts[i] + (parts[i + 1] if i + 1 < len(parts) else "")
        n = len(words(para))
        if cur and count + n > CHUNK_WORDS:
            chunks.append(cur)
            cur, count = "", 0
        cur += para
        count += n
    if cur:
        chunks.append(cur)
    return chunks


def _call(client, model: str, messages: list[dict]) -> str:
    # Streaming avoids HTTP timeouts on long passages. The server-side fallback
    # re-runs the request on another model if a safety classifier declines it.
    with client.beta.messages.stream(
        model=model,
        max_tokens=64000,
        system=SYSTEM_PROMPT,
        output_config={"effort": "high"},
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        messages=messages,
    ) as stream:
        msg = stream.get_final_message()
    if msg.stop_reason == "refusal":
        raise RefusedError("The model declined to rewrite this passage.")
    if msg.stop_reason == "max_tokens":
        raise RuntimeError("Output was cut off at the token limit; try a shorter passage.")
    return "".join(b.text for b in msg.content if b.type == "text").strip()


def llm_rewrite(text: str, model: str = DEFAULT_MODEL, rounds: int = 2, on_progress=None) -> str:
    """Rewrite ``text`` with Claude, re-checking each chunk against the analyzer.

    ``rounds`` is the maximum number of revision passes per chunk after the
    first rewrite; a pass runs only if the analyzer still finds problems.
    """
    try:
        import anthropic
    except ImportError as e:  # pragma: no cover
        raise RuntimeError("LLM mode needs the Anthropic SDK: pip install anthropic") from e

    client = anthropic.Anthropic()
    chunks = _chunks(text)
    out: list[str] = []
    try:
        for n, chunk in enumerate(chunks, 1):
            if on_progress:
                on_progress(n, len(chunks))
            body = chunk.strip()
            if not body:
                out.append(chunk)
                continue
            trail = chunk[len(chunk.rstrip()):]
            messages = [{"role": "user", "content": f"<draft>\n{body}\n</draft>"}]
            best = _call(client, model, messages)
            best_score = analyze(best).score
            for _ in range(rounds):
                issues = analyze(best).issues()
                if best_score <= 12 or not issues:
                    break
                messages += [
                    {"role": "assistant", "content": best},
                    {"role": "user", "content":
                        "A style check on your revision still finds the following. Revise again to "
                        "resolve them, keeping every other constraint, and reply with the passage only.\n- "
                        + "\n- ".join(issues)},
                ]
                cand = _call(client, model, messages)
                cand_score = analyze(cand).score
                if cand_score >= best_score:
                    break
                best, best_score = cand, cand_score
            out.append(best + trail)
    except TypeError as e:
        if "authentication" not in str(e).lower():
            raise
        raise RuntimeError(
            "No Claude API credentials found. Set the ANTHROPIC_API_KEY environment variable "
            "before starting, or use the offline 'rules' mode.") from e
    except anthropic.AuthenticationError as e:
        raise RuntimeError("Claude API credentials are missing or invalid. Set ANTHROPIC_API_KEY.") from e
    except anthropic.RateLimitError as e:
        raise RuntimeError("Rate limited by the Claude API; wait a moment and retry.") from e
    except anthropic.APIStatusError as e:
        raise RuntimeError(f"Claude API error ({e.status_code}): {e.message}") from e
    except anthropic.APIConnectionError as e:
        raise RuntimeError("Could not reach the Claude API; check the network connection.") from e
    return "".join(out)
