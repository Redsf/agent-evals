"""Graders for structured (JSON) responses — for extraction and classification endpoints."""

from __future__ import annotations

from ..extract import extract_path
from ..models import Case, GradeResult, Response
from .base import Grader

_MISSING = object()


def _normalize(value: object) -> object:
    """Compare numbers and numeric strings by value, other things by lowercased text."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip()
        try:
            return float(stripped.replace(",", ""))
        except ValueError:
            return stripped.lower()
    return value


class JsonField(Grader):
    name = "json_field"
    summary = "A field in the JSON response equals an expected value (dotted path)."

    def grade(self, response: Response, case: Case, config: object) -> GradeResult:
        if not isinstance(config, dict) or "path" not in config:
            raise ValueError("json_field needs {path: ..., equals: ...}")
        if response.json is None:
            return self._ok(False, "response was not JSON")

        actual = extract_path(response.json, config["path"])
        if "equals" in config:
            expected = config["equals"]
            if _normalize(actual) == _normalize(expected):
                return self._ok(True, f"{config['path']} == {expected!r}")
            return self._ok(False, f"{config['path']} is {actual!r}, expected {expected!r}")

        # No expected value given: just assert the field exists and is non-null.
        present = actual is not None
        return self._ok(present, f"{config['path']} {'present' if present else 'missing/null'}")


class JsonHasKeys(Grader):
    name = "json_has_keys"
    summary = "The JSON response contains all the required top-level keys."

    def grade(self, response: Response, case: Case, config: object) -> GradeResult:
        if not isinstance(response.json, dict):
            return self._ok(False, "response is not a JSON object")
        required = config if isinstance(config, list) else [config]
        missing = [k for k in required if k not in response.json]
        if missing:
            return self._ok(False, f"missing keys: {', '.join(map(str, missing))}")
        return self._ok(True, "all required keys present")


class NoNullFields(Grader):
    name = "no_null_fields"
    summary = "Named JSON fields must be non-null (catches silent extraction misses)."

    def grade(self, response: Response, case: Case, config: object) -> GradeResult:
        if not isinstance(response.json, dict):
            return self._ok(False, "response is not a JSON object")
        fields = config if isinstance(config, list) else [config]
        nulls = [f for f in fields if extract_path(response.json, str(f)) is None]
        if nulls:
            return self._ok(False, f"null/absent: {', '.join(map(str, nulls))}")
        return self._ok(True, "no null fields")
