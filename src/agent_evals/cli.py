"""Command-line entry point for agent-eval."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .graders import ALL_GRADERS
from .report import format_json, format_markdown, format_text, summarize
from .runner import run_suite
from .suite import SuiteError, load_suite

EXIT_OK = 0
EXIT_FAILURES = 1
EXIT_USAGE = 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-eval",
        description="Evaluate an AI automation behind an HTTP endpoint against a suite of cases.",
    )
    sub = parser.add_subparsers(dest="command")

    run = sub.add_parser("run", help="run a suite")
    run.add_argument("suite", help="path to a suite spec (.json, .yaml, .yml)")
    run.add_argument("--format", choices=("text", "json", "markdown"), default="text")
    run.add_argument("--no-llm", action="store_true", help="skip llm_judge graders (run offline)")
    run.add_argument("--no-color", action="store_true")
    run.add_argument("--output", help="write the report to a file instead of stdout")
    run.add_argument(
        "--min-pass-rate",
        type=float,
        default=1.0,
        help="fail (exit 1) if the pass rate is below this fraction (default: 1.0)",
    )

    sub.add_parser("list-graders", help="print every grader and exit")

    parser.add_argument("--version", action="version", version=f"agent-eval {__version__}")
    return parser


def list_graders() -> str:
    width = max(len(g.name) for g in ALL_GRADERS)
    lines = ["Available graders:", ""]
    for grader in ALL_GRADERS:
        tag = "  (needs API key)" if grader.needs_llm else ""
        lines.append(f"  {grader.name.ljust(width)}  {grader.summary}{tag}")
    return "\n".join(lines)


def _run(args) -> int:
    try:
        suite = load_suite(args.suite)
    except SuiteError as exc:
        print(f"suite error: {exc}", file=sys.stderr)
        return EXIT_USAGE

    results = run_suite(suite, skip_llm=args.no_llm)
    summary = summarize(results)

    color = sys.stdout.isatty() and not args.no_color and not args.output
    if args.format == "json":
        rendered = format_json(results, summary)
    elif args.format == "markdown":
        rendered = format_markdown(results, summary, suite.name)
    else:
        rendered = format_text(results, summary, color=color)

    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
        print(f"wrote {args.output}", file=sys.stderr)
    else:
        print(rendered)

    rate = summary["pass_rate"]
    if rate is None or rate < args.min_pass_rate:
        return EXIT_FAILURES
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "list-graders":
        print(list_graders())
        return EXIT_OK
    if args.command == "run":
        return _run(args)

    parser.print_help()
    return EXIT_USAGE


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
