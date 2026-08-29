"""Content Digital Twin service models."""

from __future__ import annotations

from dataclasses import dataclass, field

from content_digital_twin.simulation import (
    ArticlePlan,
    FindingResult,
    RequirementScoreResult,
    SimulationContext,
)


@dataclass
class TwinSpec:
    website_id: str
    name: str
    client_brand: str
    article_plan: ArticlePlan
    simulation_context: SimulationContext
    topic_cluster: str | None = None
    content_lab_proposal_id: str | None = None
    notes: str | None = None


@dataclass
class TwinEvaluationReport:
    twin_id: str
    evaluation_id: str
    evaluation_number: int
    plan_revision: int
    client_brand: str
    methodology: str
    article_plan: ArticlePlan
    predicted_strength_score: float
    readiness_score: float
    summary: str
    requirement_scores: list[RequirementScoreResult]
    findings: list[FindingResult]
    findings_by_category: dict[str, list[FindingResult]] = field(default_factory=dict)


@dataclass
class TwinReport:
    twin_id: str
    name: str
    client_brand: str
    methodology: str
    plan_revision: int
    evaluation_count: int
    article_plan: ArticlePlan
    simulation_context: SimulationContext
    latest_evaluation: TwinEvaluationReport | None
    evaluation_history: list[dict] = field(default_factory=list)
