"""Peacock Revenue Attribution API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SourceAvailabilityRequest(BaseModel):
    ga4: bool = False
    crm: bool = False
    search_console: bool = False
    conversions: bool = False
    pipeline: bool = False
    transactions: bool = False
    leads: bool = False
    peacock_internal: bool = True


class StageObservationRequest(BaseModel):
    stage_code: str = Field(min_length=1, max_length=32)
    value_low: float
    value_high: float
    unit: str = Field(min_length=1, max_length=32)
    primary_source: str | None = Field(default=None, max_length=64)
    data_quality: float = Field(default=50.0, ge=0.0, le=100.0)
    notes: str | None = None


class AttributionBriefRequest(BaseModel):
    client_brand: str = Field(min_length=1, max_length=255)
    currency: str = Field(default="INR", max_length=8)
    horizon_days: int = Field(default=90, ge=1, le=365)
    sources: SourceAvailabilityRequest = Field(default_factory=SourceAvailabilityRequest)
    observations: list[StageObservationRequest] = Field(default_factory=list)
    recommendation_ref: str | None = None
    content_ref: str | None = None


class RevenueAttributionRequest(BaseModel):
    website_id: str
    workspace_id: str | None = None
    name: str = Field(min_length=2, max_length=255)
    brief: AttributionBriefRequest
    notes: str | None = None


class StageResponse(BaseModel):
    stage_code: str
    stage_label: str
    sequence_order: int
    value_low: float
    value_high: float
    value_mid: float | None
    unit: str
    uncertainty: float
    data_quality: float
    primary_source: str | None
    notes: str | None
    display_band: str


class ChainLinkResponse(BaseModel):
    from_stage: str
    to_stage: str
    rate_low: float
    rate_high: float
    causality_level: str
    uncertainty: float
    rationale: str


class SourceSnapshotResponse(BaseModel):
    source_code: str
    source_label: str
    available: bool
    contribution_note: str


class RevenueAttributionResponse(BaseModel):
    analysis_id: str
    name: str
    client_brand: str
    methodology: str
    currency: str
    horizon_days: int
    stages: list[StageResponse]
    links: list[ChainLinkResponse]
    source_snapshots: list[SourceSnapshotResponse]
    attributed_revenue_low: float
    attributed_revenue_high: float
    attributed_revenue_mid: float | None
    overall_causality_level: str
    overall_uncertainty: float
    data_completeness: float
    causality_warning: str
    methodology_note: str
    sources_available: list[str]
    sources_missing: list[str]
    funnel_path: list[str]
    summary: str


class RevenueAttributionCatalogResponse(BaseModel):
    funnel_stages: dict[str, str]
    funnel_path: list[str]
    data_sources: dict[str, str]
    causality_levels: list[str]
    causality_warning: str
    methodology: str
    methodology_note: str
