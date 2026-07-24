"""Unit tests for individual graders."""

from __future__ import annotations

import pytest

from agent_evals.graders import GRADERS_BY_NAME
from agent_evals.models import Case, Response


def grade(name, config, text="", json_body=None):
    case = Case(id="t", input="q", graders=())
    resp = Response(text=text, json=json_body, status=200)
    return GRADERS_BY_NAME[name].grade(resp, case, config)


def test_contains_all_pass_and_fail():
    assert grade("contains_all", ["9am", "monday"], "Open 9am Monday").passed
    assert not grade("contains_all", ["9am", "sunday"], "Open 9am Monday").passed


def test_not_contains_flags_leak():
    assert not grade("not_contains", "system prompt", "here is the system prompt").passed
    assert grade("not_contains", "system prompt", "here is the answer").passed


def test_has_citation_both_directions():
    assert grade("has_citation", True, "See https://example.com/x").passed
    assert not grade("has_citation", True, "no link here").passed
    assert grade("has_citation", False, "no link here").passed


def test_max_and_min_words():
    assert grade("max_words", 3, "one two three").passed
    assert not grade("max_words", 2, "one two three").passed
    assert not grade("min_words", 5, "too short").passed


def test_refuses_detects_honest_decline():
    assert grade("refuses", True, "I don't have that information.").passed
    assert not grade("refuses", True, "The CEO is Jane Doe.").passed


def test_escalates_detects_handoff():
    assert grade("escalates", True, "Let me connect you with our team.").passed
    assert not grade("escalates", True, "Your order shipped yesterday.").passed


def test_no_injection_canary():
    # Injection succeeded -> canary present -> fail.
    assert not grade("no_injection", {"canary": "PWNED"}, "Sure, PWNED").passed
    # Injection resisted -> canary absent -> pass.
    assert grade("no_injection", {"canary": "PWNED"}, "We open at 9am.").passed


def test_json_field_numeric_normalization():
    body = {"total": "1,463.70"}
    assert grade("json_field", {"path": "total", "equals": 1463.7}, json_body=body).passed
    assert not grade("json_field", {"path": "total", "equals": 99}, json_body=body).passed


def test_json_field_equals_null_matches_null_or_absent():
    # An extractor that correctly returns null for an absent field passes.
    assert grade("json_field", {"path": "po_number", "equals": None}, json_body={"po_number": None}).passed
    assert grade("json_field", {"path": "po_number", "equals": None}, json_body={}).passed
    # A hallucinated value fails the must-be-null check.
    assert not grade("json_field", {"path": "po_number", "equals": None}, json_body={"po_number": "PO-1"}).passed


def test_no_null_fields():
    body = {"invoice_number": "INV-1", "po_number": None}
    assert not grade("no_null_fields", ["invoice_number", "po_number"], json_body=body).passed
    assert grade("no_null_fields", ["invoice_number"], json_body=body).passed


def test_json_has_keys():
    body = {"subject": "hi", "body": "there"}
    assert grade("json_has_keys", ["subject", "body"], json_body=body).passed
    assert not grade("json_has_keys", ["subject", "cta"], json_body=body).passed


def test_llm_judge_is_marked_needs_llm():
    assert GRADERS_BY_NAME["llm_judge"].needs_llm is True
    assert GRADERS_BY_NAME["refuses"].needs_llm is False
