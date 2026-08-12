"""Peacock Judge 2.0 service models."""

from __future__ import annotations

from dataclasses import dataclass

from judge2.scoring import JudgeBrief, JudgeResult


@dataclass
class Judge2Spec:
    website_id: str
    name: str
    brief: JudgeBrief
    notes: str | None = None


@dataclass
class Judge2Report:
    judgment_id: str
    name: str
    client_brand: str
    decision_question: str
    methodology: str
    result: JudgeResult
