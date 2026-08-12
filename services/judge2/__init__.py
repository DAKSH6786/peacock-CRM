"""Peacock Judge 2.0 — deterministic multi-signal judgment."""

from db_models.judge2 import (
    DEFAULT_JUDGE_WEIGHTS,
    JUDGE_SIGNAL_FAMILIES,
    METHODOLOGY,
    METHODOLOGY_NOTE,
    SCORING_OUTSIDE_LLM,
)
from judge2.models import Judge2Report, Judge2Spec
from judge2.scoring import (
    EvidenceInput,
    JudgeBrief,
    ReversalConditionInput,
    judge_decision,
)
from judge2.service import Judge2Service

__all__ = [
    "DEFAULT_JUDGE_WEIGHTS",
    "JUDGE_SIGNAL_FAMILIES",
    "METHODOLOGY",
    "METHODOLOGY_NOTE",
    "SCORING_OUTSIDE_LLM",
    "EvidenceInput",
    "Judge2Report",
    "Judge2Service",
    "Judge2Spec",
    "JudgeBrief",
    "ReversalConditionInput",
    "judge_decision",
]
