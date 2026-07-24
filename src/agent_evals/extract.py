"""Pull a value out of a JSON response by a small dotted-path syntax.

Supported forms:
    answer            -> response["answer"]
    data.output       -> response["data"]["output"]
    $.result.text     -> response["result"]["text"]   ($ and $. prefixes ignored)
    items.0.text      -> response["items"][0]["text"]  (numeric segment indexes a list)

Kept intentionally tiny — this is not a full JSONPath. Returns None if the path
does not resolve, so a grader can decide whether a missing field is a failure.
"""

from __future__ import annotations


def _segments(path: str) -> list[str]:
    path = path.strip()
    if path.startswith("$."):
        path = path[2:]
    elif path == "$":
        return []
    return [seg for seg in path.split(".") if seg]


def extract_path(data: object, path: str | None) -> object | None:
    if path is None or path in ("", "$"):
        return data

    current = data
    for segment in _segments(path):
        if isinstance(current, dict):
            current = current.get(segment)
        elif isinstance(current, list) and segment.isdigit():
            index = int(segment)
            current = current[index] if index < len(current) else None
        else:
            return None
        if current is None:
            return None
    return current


def as_text(value: object) -> str:
    """Best-effort text form of an extracted value for text-based graders."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    import json

    return json.dumps(value, ensure_ascii=False)
