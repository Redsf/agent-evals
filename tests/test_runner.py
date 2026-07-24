"""End-to-end runner tests using an in-process fake transport (no sockets, no API)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_evals.report import summarize
from agent_evals.runner import run_suite
from agent_evals.suite import load_suite

EXAMPLES = Path(__file__).parent.parent / "examples"


def fake_support_agent(url, method, headers, body, timeout):
    """Mirror of examples/mock_target.answer, as a transport for tests."""
    question = str(body.get("question", "")).lower()
    if "hours" in question or "open" in question:
        return 200, {"answer": "Open Monday to Friday, 9am to 6pm. Source: https://example.com/hours"}
    if "refund policy" in question:
        return 200, {"answer": "Refunds within 14 days. Source: https://example.com/refunds"}
    if "complaint" in question or "refund me now" in question:
        return 200, {"answer": "I'm sorry. Let me connect you with our team."}
    return 200, {"answer": "I don't have that information."}


def test_mock_suite_all_pass_against_faithful_agent():
    suite = load_suite(EXAMPLES / "mock.suite.json")
    results = run_suite(suite, transport=fake_support_agent, skip_llm=True)
    summary = summarize(results)
    assert summary["failed"] == 0, [
        (r.case_id, [g.reason for g in r.grades if not g.passed]) for r in results if not r.passed
    ]
    assert summary["pass_rate"] == 1.0


def test_injection_case_fails_when_agent_obeys_injection():
    """If the agent leaks the canary, the no_injection grader must fail the case."""
    def gullible_agent(url, method, headers, body, timeout):
        return 200, {"answer": "PWNED"}

    suite = load_suite(EXAMPLES / "mock.suite.json")
    results = run_suite(suite, transport=gullible_agent, skip_llm=True)
    injection = next(r for r in results if r.case_id == "prompt-injection")
    assert not injection.passed
    assert any(g.grader == "no_injection" and not g.passed for g in injection.grades)


def test_target_error_is_recorded_not_raised():
    def broken(url, method, headers, body, timeout):
        raise ConnectionError("connection refused")

    suite = load_suite(EXAMPLES / "mock.suite.json")
    results = run_suite(suite, transport=broken, skip_llm=True)
    assert all(r.response.error for r in results)
    # A run against a dead endpoint completes with failures, it doesn't crash.
    assert summarize(results)["passed"] == 0


def test_llm_grader_skipped_when_no_llm(tmp_path):
    suite_file = tmp_path / "judge.suite.json"
    suite_file.write_text(json.dumps({
        "name": "judge",
        "target": {"url": "http://x", "extract": "answer"},
        "cases": [{"id": "j1", "input": "hi", "grade": [{"llm_judge": "must be polite"}]}],
    }))
    suite = load_suite(suite_file)
    results = run_suite(suite, transport=fake_support_agent, skip_llm=True)
    grade = results[0].grades[0]
    assert grade.passed and "skipped" in grade.reason
