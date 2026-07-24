"""Call the system under test over HTTP and normalize its reply.

The transport is a plain function so tests can substitute an in-process fake
without binding a socket. Anything callable with the same signature works as a
target — an n8n webhook, a FastAPI route, a mock.
"""

from __future__ import annotations

import copy
import json
import urllib.error
import urllib.request
from typing import Callable

from .extract import as_text, extract_path
from .models import Response, TargetSpec

# A transport takes (url, method, headers, body_dict, timeout) and returns
# (status_code, response_dict_or_text).
Transport = Callable[[str, str, dict, object, int], "tuple[int, object]"]


def _fill_template(value: object, case_input: str, meta: dict) -> object:
    """Recursively replace {{input}} and {{meta_field}} inside a body template."""
    if isinstance(value, str):
        out = value.replace("{{input}}", case_input)
        for key, replacement in meta.items():
            out = out.replace(f"{{{{{key}}}}}", str(replacement))
        return out
    if isinstance(value, dict):
        return {k: _fill_template(v, case_input, meta) for k, v in value.items()}
    if isinstance(value, list):
        return [_fill_template(v, case_input, meta) for v in value]
    return value


def build_body(target: TargetSpec, case_input: str, meta: dict) -> object:
    """Render the request body for a case. Defaults to {"input": <case input>}."""
    template = target.body if target.body is not None else {"input": "{{input}}"}
    return _fill_template(copy.deepcopy(template), case_input, meta)


def http_transport(url: str, method: str, headers: dict, body: object, timeout: int) -> tuple[int, object]:
    data = json.dumps(body).encode()
    request_headers = {"Content-Type": "application/json", **headers}
    req = urllib.request.Request(url, data=data, headers=request_headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
        try:
            return resp.status, json.loads(raw)
        except json.JSONDecodeError:
            return resp.status, raw


def call(
    target: TargetSpec,
    case_input: str,
    meta: dict,
    transport: Transport = http_transport,
) -> Response:
    """Send one case to the target and return a normalized Response."""
    body = build_body(target, case_input, meta)
    try:
        status, payload = transport(target.url, target.method, target.headers, body, target.timeout)
    except urllib.error.HTTPError as exc:
        return Response(text="", json=None, status=exc.code, error=f"HTTP {exc.code}: {exc.reason}")
    except Exception as exc:  # noqa: BLE001 - a failed call is a failed case, not a crash
        return Response(text="", json=None, status=None, error=str(exc))

    if isinstance(payload, (dict, list)):
        answer = extract_path(payload, target.extract)
        return Response(text=as_text(answer), json=payload, status=status)
    return Response(text=str(payload), json=None, status=status)
