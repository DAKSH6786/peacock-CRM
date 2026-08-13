"""Peacock Proprietary Metrics API schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class MetricInputsRequest(BaseModel):
    visibility_dimensions: dict[str, float] = Field(default_factory=dict)
    soa_indicators: dict[str, float] = Field(default_factory=dict)
    cis_components: dict[str, float] = Field(default_factory=dict)
    entity_components: dict[str, float] = Field(default_factory=dict)
    answer_readiness: dict[str, float] = Field(default_factory=dict)
    citability_components: dict[str, float] = Field(default_factory=dict)
    moat_format_prior: float | None = None
    moat_information_gain: float | None = None
    topic_opportunity: dict[str, float] = Field(default_factory=dict)
    writer_match: dict[str, float] = Field(default_factory=dict)
    agent_checks: dict[str, float] = Field(default_factory=dict)
    competitive_threat: dict[str, float] = Field(default_factory=dict)
    opportunity_confidence: dict[str, float] = Field(default_factory=dict)
    ai_visibility_parts: dict[str, float] = Field(default_factory=dict)


class ProprietaryMetricsBriefRequest(BaseModel):
    client_brand: str = Field(min_length=1, max_length=255)
    inputs: MetricInputsRequest = Field(default_factory=MetricInputsRequest)
    scored_at: datetime | None = None


class ProprietaryMetricsCreateRequest(BaseModel):
    website_id: str
    workspace_id: str | None = None
    name: str = Field(min_length=2, max_length=255)
    brief: ProprietaryMetricsBriefRequest
    notes: str | None = None


class MetricComponentResponse(BaseModel):
    component_key: str
    component_label: str
    raw_value: float
    weight: float
    contribution: float
    rank_order: int


class MetricScoreResponse(BaseModel):
    metric_key: str
    metric_label: str
    score: float
    unit: str
    formula_id: str
    formula_text: str
    explanation: str
    proprietary_note: str
    components: list[MetricComponentResponse]


class ProprietaryMetricsResponse(BaseModel):
    scorecard_id: str
    name: str
    client_brand: str
    methodology: str
    scored_at: str
    metrics_scored: int
    proprietary_disclaimer: str
    methodology_note: str
    summary: str
    metrics: list[MetricScoreResponse]
    not_official_platforms: list[str]


class FormulaDocResponse(BaseModel):
    formula_id: str
    metric_key: str
    metric_label: str
    unit: str
    formula_text: str
    range_note: str
    components: list[str]
    proprietary_note: str


class ProprietaryMetricsCatalogResponse(BaseModel):
    metric_keys: list[str]
    metric_labels: dict[str, str]
    proprietary_disclaimer: str
    not_official_platforms: list[str]
    formulas: list[FormulaDocResponse]
    default_weights: dict[str, dict[str, float]]
    important: str
    methodology_note: str


class ProprietaryMetricsPreviewResponse(BaseModel):
    client_brand: str
    scored_at: str
    metrics_scored: int
    proprietary_disclaimer: str
    methodology_note: str
    summary: str
    metrics: list[MetricScoreResponse]
    not_official_platforms: list[str]
