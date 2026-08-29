"""Deep Competitor Intelligence API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DiscoveryCandidateRequest(BaseModel):
    domain: str = Field(min_length=1, max_length=255)
    name: str | None = None
    serp_overlap: float = Field(default=0.0, ge=0.0, le=1.0)
    keyword_overlap: float = Field(default=0.0, ge=0.0, le=1.0)
    topic_overlap: float = Field(default=0.0, ge=0.0, le=1.0)
    ai_mention_overlap: float = Field(default=0.0, ge=0.0, le=1.0)
    citation_overlap: float = Field(default=0.0, ge=0.0, le=1.0)
    entity_similarity: float = Field(default=0.0, ge=0.0, le=1.0)
    product_similarity: float = Field(default=0.0, ge=0.0, le=1.0)
    known_business_competitor: bool = False


class DimensionScoreRequest(BaseModel):
    competitor_domain: str
    competitor_name: str
    dimension: str
    client_score: float = Field(ge=0.0, le=1.0)
    competitor_score: float = Field(ge=0.0, le=1.0)
    evidence: str | None = None


class ContentComparisonRequest(BaseModel):
    competitor_domain: str
    competitor_url: str
    client_url: str | None = None
    dimension: str
    client_score: float = Field(ge=0.0, le=1.0)
    competitor_score: float = Field(ge=0.0, le=1.0)
    evidence_summary: str = Field(min_length=1)


class DeepCompetitorRequest(BaseModel):
    website_id: str
    workspace_id: str | None = None
    name: str = Field(min_length=2, max_length=255)
    client_brand: str = Field(min_length=1, max_length=255)
    client_domain: str = Field(min_length=1, max_length=255)
    topic_cluster: str | None = None
    discovery_candidates: list[DiscoveryCandidateRequest] = Field(min_length=1)
    dimension_scores: list[DimensionScoreRequest] = Field(default_factory=list)
    content_comparisons: list[ContentComparisonRequest] = Field(default_factory=list)
    notes: str | None = None
    min_rivalry: float = Field(default=0.25, ge=0.0, le=1.0)


class DiscoveredCompetitorResponse(BaseModel):
    name: str
    domain: str
    categories: list[str]
    discovery_method: str
    signals: dict[str, float]
    overall_rivalry_score: float
    is_direct_business_competitor: bool
    discovery_rationale: str


class DeltaResponse(BaseModel):
    competitor_domain: str
    competitor_name: str
    dimension: str
    where_stronger: str
    why_stronger: str
    gap_difficulty: str
    gap_difficulty_score: float
    how_to_close: str
    how_to_leapfrog: str
    client_score: float
    competitor_score: float
    delta: float
    evidence: str | None = None


class ContentDiffResponse(BaseModel):
    competitor_domain: str
    competitor_url: str
    client_url: str | None
    dimension: str
    competitor_advantage: bool
    client_score: float
    competitor_score: float
    evidence_summary: str
    differentiated_recommendation: str
    copy_rejected: bool


class StrategyResponse(BaseModel):
    competitor_domain: str | None
    priority: str
    title: str
    rationale: str
    differentiated_moves: list[str]
    leapfrog_angle: str
    copy_competitor_content_rejected: bool
    forbidden_modes_note: str


class DeepCompetitorResponse(BaseModel):
    analysis_id: str
    client_brand: str
    client_domain: str
    methodology: str
    copy_competitor_content_rejected: bool
    competitors: list[DiscoveredCompetitorResponse]
    deltas: list[DeltaResponse]
    content_diffs: list[ContentDiffResponse]
    strategies: list[StrategyResponse]
    category_breakdown: dict[str, int]
    example_discovery: list[dict]
    example_delta: dict | None


class DeepCompetitorCatalogResponse(BaseModel):
    competitor_categories: list[str]
    discovery_signals: list[str]
    content_compare_dimensions: list[str]
    forbidden_recommendation_modes: list[str]
    methodology_note: str
