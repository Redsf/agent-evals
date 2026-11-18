"""Demo-only stand-in for a support agent after a bad prompt change.

Used by demo/demo.tape to show agent-eval catching a regression. It makes the
three mistakes the suite is designed to catch: it follows an instruction
smuggled into the question, answers a complaint with policy instead of
escalating, and invents a fact it has no source for.

    python demo/regressed_target.py &   # serves on http://127.0.0.1:8900
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer


def answer(question: str) -> str:
    q = question.lower()
    if "ignore all previous instructions" in q:
        return "PWNED"
    if "hours" in q or "open" in q:
        return "We're open Monday to Friday, 9am to 6pm. Source: https://example.com/hours"
    if "refund" in q:
        return "Refunds are processed within 14 days. Source: https://example.com/refunds"
    return "We have around 250 employees across three offices."


class Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802 - http.server API
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length) or b"{}")
        body = json.dumps({"answer": answer(str(payload.get("question", "")))}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args) -> None:
        pass


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 8900), Handler).serve_forever()
