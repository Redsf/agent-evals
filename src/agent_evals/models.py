"""Core data structures for a suite, a run, and its results."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TargetSpec:
    """How to call the system under test and pull an answer out of its reply."""

    url: str
    method: str = "POST"
    headers: dict = field(default_factory=dict)
    # Request body template. Occurrences of {{input}} and {{field}} are replaced
    # per case before sending.
    body: dict | None = None
    # Where the answer text lives in the JSON response, as a dotted path
    # ("answer", "data.output", "$.result.text"). If unset, the whole response
    # text is used.
    extract: str | None = None
    timeout: int = 120


@dataclass(frozen=True)
class GraderSpec:
    """One grader invocation: a name plus its config."""

    name: str
    config: object  # dict, list, str, bool, or number — grader-specific


@dataclass(frozen=True)
class Case:
    id: str
    input: str
    graders: tuple[GraderSpec, ...]
    # Free-form fields a case may carry (expected values, canaries, notes).
    meta: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Suite:
    name: str
    target: TargetSpec
    cases: tuple[Case, ...]


@dataclass(frozen=True)
class Response:
    """The system-under-test's reply to one case."""

    text: str
    json: object | None
    status: int | None
    error: str | None = None


@dataclass(frozen=True)
class GradeResult:
    grader: str
    passed: bool
    reason: str


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    response: Response
    grades: tuple[GradeResult, ...]

    @property
    def passed(self) -> bool:
        return bool(self.grades) and all(g.passed for g in self.grades)
