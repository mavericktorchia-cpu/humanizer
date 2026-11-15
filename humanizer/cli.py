"""Command-line interface: ``python -m humanizer`` or the ``humanize`` script."""
from __future__ import annotations

import argparse
import json
import sys

from . import MODES, analyze, humanize


def _print_report(label: str, rep, stream) -> None:
    print(f"{label}: score {rep.score}/100 | {rep.word_count} words, {rep.sentence_count} sentences, "
          f"mean length {rep.mean_sentence_len:.1f}, variation {rep.burstiness:.2f}", file=stream)
    for issue in rep.issues():
        print(f"  - {issue}", file=stream)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="humanize",
        description="Rewrite formulaic prose into natural academic writing.",
    )
    p.add_argument("input", nargs="?", default="-", help="input text file (default: stdin)")
    p.add_argument("-o", "--output", help="write result here instead of stdout")
    p.add_argument("-m", "--mode", choices=MODES, default="rules",
                   help="rules = offline; llm = Claude; both = Claude then rules (default: rules)")
    p.add_argument("--model", help="Claude model ID for llm/both modes")
    p.add_argument("--seed", type=int, default=0, help="seed for rule choices (default: 0)")
    p.add_argument("--analyze", action="store_true", help="only report on the input; do not rewrite")
    p.add_argument("--json", action="store_true", help="with --analyze, print the report as JSON")
    p.add_argument("--serve", action="store_true", help="start the local web interface")
    p.add_argument("--port", type=int, default=8000, help="port for --serve (default: 8000)")
    args = p.parse_args(argv)

    if args.serve:
        from .server import serve
        serve(args.port)
        return 0

    text = sys.stdin.read() if args.input == "-" else open(args.input, encoding="utf-8").read()
    before = analyze(text)
    if args.analyze:
        if args.json:
            print(json.dumps(before.to_dict(), indent=2))
        else:
            _print_report("Input", before, sys.stdout)
        return 0

    def progress(n: int, total: int) -> None:
        print(f"Rewriting section {n} of {total}...", file=sys.stderr)

    try:
        result = humanize(text, mode=args.mode, seed=args.seed, model=args.model, on_progress=progress)
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result)
    else:
        sys.stdout.write(result if result.endswith("\n") else result + "\n")
    _print_report("Before", before, sys.stderr)
    _print_report("After ", analyze(result), sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
