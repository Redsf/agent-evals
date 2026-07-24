# Contributing

## Development setup

```bash
git clone https://github.com/Redsf/agent-evals
cd agent-evals
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

The core has no required runtime dependencies — keep it that way so the tool
runs in bare CI. PyYAML is an optional extra, imported lazily only when a `.yaml`
suite is loaded. Dev-only tooling (pytest) is fine.

## Adding a grader

1. Subclass `Grader` in `src/agent_evals/graders/`. Group it with related
   graders (`text_graders.py`, `json_graders.py`, `adversarial.py`) or add a
   module.
2. Give it a snake_case `name`, a one-line `summary`, and — if it calls a model —
   set `needs_llm = True` so `--no-llm` skips it.
3. `grade(response, case, config)` returns a `GradeResult`. Use `self._ok(bool, reason)`.
4. Register the instance in `graders/__init__.py`.
5. Add a unit test in `tests/test_graders.py` covering both a pass and a fail.

## The deterministic-first principle

If a check can be made deterministic, it must be. An `llm_judge` grader that
could have been a `contains_all` costs money, adds latency, and flakes. New
graders that call a model need to justify why the check can't be done offline.

## Tests

`pytest` before every PR. The suite uses an in-process fake transport, so it
needs no network and no API key. CI runs on Python 3.9, 3.11, and 3.13, plus an
end-to-end smoke test against the bundled mock server.

## Commit style

Conventional commits (`feat:`, `fix:`, `docs:`, `chore:`, `test:`).
