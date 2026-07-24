"""LLM-as-judge grader — the one grader that needs a model.

Opt-in by design. Reach for it only when a check can't be made deterministic:
open-ended correctness, tone, faithfulness to a rubric. Everything else should
use a deterministic grader, which is cheaper and never flakes.

Talks to any OpenAI-compatible chat-completions endpoint. Configure the base URL
and model via environment variables so the same suite runs against a hosted model
or a local one:

    AGENT_EVALS_JUDGE_BASE_URL   default https://api.openai.com/v1
    AGENT_EVALS_JUDGE_MODEL      default gpt-4o-mini
    AGENT_EVALS_JUDGE_API_KEY    falls back to OPENAI_API_KEY
"""

from __future__ import annotations

import json
import os
import urllib.request

from ..models import Case, GradeResult, Response
from .base import Grader

JUDGE_PROMPT = """You are grading one response from an AI system.

Question / input:
{question}

Grading rubric:
{rubric}

System's response:
{answer}

Decide whether the response satisfies the rubric. Reply with ONLY a JSON object:
{{"pass": true/false, "reason": "<one sentence>"}}
"""


class MissingJudgeKey(RuntimeError):
    """Raised when the judge grader runs with no API key configured."""


def _judge_config() -> tuple[str, str, str | None]:
    base = os.environ.get("AGENT_EVALS_JUDGE_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("AGENT_EVALS_JUDGE_MODEL", "gpt-4o-mini")
    key = os.environ.get("AGENT_EVALS_JUDGE_API_KEY") or os.environ.get("OPENAI_API_KEY")
    return base, model, key


def _ask_judge(rubric: str, question: str, answer: str) -> dict:
    base, model, key = _judge_config()
    if not key:
        raise MissingJudgeKey(
            "llm_judge needs an API key — set AGENT_EVALS_JUDGE_API_KEY or OPENAI_API_KEY"
        )
    body = json.dumps({
        "model": model,
        "messages": [{
            "role": "user",
            "content": JUDGE_PROMPT.format(question=question, rubric=rubric, answer=answer or "(empty)"),
        }],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }).encode()
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.load(resp)
    return json.loads(payload["choices"][0]["message"]["content"])


class LlmJudge(Grader):
    name = "llm_judge"
    summary = "An LLM grades the response against a rubric (opt-in; needs an API key)."
    needs_llm = True

    def grade(self, response: Response, case: Case, config: object) -> GradeResult:
        rubric = config if isinstance(config, str) else (config or {}).get("rubric", "")
        if not rubric:
            raise ValueError("llm_judge needs a rubric string")
        verdict = _ask_judge(rubric, case.input, response.text)
        passed = bool(verdict.get("pass"))
        reason = verdict.get("reason", "no reason given")
        return self._ok(passed, f"judge: {reason}")
