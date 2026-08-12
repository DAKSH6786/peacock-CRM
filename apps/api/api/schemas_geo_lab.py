"""Peacock GEO Lab API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class VariantRequest(BaseModel):
    variant_code: str = Field(min_length=1, max_length=16)
    label: str | None = None
    treatment_description: str | None = None
    is_baseline: bool = False
    change_summary: str | None = None


class PageRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2048)
    page_role: str = Field(pattern="^(control|test)$")
    variant_code: str | None = None
    title: str | None = None
    matched_group: str | None = None
    match_key: str | None = None


class ObservationRequest(BaseModel):
    page_url: str = Field(min_length=1)
    metric_code: str = Field(min_length=1, max_length=64)
    observed_at: str = Field(min_length=4, max_length=32)
    period: str = Field(pattern="^(pre|post|during)$")
    value: float
    engine: str | None = None
    notes: str | None = None


class GeoLabExperimentRequest(BaseModel):
    website_id: str
    workspace_id: str | None = None
    name: str = Field(min_length=2, max_length=255)
    client_brand: str = Field(min_length=1, max_length=255)
    hypothesis: str = Field(min_length=4)
    topic_cluster: str | None = None
    design_type: str = "before_after_with_controls"
    pre_window_start: str | None = None
    pre_window_end: str | None = None
    post_window_start: str | None = None
    post_window_end: str | None = None
    intervention_date: str | None = None
    variants: list[VariantRequest] = Field(default_factory=list)
    pages: list[PageRequest] = Field(min_length=1)
    observations: list[ObservationRequest] = Field(min_length=1)
    known_confounds: list[str] = Field(default_factory=list)
    concurrent_changes: list[str] = Field(default_factory=list)
    notes: str | None = None
    use_default_variants_if_empty: bool = True


class MetricDeltaResponse(BaseModel):
    scope_type: str
    scope_id: str
    metric_code: str
    pre_mean: float
    post_mean: float
    absolute_delta: float
    relative_delta_pct: float | None
    control_adjusted_delta: float | None
    observation_count_pre: int
    observation_count_post: int


class CausalityAssessmentResponse(BaseModel):
    metric_code: str
    variant_code: str
    causality_level: str
    claim_allowed: bool
    auto_causal_conclusion_rejected: bool
    rationale: str
    confounds_noted: str | None
    design_supports: list[str]
    confidence_note: str


class TimeSeriesPointResponse(BaseModel):
    observed_at: str
    period: str
    metric_code: str
    scope_type: str
    scope_id: str
    value: float


class GeoLabExperimentResponse(BaseModel):
    experiment_id: str
    name: str
    client_brand: str
    hypothesis: str
    methodology: str
    design_type: str
    design_features: list[str]
    causality_warning: str
    overall_causality_level: str
    overall_summary: str
    auto_causal_conclusion_rejected: bool
    variants: list[dict]
    pages: list[dict]
    deltas: list[MetricDeltaResponse]
    causality_assessments: list[CausalityAssessmentResponse]
    time_series: list[TimeSeriesPointResponse]


class GeoLabCatalogResponse(BaseModel):
    variant_presets: dict[str, str]
    variant_codes: list[str]
    metrics: list[str]
    page_roles: list[str]
    causality_levels: list[str]
    causality_warning: str
    methodology: str
    methodology_note: str
