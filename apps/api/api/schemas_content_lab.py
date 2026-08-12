"""Peacock Content Lab API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProposalRequest(BaseModel):
    title: str = Field(min_length=2, max_length=512)
    slug: str = Field(min_length=1, max_length=255)
    content_format: str = Field(default="article", max_length=64)
    angle: str | None = None
    target_url: str | None = None
    seo_opportunity: float | None = Field(default=None, ge=0.0, le=1.0)
    aeo_opportunity: float | None = Field(default=None, ge=0.0, le=1.0)
    geo_opportunity: float | None = Field(default=None, ge=0.0, le=1.0)
    ai_citation_opportunity: float | None = Field(default=None, ge=0.0, le=1.0)
    business_value: float | None = Field(default=None, ge=0.0, le=1.0)
    audience_relevance: float | None = Field(default=None, ge=0.0, le=1.0)
    competitor_gap: float | None = Field(default=None, ge=0.0, le=1.0)
    originality_opportunity: float | None = Field(default=None, ge=0.0, le=1.0)
    topical_authority_impact: float | None = Field(default=None, ge=0.0, le=1.0)
    conversion_potential: float | None = Field(default=None, ge=0.0, le=1.0)
    backlink_potential: float | None = Field(default=None, ge=0.0, le=1.0)
    entity_impact: float | None = Field(default=None, ge=0.0, le=1.0)
    effort: float | None = Field(default=None, ge=0.0, le=1.0)
    time_sensitivity: float | None = Field(default=None, ge=0.0, le=1.0)
    info_gain_penalties: dict[str, float] = Field(default_factory=dict)
    info_gain_rewards: dict[str, float] = Field(default_factory=dict)
    citability_signals: dict[str, float] = Field(default_factory=dict)
    moat_override: float | None = Field(default=None, ge=0.0, le=100.0)
    outline_text: str | None = None


class ContentLabRequest(BaseModel):
    website_id: str
    workspace_id: str | None = None
    name: str = Field(min_length=2, max_length=255)
    client_brand: str = Field(min_length=1, max_length=255)
    topic_cluster: str | None = None
    proposals: list[ProposalRequest] = Field(min_length=1)
    notes: str | None = None


class InfoGainSignalResponse(BaseModel):
    signal_code: str
    polarity: str
    strength: float
    evidence: str


class CitabilityComponentResponse(BaseModel):
    component_code: str
    score: float
    explanation: str


class ProposalScoreResponse(BaseModel):
    title: str
    slug: str
    content_format: str
    angle: str | None
    target_url: str | None
    lab_priority_score: float
    opportunities: dict[str, float]
    information_gain_score: float
    content_moat_score: float
    generative_citability_score: float
    info_gain_signals: list[InfoGainSignalResponse]
    citability_components: list[CitabilityComponentResponse]
    moat_rationale: str
    recommendation_summary: str
    citability_is_proprietary_estimate: bool
    citability_disclaimer: str


class ContentLabResponse(BaseModel):
    analysis_id: str
    client_brand: str
    methodology: str
    citability_is_proprietary_estimate: bool
    citability_disclaimer: str
    proposals: list[ProposalScoreResponse]
    example_moat: list[dict]
    top_recommendation: dict | None


class ContentLabCatalogResponse(BaseModel):
    opportunity_dimensions: list[str]
    info_gain_penalties: list[str]
    info_gain_rewards: list[str]
    moat_format_priors: dict[str, int]
    citability_components: list[str]
    citability_disclaimer: str
    methodology_note: str
