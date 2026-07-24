"""Grader base class.

A grader inspects one Response for one Case and returns a GradeResult. Config
comes from the suite (the value after the grader name) and is grader-specific:
a bool, a string, a list, or a dict.
"""

from __future__ import annotations

from ..models import Case, GradeResult, Response


class Grader:
    name: str = ""
    summary: str = ""
    #: True if this grader needs network/API access (an LLM). Deterministic
    #: graders leave this False so a run can be filtered to offline-only.
    needs_llm: bool = False

    def grade(self, response: Response, case: Case, config: object) -> GradeResult:  # pragma: no cover
        raise NotImplementedError

    def _ok(self, passed: bool, reason: str) -> GradeResult:
        return GradeResult(grader=self.name, passed=passed, reason=reason)
