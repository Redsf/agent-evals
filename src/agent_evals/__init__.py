"""agent-evals — evaluate any AI automation behind an HTTP endpoint.

Point it at an n8n webhook, a FastAPI route, a LangGraph server — anything that
takes JSON and returns JSON — and grade the responses against a suite of cases.

Deterministic graders run on the standard library alone (no API key, no flake).
The LLM-as-judge grader is opt-in, for the checks that genuinely need a model.
"""

__version__ = "0.1.0"
