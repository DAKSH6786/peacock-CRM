"""Peacock Learning Engine 2.0 API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ContextFactorRequest(BaseModel):
    factor_key: str = Field(min_length=1, max_length=128)
    factor_value: str = Field(min_length=1)
    weight: float = Field(default=1.0, ge=0.0)


class CreateLearningRecordRequest(BaseModel):
    website_id: str
    workspace_id: str | None = None
    name: str = Field(min_length=2, max_length=255)
    industry: str = Field(min_length=1, max_length=64)
    context_summary: str = Field(min_length=1)
    recommendation_text: str = Field(min_length=1)
    expected_impact: str = Field(min_length=1)
    expected_impact_score: float = Field(ge=0.0, le=100.0)
    confidence: float = Field(ge=0.0, le=100.0)
    topic_key: str | None = None
    format_key: str | None = None
    source_key: str | None = None
    writer_key: str | None = None
    intervention_key: str | None = None
    engine_key: str | None = None
    context_factors: list[ContextFactorRequest] = Field(default_factory=list)
    central_recommendation_id: str | None = None
    notes: str | None = None


class ExecutionRequest(BaseModel):
    execution_summary: str = Field(min_length=1)
    execution_status: str = Field(default="executed", max_length=32)


class OutcomeRequest(BaseModel):
    actual_outcome: str = Field(min_length=1)
    actual_outcome_score: float = Field(ge=0.0, le=100.0)


class LearningRunRequest(BaseModel):
    workspace_id: str | None = None
    website_id: str | None = None
    name: str = Field(min_length=2, max_length=255)


class ContextFactorResponse(BaseModel):
    factor_key: str
    factor_value: str
    weight: float


class LearningRecordResponse(BaseModel):
    record_id: str
    methodology: str
    name: str
    industry: str
    record_status: str
    context_summary: str
    recommendation_text: str
    expected_impact: str
    expected_impact_score: float
    confidence: float
    execution_summary: str | None
    execution_status: str | None
    actual_outcome: str | None
    actual_outcome_score: float | None
    outcome_delta: float | None
    topic_key: str | None
    format_key: str | None
    source_key: str | None
    writer_key: str | None
    intervention_key: str | None
    engine_key: str | None
    context_factors: list[ContextFactorResponse]
    not_universal_geo_strategy: bool
    not_universal_geo_note: str


class DimensionInsightResponse(BaseModel):
    dimension: str
    dimension_key: str
    industry: str
    sample_size: int
    avg_expected_impact: float
    avg_actual_outcome: float
    avg_confidence: float
    success_rate: float
    insight_summary: str
    not_universal_geo_strategy: bool


class IndustryPolicyResponse(BaseModel):
    industry: str
    industry_label: str
    policy_code: str
    title: str
    guidance: str
    preferred_formats: list[str]
    preferred_sources: list[str]
    citation_interventions: list[str]
    forbidden_universal_claims: str
    sample_size: int
    success_rate: float | None
    active: bool


class LearningRunResponse(BaseModel):
    run_id: str
    name: str
    methodology: str
    records_considered: int
    insights: list[DimensionInsightResponse]
    industry_policies: list[IndustryPolicyResponse]
    industries_touched: list[str]
    not_universal_geo_strategy: bool
    methodology_note: str
    learning_questions: dict[str, str]
    summary: str


class Learning2CatalogResponse(BaseModel):
    industries: dict[str, str]
    industry_codes: list[str]
    learning_dimensions: list[str]
    loop_fields: list[str]
    not_universal_geo_strategy: bool
    not_universal_geo_note: str
    methodology_note: str
    learning_questions: dict[str, str]
