"""Peacock Opportunity Engine API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class EvidenceRequest(BaseModel):
    evidence_type: str = Field(min_length=1, max_length=64)
    statement: str = Field(min_length=1)
    source_ref: str | None = None
    strength: float = Field(default=50.0, ge=0.0, le=100.0)


class SignalRequest(BaseModel):
    opportunity_type: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=512)
    description: str = Field(min_length=1)
    impact: float = Field(ge=0.0, le=100.0)
    urgency: float = Field(ge=0.0, le=100.0)
    confidence: float = Field(ge=0.0, le=100.0)
    difficulty: float = Field(ge=0.0, le=100.0)
    expected_value: float = Field(ge=0.0, le=100.0)
    recommended_action: str = Field(min_length=1)
    evidence: list[EvidenceRequest] = Field(default_factory=list)
    related_entity: str | None = None
    related_url: str | None = None
    opportunity_key: str | None = None


class OutcomeFeedbackRequest(BaseModel):
    opportunity_type: str = Field(min_length=1, max_length=64)
    impact: float = Field(ge=0.0, le=100.0)
    urgency: float = Field(ge=0.0, le=100.0)
    confidence: float = Field(ge=0.0, le=100.0)
    difficulty: float = Field(ge=0.0, le=100.0)
    expected_value: float = Field(ge=0.0, le=100.0)
    predicted_score: float = Field(ge=0.0, le=100.0)
    realized_outcome: float = Field(ge=0.0, le=100.0)
    opportunity_key: str | None = None
    outcome_label: str = "observed"
    notes: str | None = None


class OpportunityScanRequest(BaseModel):
    website_id: str
    workspace_id: str | None = None
    name: str = Field(min_length=2, max_length=255)
    client_brand: str = Field(min_length=1, max_length=255)
    signals: list[SignalRequest] = Field(min_length=1)
    outcome_feedback: list[OutcomeFeedbackRequest] = Field(default_factory=list)
    notes: str | None = None


class RecordOutcomeRequest(BaseModel):
    website_id: str
    workspace_id: str | None = None
    feedback: OutcomeFeedbackRequest


class EvidenceResponse(BaseModel):
    evidence_type: str
    statement: str
    source_ref: str | None
    strength: float


class RankingFactorResponse(BaseModel):
    feature_code: str
    feature_value: float
    weight: float
    contribution: float
    weight_source: str
    explanation: str


class OpportunityResponse(BaseModel):
    opportunity_key: str
    opportunity_type: str
    title: str
    description: str
    impact: float
    urgency: float
    confidence: float
    difficulty: float
    expected_value: float
    recommended_action: str
    evidence: list[EvidenceResponse]
    rank: int
    opportunity_score: float
    ranking_explanation: str
    ranking_factors: list[RankingFactorResponse]
    related_entity: str | None = None
    related_url: str | None = None


class RankingWeightResponse(BaseModel):
    feature_code: str
    base_weight: float
    learned_weight: float
    effective_weight: float
    learning_sample_size: int
    explanation: str


class OpportunityScanResponse(BaseModel):
    scan_id: str
    name: str
    client_brand: str
    methodology: str
    always_on_layer: bool
    ranking_model_version: int
    ranking_is_adaptive: bool
    fixed_formula_rejected: bool
    always_on_note: str
    methodology_note: str
    summary: str
    ranking_weights: list[RankingWeightResponse]
    opportunities: list[OpportunityResponse]


class OpportunityCatalogResponse(BaseModel):
    opportunity_types: list[str]
    type_examples: list[dict]
    ranking_features: list[str]
    default_ranking_weights: dict[str, float]
    methodology: str
    methodology_note: str
    always_on_note: str
    fixed_formula_rejected: bool
