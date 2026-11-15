# Academic Humanizer

Rewrites formulaic, machine-sounding prose into natural academic writing. The
register stays formal (no contractions, no slang), and citations, quotations,
numbers and meaning are left alone.

It has two engines:

| Mode | What it does | Needs |
|---|---|---|
| `rules` (default) | Offline rule engine: swaps stock phrases for plain academic wording, removes throat-clearing openers and stacked transitions, replaces dash asides, expands contractions, and joins or splits sentences at safe boundaries to vary rhythm. Deterministic for a given seed. | Nothing (Python standard library) |
| `llm` | Claude rewrites each section under strict constraints, then the built-in analyzer checks the result and asks for another pass if formulaic patterns remain. | `pip install anthropic` and an API key |
| `both` | `llm`, then `rules` as a final clean-up. Best quality. | Same as `llm` |

## Install

```bash
pip install -e .
```

For the Claude modes:

```bash
pip install -e ".[llm]"
```

```bash
export ANTHROPIC_API_KEY=your-key
```

## Use

Web interface (runs on your machine only):

```bash
humanize --serve
```

Then open http://127.0.0.1:8000.

Command line:

```bash
humanize essay.txt -o essay.out.txt
```

```bash
humanize essay.txt --mode both -o essay.out.txt
```

```bash
humanize essay.txt --analyze
```

`--seed N` gives a different set of word choices in rules mode. Without
installing, `python -m humanizer` works the same way from the repository root.

Python:

```python
from humanizer import analyze, humanize

report = analyze(text)          # report.score, report.issues()
better = humanize(text, mode="rules", seed=0)
```

## What the score means

`analyze` returns a 0-100 "formulaic" score built from surface features:
stock phrases, uniform sentence length, signpost transitions at the start of
sentences, dash asides, set constructions ("not only ... but also"), lists of
three, and repeated sentence openers.

It is this project's own heuristic. It is **not** a commercial AI detector,
it does not reproduce one, and a low score here does not guarantee any result
from GPTZero, Turnitin, Originality.ai or similar tools. Those detectors are
statistical, change without notice, and produce false positives and false
negatives on human and edited text alike. No rewriting tool can promise a
particular detector verdict.

## Limits

- The rule engine is conservative. It will not restructure arguments or fix
  constructions that need judgement; use `both` for that, and read the output.
- Protected spans are straight or curly double-quoted text, parenthetical
  citations containing a year, and bracketed numeric references. Other
  citation styles (footnote markers, single-quoted quotations) are not
  specifically protected.
- English only.
- Check your institution's or publisher's policy on AI assistance and
  disclose its use where required. The tool edits style; responsibility for
  the content and for how it is presented stays with the author.

## Tests

```bash
python -m unittest discover -s tests
```
