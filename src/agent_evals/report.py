"""Summarize a run and render it as text, JSON, or Markdown."""

from __future__ import annotations

import json

from .models import CaseResult


def summarize(results: list[CaseResult]) -> dict:
    total = len(results)
    passed = sum(1 for r in results if r.passed)

    per_grader: dict[str, dict[str, int]] = {}
    for result in results:
        for grade in result.grades:
            bucket = per_grader.setdefault(grade.grader, {"pass": 0, "fail": 0})
            bucket["pass" if grade.passed else "fail"] += 1

    return {
        "total_cases": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": round(passed / total, 3) if total else None,
        "per_grader": per_grader,
    }


def format_text(results: list[CaseResult], summary: dict, *, color: bool) -> str:
    green, red, dim, bold, reset = (
        ("\033[32m", "\033[31m", "\033[2m", "\033[1m", "\033[0m") if color else ("",) * 5
    )

    lines: list[str] = []
    for result in results:
        mark = f"{green}PASS{reset}" if result.passed else f"{red}FAIL{reset}"
        lines.append(f"{mark}  {bold}{result.case_id}{reset}")
        if result.response.error:
            lines.append(f"        {red}target error:{reset} {result.response.error}")
        for grade in result.grades:
            if not grade.passed:
                lines.append(f"        {red}✗{reset} {grade.grader}: {grade.reason}")
        # Show a compact hint of what passed, dimmed.
        oks = [g.grader for g in result.grades if g.passed]
        if oks:
            lines.append(f"        {dim}✓ {', '.join(oks)}{reset}")

    rate = "n/a" if summary["pass_rate"] is None else f"{summary['pass_rate']:.0%}"
    lines.append("")
    lines.append(
        f"{bold}{summary['passed']}/{summary['total_cases']} cases passed ({rate}).{reset}"
    )
    return "\n".join(lines)


def format_markdown(results: list[CaseResult], summary: dict, suite_name: str) -> str:
    rate = "n/a" if summary["pass_rate"] is None else f"{summary['pass_rate']:.0%}"
    lines = [
        f"# Eval report — {suite_name}",
        "",
        f"- **Cases:** {summary['total_cases']}",
        f"- **Passed:** {summary['passed']} ({rate})",
        f"- **Failed:** {summary['failed']}",
        "",
        "## Per-grader",
        "",
        "| Grader | Pass | Fail |",
        "|---|---|---|",
    ]
    for grader, counts in summary["per_grader"].items():
        lines.append(f"| {grader} | {counts['pass']} | {counts['fail']} |")

    lines += ["", "## Cases", "", "| Case | Result | Failing checks |", "|---|---|---|"]
    for result in results:
        failing = "; ".join(
            f"{g.grader}: {g.reason}" for g in result.grades if not g.passed
        ) or "—"
        lines.append(f"| {result.case_id} | {'✅' if result.passed else '❌'} | {failing} |")
    return "\n".join(lines) + "\n"


def format_json(results: list[CaseResult], summary: dict) -> str:
    payload = {
        "summary": summary,
        "cases": [
            {
                "id": r.case_id,
                "passed": r.passed,
                "response": {"text": r.response.text, "status": r.response.status, "error": r.response.error},
                "grades": [
                    {"grader": g.grader, "passed": g.passed, "reason": g.reason}
                    for g in r.grades
                ],
            }
            for r in results
        ],
    }
    return json.dumps(payload, indent=2)
