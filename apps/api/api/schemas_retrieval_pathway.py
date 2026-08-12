"""Retrieval Pathway Intelligence API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ObservedEvidenceRequest(BaseModel):
    page_reachable: bool | None = None
    http_status: int | None = None
    robots_blocked: bool | None = None
    noindex: bool | None = None
    topical_relevance: float | None = Field(default=None, ge=0.0, le=1.0)
    entity_relationship_strength: float | None = Field(default=None, ge=0.0, le=1.0)
    competitor_page_strength: float | None = Field(default=None, ge=0.0, le=1.0)
    source_freshness_days: int | None = Field(default=None, ge=0)
    competitor_fresher: bool | None = None
    extractability: float | None = Field(default=None, ge=0.0, le=1.0)
    supporting_evidence_strength: float | None = Field(default=None, ge=0.0, le=1.0)
    third_party_corroboration: float | None = Field(default=None, ge=0.0, le=1.0)
    content_appeared_retrieved: bool | None = None
    brand_mentioned: bool | None = None
    page_cited: bool | None = None
    citation_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    mention_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    observation_sample_size: int = Field(default=0, ge=0)
    evidence_confidence: float = Field(default=0.55, ge=0.0, le=1.0)


class RetrievalPathwayRequest(BaseModel):
    website_id: str
    workspace_id: str | None = None
    name: str = Field(min_length=2, max_length=255)
    query_cluster: str = Field(min_length=1, max_length=255)
    client_brand: str = Field(min_length=1, max_length=255)
    target_url: str = Field(min_length=3, max_length=2048)
    evidence: ObservedEvidenceRequest
    competitor_urls: list[str] = Field(default_factory=list)
    notes: str | None = None


class CauseResponse(BaseModel):
    cause_code: str
    estimated_likelihood: float
    likelihood_band: str
    uncertainty: str
    supporting_evidence: list[str]
    contrary_evidence: list[str]
    rationale: str
    is_primary: bool


class BottleneckResponse(BaseModel):
    bottleneck_stage: str
    headline: str
    retrieval_probability_band: str
    citation_selection_band: str
    estimated_retrieval_likelihood: float
    estimated_selection_likelihood: float
    interpretation: str
    recommended_investigation: str
    uncertainty: str
    disclaimer: str


class RetrievalPathwayResponse(BaseModel):
    analysis_id: str
    query_cluster: str
    client_brand: str
    target_url: str
    target_domain: str
    methodology: str
    proprietary_ranking_access_claimed: bool
    disclaimer: str
    estimated_retrieval_likelihood: float
    estimated_selection_likelihood: float
    retrieval_likelihood_band: str
    selection_likelihood_band: str
    overall_uncertainty: str
    causes: list[CauseResponse]
    bottleneck: BottleneckResponse
    evidence_summary: list[dict]
    example_display: dict


class RetrievalPathwayCatalogResponse(BaseModel):
    forensic_causes: list[str]
    likelihood_bands: list[str]
    uncertainty_bands: list[str]
    bottleneck_stages: list[str]
    methodology: str
    disclaimer: str
    terminology: list[str]
