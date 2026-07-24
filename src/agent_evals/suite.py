"""Load and validate a suite spec from JSON or YAML.

JSON needs no dependencies. YAML is supported when PyYAML is installed
(`pip install agent-evals[yaml]`) — nicer for hand-writing multi-line prompts,
but never required.
"""

from __future__ import annotations

import json
from pathlib import Path

from .graders import GRADERS_BY_NAME
from .models import Case, GraderSpec, Suite, TargetSpec


class SuiteError(ValueError):
    """A suite spec is malformed or references an unknown grader."""


def _load_raw(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix in (".yaml", ".yml"):
        try:
            import yaml  # type: ignore
        except ImportError as exc:  # pragma: no cover - depends on install extras
            raise SuiteError(
                f"{path} is YAML but PyYAML is not installed — "
                f"`pip install agent-evals[yaml]` or use a JSON suite"
            ) from exc
        data = yaml.safe_load(text)
    else:
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise SuiteError(f"{path}: invalid JSON — {exc}") from exc

    if not isinstance(data, dict):
        raise SuiteError(f"{path}: top level must be an object")
    return data


def _parse_target(raw: object, where: str) -> TargetSpec:
    if not isinstance(raw, dict) or "url" not in raw:
        raise SuiteError(f"{where}: 'target' must be an object with a 'url'")
    return TargetSpec(
        url=str(raw["url"]),
        method=str(raw.get("method", "POST")).upper(),
        headers=dict(raw.get("headers", {})),
        body=raw.get("body"),
        extract=raw.get("extract"),
        timeout=int(raw.get("timeout", 120)),
    )


def _parse_graders(raw: object, case_id: str) -> tuple[GraderSpec, ...]:
    if not isinstance(raw, list) or not raw:
        raise SuiteError(f"case {case_id!r}: 'grade' must be a non-empty list")
    specs: list[GraderSpec] = []
    for entry in raw:
        if not isinstance(entry, dict) or len(entry) != 1:
            raise SuiteError(
                f"case {case_id!r}: each grade entry must be a single {{name: config}} mapping"
            )
        (name, config), = entry.items()
        if name not in GRADERS_BY_NAME:
            raise SuiteError(f"case {case_id!r}: unknown grader {name!r}")
        specs.append(GraderSpec(name=name, config=config))
    return tuple(specs)


def _parse_case(raw: object, index: int) -> Case:
    if not isinstance(raw, dict):
        raise SuiteError(f"case #{index}: must be an object")
    case_id = str(raw.get("id", f"case-{index}"))
    if "input" not in raw:
        raise SuiteError(f"case {case_id!r}: missing 'input'")
    reserved = {"id", "input", "grade"}
    meta = {k: v for k, v in raw.items() if k not in reserved}
    return Case(
        id=case_id,
        input=str(raw["input"]),
        graders=_parse_graders(raw.get("grade"), case_id),
        meta=meta,
    )


def load_suite(path: str | Path) -> Suite:
    path = Path(path)
    where = str(path)
    data = _load_raw(path)

    if "cases" not in data or not isinstance(data["cases"], list):
        raise SuiteError(f"{where}: 'cases' must be a list")

    return Suite(
        name=str(data.get("name", path.stem)),
        target=_parse_target(data.get("target"), where),
        cases=tuple(_parse_case(c, i) for i, c in enumerate(data["cases"])),
    )
