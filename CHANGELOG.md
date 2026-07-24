# Changelog

## [0.1.0] — 2026-07-24

Initial release.

### Added

- HTTP target adapter with per-case body templating and dotted-path answer
  extraction. Works with any JSON-over-HTTP endpoint (n8n, FastAPI, LangGraph).
- Fourteen graders across four groups: text, structured/JSON, adversarial
  (`refuses`, `escalates`, `no_injection`), and an opt-in `llm_judge`.
- `agent-eval` CLI with `run` and `list-graders`; text, markdown, and JSON
  output; `--no-llm`, `--min-pass-rate`, and `--output`.
- JSON suites with zero dependencies; YAML suites via the `[yaml]` extra.
- A bundled mock target and example suites for an offline end-to-end demo.
- Zero required runtime dependencies.
