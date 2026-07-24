"""Grader registry.

Add a grader: implement a Grader subclass, then register an instance below. The
runner, the suite loader's validation, and `--list-graders` all read from here.
"""

from __future__ import annotations

from .adversarial import Escalates, NoInjection, Refuses
from .base import Grader
from .json_graders import JsonField, JsonHasKeys, NoNullFields
from .llm_judge import LlmJudge
from .text_graders import (
    ContainsAll,
    ContainsAny,
    HasCitation,
    MaxWords,
    MinWords,
    NotContains,
    RegexMatch,
)

ALL_GRADERS: tuple[Grader, ...] = (
    ContainsAll(),
    ContainsAny(),
    NotContains(),
    RegexMatch(),
    HasCitation(),
    MaxWords(),
    MinWords(),
    JsonField(),
    JsonHasKeys(),
    NoNullFields(),
    Refuses(),
    Escalates(),
    NoInjection(),
    LlmJudge(),
)

GRADERS_BY_NAME: dict[str, Grader] = {g.name: g for g in ALL_GRADERS}
