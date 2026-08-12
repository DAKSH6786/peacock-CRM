"""Learning Engine 2.0 service models."""

from __future__ import annotations

from dataclasses import dataclass

from learning_engine2.learning import LearningRecordView, LearningRunResult


@dataclass
class Learning2CreateSpec:
    website_id: str
    view: LearningRecordView
    central_recommendation_id: str | None = None
    notes: str | None = None


@dataclass
class Learning2RecordReport:
    record_id: str
    methodology: str
    view: LearningRecordView


@dataclass
class Learning2RunReport:
    run_id: str
    name: str
    methodology: str
    result: LearningRunResult
