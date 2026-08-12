"""Peacock Judge 2.0 API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class EvidenceRequest(BaseModel):
    evidence_type: str = Field(min_length=1, max_length=64)
    statement: str = Field(min_length=1)
    source_ref: str | None = None
    reliability: float = Field(default=50.0, ge=0.0, le=100.0)
    signal_code: str | None = None


class ReversalConditionRequest(BaseModel):
    condition_key: str = Field(min_length=1, max_length=128)
    metric_code: str = Field(min_length=1, max_length=64)
    operator: str = Field(min_length=1, max_length=16)
    threshold: float
    statement: str = Field(min_length=1)
    unit: str | None = None
    reevaluate_action: str = "re-evaluate"
    priority: float = 50.0


class JudgeBriefRequest(BaseModel):
    decision_question: str = Field(min_length=4)
    client_brand: str = Field(min_length=1, max_length=255)
    signals: dict[str, float] = Field(default_factory=dict)
    evidence: list[EvidenceRequest] = Field(default_factory=list)
    reversal_conditions: list[ReversalConditionRequest] = Field(default_factory=list)
    business_goal_summary: str | None = None
    alternative_hint: str | None = None
    council2_session_id: str | None = None
    custom_weights: dict[str, float] | None = None


class Judge2Request(BaseModel):
    website_id: str
    workspace_id: str | None = None
    name: str = Field(min_length=2, max_length=255)
    brief: JudgeBriefRequest
    notes: str | None = None


class SignalScoreResponse(BaseModel):
    signal_code: str
    raw_value: float
    weight: float
    inverted: bool
    contribution: float
    explanation: str
    computed_outside_llm: bool


class EvidenceResponse(BaseModel):
    evidence_type: str
    statement: str
    source_ref: str | None
    reliability: float
    signal_code: str | None


class ReversalConditionResponse(BaseModel):
    condition_key: str
    metric_code: str
    operator: str
    threshold: float
    unit: str | None
    statement: str
    reevaluate_action: str
    priority: float


class Judge2Response(BaseModel):
    judgment_id: str
    name: str
    client_brand: str
    decision_question: str
    methodology: str
    scoring_outside_llm: bool
    scoring_note: str
    methodology_note: str
    recommended_action: str
    why: str
    evidence: list[EvidenceResponse]
    expected_upside: str
    expected_upside_score: float
    risk_summary: str
    risk_score: float
    confidence: float
    alternative: str
    what_would_change_decision: str
    reversal_conditions: list[ReversalConditionResponse]
    signal_scores: list[SignalScoreResponse]
    composite_score: float
    action_code: str
    summary: str


class Judge2CatalogResponse(BaseModel):
    signal_families: list[str]
    default_weights: dict[str, float]
    methodology: str
    methodology_note: str
    scoring_outside_llm: bool
    scoring_note: str
    output_fields: list[str]
    example_reversal_conditions: list[str]
