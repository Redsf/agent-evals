"""Deterministic text graders: substrings, regex, length, citations."""

from __future__ import annotations

import re

from ..models import Case, GradeResult, Response
from .base import Grader

URL_PATTERN = re.compile(r"https?://\S+")


def _as_list(config: object) -> list[str]:
    if isinstance(config, str):
        return [config]
    if isinstance(config, list):
        return [str(item) for item in config]
    raise ValueError("expected a string or list of strings")


class ContainsAll(Grader):
    name = "contains_all"
    summary = "Response contains every one of the given substrings (case-insensitive)."

    def grade(self, response: Response, case: Case, config: object) -> GradeResult:
        needles = _as_list(config)
        text = response.text.lower()
        missing = [n for n in needles if n.lower() not in text]
        if missing:
            return self._ok(False, f"missing: {', '.join(missing)}")
        return self._ok(True, "all substrings present")


class ContainsAny(Grader):
    name = "contains_any"
    summary = "Response contains at least one of the given substrings."

    def grade(self, response: Response, case: Case, config: object) -> GradeResult:
        needles = _as_list(config)
        text = response.text.lower()
        if any(n.lower() in text for n in needles):
            return self._ok(True, "at least one substring present")
        return self._ok(False, f"none of: {', '.join(needles)}")


class NotContains(Grader):
    name = "not_contains"
    summary = "Response contains none of the given substrings (leak / forbidden-content check)."

    def grade(self, response: Response, case: Case, config: object) -> GradeResult:
        needles = _as_list(config)
        text = response.text.lower()
        present = [n for n in needles if n.lower() in text]
        if present:
            return self._ok(False, f"forbidden content present: {', '.join(present)}")
        return self._ok(True, "no forbidden content")


class RegexMatch(Grader):
    name = "regex_match"
    summary = "Response matches the given regular expression."

    def grade(self, response: Response, case: Case, config: object) -> GradeResult:
        pattern = re.compile(str(config))
        if pattern.search(response.text):
            return self._ok(True, "pattern matched")
        return self._ok(False, f"no match for /{config}/")


class HasCitation(Grader):
    name = "has_citation"
    summary = "Response includes a source URL (or must not, if config is false)."

    def grade(self, response: Response, case: Case, config: object) -> GradeResult:
        want = bool(config) if config is not None else True
        has = bool(URL_PATTERN.search(response.text))
        if has == want:
            return self._ok(True, "citation present" if want else "no citation, as required")
        return self._ok(False, "no source URL cited" if want else "unexpected URL in answer")


class MaxWords(Grader):
    name = "max_words"
    summary = "Response is within a word budget (brevity — matters for voice/TTS)."

    def grade(self, response: Response, case: Case, config: object) -> GradeResult:
        limit = int(config)
        words = len(response.text.split())
        if words <= limit:
            return self._ok(True, f"{words} words (<= {limit})")
        return self._ok(False, f"{words} words exceeds budget of {limit}")


class MinWords(Grader):
    name = "min_words"
    summary = "Response is at least this many words (catches empty / truncated replies)."

    def grade(self, response: Response, case: Case, config: object) -> GradeResult:
        floor = int(config)
        words = len(response.text.split())
        if words >= floor:
            return self._ok(True, f"{words} words (>= {floor})")
        return self._ok(False, f"only {words} words, below {floor}")
