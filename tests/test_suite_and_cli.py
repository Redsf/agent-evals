"""Suite-loader validation and CLI-level behavior."""

from __future__ import annotations

import json

import pytest

from agent_evals.cli import EXIT_FAILURES, EXIT_OK, EXIT_USAGE, main
from agent_evals.suite import SuiteError, load_suite


def write(tmp_path, data):
    path = tmp_path / "s.json"
    path.write_text(json.dumps(data))
    return path


def test_unknown_grader_is_rejected(tmp_path):
    path = write(tmp_path, {
        "target": {"url": "http://x"},
        "cases": [{"id": "c1", "input": "q", "grade": [{"no_such_grader": 1}]}],
    })
    with pytest.raises(SuiteError, match="unknown grader"):
        load_suite(path)


def test_case_without_input_is_rejected(tmp_path):
    path = write(tmp_path, {
        "target": {"url": "http://x"},
        "cases": [{"id": "c1", "grade": [{"refuses": True}]}],
    })
    with pytest.raises(SuiteError, match="missing 'input'"):
        load_suite(path)


def test_target_without_url_is_rejected(tmp_path):
    path = write(tmp_path, {"target": {}, "cases": []})
    with pytest.raises(SuiteError, match="url"):
        load_suite(path)


def test_meta_fields_are_preserved(tmp_path):
    path = write(tmp_path, {
        "target": {"url": "http://x"},
        "cases": [{"id": "c1", "input": "q", "note": "hi", "grade": [{"refuses": True}]}],
    })
    suite = load_suite(path)
    assert suite.cases[0].meta["note"] == "hi"


def test_cli_list_graders_exits_zero(capsys):
    assert main(["list-graders"]) == EXIT_OK
    assert "no_injection" in capsys.readouterr().out


def test_cli_bad_suite_is_usage_error(tmp_path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    assert main(["run", str(bad)]) == EXIT_USAGE


def test_cli_run_against_dead_endpoint_fails(tmp_path, capsys):
    # A real HTTP call to a closed port: the run completes and reports failure
    # rather than crashing, and exits non-zero.
    suite = tmp_path / "s.json"
    suite.write_text(json.dumps({
        "name": "dead",
        "target": {"url": "http://127.0.0.1:1/never", "extract": "answer", "timeout": 1},
        "cases": [{"id": "c1", "input": "hi", "grade": [{"contains_all": "x"}]}],
    }))
    assert main(["run", str(suite), "--no-color"]) == EXIT_FAILURES
