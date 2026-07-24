"""Run a suite: call the target for each case, apply its graders, collect results."""

from __future__ import annotations

from .graders import GRADERS_BY_NAME
from .models import CaseResult, GradeResult, Response, Suite
from .target import Transport, call, http_transport


def _grade_case(response: Response, case, skip_llm: bool) -> tuple[GradeResult, ...]:
    grades: list[GradeResult] = []
    for spec in case.graders:
        grader = GRADERS_BY_NAME[spec.name]
        if skip_llm and grader.needs_llm:
            grades.append(GradeResult(spec.name, True, "skipped (--no-llm)"))
            continue
        if response.error and grader.needs_llm:
            grades.append(GradeResult(spec.name, False, f"target error: {response.error}"))
            continue
        try:
            grades.append(grader.grade(response, case, spec.config))
        except Exception as exc:  # noqa: BLE001 - a grader error fails that check, not the run
            grades.append(GradeResult(spec.name, False, f"grader error: {exc}"))
    return tuple(grades)


def run_suite(
    suite: Suite,
    *,
    transport: Transport = http_transport,
    skip_llm: bool = False,
    on_case=None,
) -> list[CaseResult]:
    """Execute every case in the suite and return per-case results.

    `transport` is injectable so tests (and offline demos) can run without a
    live endpoint. `on_case` is an optional callback for progress reporting.
    """
    results: list[CaseResult] = []
    for case in suite.cases:
        response = call(suite.target, case.input, case.meta, transport=transport)
        grades = _grade_case(response, case, skip_llm)
        result = CaseResult(case_id=case.id, response=response, grades=grades)
        results.append(result)
        if on_case is not None:
            on_case(result)
    return results
