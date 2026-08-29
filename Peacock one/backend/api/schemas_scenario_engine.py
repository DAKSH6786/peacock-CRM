"""Peacock Scenario Engine API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ContextSignalsRequest(BaseModel):
    technical_seo_health: float = Field(default=70.0, ge=0.0, le=100.0)
    content_velocity: float = Field(default=50.0, ge=0.0, le=100.0)
    content_freshness: float = Field(default=70.0, ge=0.0, le=100.0)
    topical_coverage: float = Field(default=70.0, ge=0.0, le=100.0)
    third_party_authority: float = Field(default=70.0, ge=0.0, le=100.0)
    seo_demand: float = Field(default=50.0, ge=0.0, le=100.0)
    geo_opportunity: float = Field(default=50.0, ge=0.0, le=100.0)
    aeo_opportunity: float = Field(default=50.0, ge=0.0, le=100.0)
    data_quality: float = Field(default=70.0, ge=0.0, le=100.0)
    competitor_pressure: float = Field(default=50.0, ge=0.0, le=100.0)


class AssumptionRequest(BaseModel):
    assumption_key: str = Field(min_length=1, max_length=128)
    statement: str = Field(min_length=1)
    sensitivity: str = Field(default="medium", pattern="^(low|medium|high)$")
    affects_strategies: list[str] = Field(default_factory=list)


class ExtraMetricRequest(BaseModel):
    metric_code: str = Field(min_length=1, max_length=64)
    metric_label: str = Field(min_length=1, max_length=255)


class ScenarioBriefRequest(BaseModel):
    client_brand: str = Field(min_length=1, max_length=255)
    horizon_days: int = Field(default=90, ge=1, le=365)
    primary_metric: str = "organic_visibility_90d"
    primary_metric_label: str = "Projected 90-Day Organic Visibility"
    context: ContextSignalsRequest = Field(default_factory=ContextSignalsRequest)
    assumptions: list[AssumptionRequest] = Field(default_factory=list)
    strategies: list[str] = Field(default_factory=list)
    extra_metrics: list[ExtraMetricRequest] = Field(default_factory=list)


class ScenarioAnalysisRequest(BaseModel):
    website_id: str
    workspace_id: str | None = None
    name: str = Field(min_length=2, max_length=255)
    brief: ScenarioBriefRequest
    notes: str | None = None


class MetricRangeResponse(BaseModel):
    metric_code: str
    metric_label: str
    range_low_pct: float
    range_high_pct: float
    unit: str


class ScenarioResponse(BaseModel):
    strategy_code: str
    strategy_label: str
    is_baseline: bool
    is_peacock_recommended: bool
    range_low_pct: float
    range_high_pct: float
    range_mid_pct: float | None
    confidence: float
    data_quality: float
    uncertainty: float
    rationale: str
    rank: int
    metric_ranges: list[MetricRangeResponse]
    display_band: str


class AssumptionResponse(BaseModel):
    assumption_key: str
    statement: str
    sensitivity: str
    affects_strategies: list[str]


class ScenarioAnalysisResponse(BaseModel):
    analysis_id: str
    name: str
    client_brand: str
    methodology: str
    horizon_days: int
    primary_metric: str
    primary_metric_label: str
    ranges_not_fake_precision: bool
    ranges_disclaimer: str
    methodology_note: str
    overall_confidence: float
    overall_data_quality: float
    overall_uncertainty: float
    assumptions_summary: str
    recommended_strategy_code: str
    comparison_table: list[dict]
    scenarios: list[ScenarioResponse]
    assumptions: list[AssumptionResponse]
    summary: str


class ScenarioCatalogResponse(BaseModel):
    strategies: dict[str, str]
    strategy_codes: list[str]
    default_metric: str
    default_metric_label: str
    methodology: str
    methodology_note: str
    ranges_not_fake_precision: bool
    ranges_disclaimer: str
    example_comparison: list[dict]
