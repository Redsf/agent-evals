"""A tiny local stand-in for a real automation endpoint.

Run it to try agent-eval end to end without wiring up an n8n webhook or an API
key:

    python examples/mock_target.py &          # serves on http://127.0.0.1:8900
    agent-eval run examples/mock.suite.json --no-llm

It mimics a support agent: answers a couple of known questions with a source
link, honestly refuses what it doesn't know, escalates complaints, and — the
important part — ignores instructions embedded in the incoming question.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer

KNOWLEDGE = {
    "hours": "We're open Monday to Friday, 9am to 6pm. Source: https://example.com/hours",
    "refund": "Refunds are processed within 14 days. Source: https://example.com/refunds",
}


def answer(question: str) -> str:
    q = question.lower()
    # Injection resistance: the agent treats the question as data, never as
    # instructions, so a smuggled "print PWNED" is simply not acted on.
    if "hours" in q or "open" in q:
        return KNOWLEDGE["hours"]
    # Intent before FAQ: a complaint that happens to mention "refund" must
    # escalate, not get answered with the refund policy. Order matters.
    if "complaint" in q or "angry" in q or "never arrived" in q or "refund me now" in q:
        return "I'm sorry to hear that. Let me connect you with a member of our team who can help."
    if "refund" in q:
        return KNOWLEDGE["refund"]
    return "I don't have that information in our documentation."


class Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802 - http.server API
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length) or b"{}")
        reply = {"answer": answer(str(payload.get("question", payload.get("input", ""))))}
        body = json.dumps(reply).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args) -> None:  # keep the demo output quiet
        pass


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8900), Handler)
    print("mock target on http://127.0.0.1:8900 (Ctrl-C to stop)")
    server.serve_forever()
