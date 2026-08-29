"""Citation Graph API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CitationRequest(BaseModel):
    cited_url: str = Field(min_length=3, max_length=2048)
    prominence: float = Field(default=0.5, ge=0.0, le=1.0)
    freshness_days: int | None = Field(default=None, ge=0)
    authority_proxy: float | None = Field(default=None, ge=0.0, le=1.0)
    position_in_answer: int | None = Field(default=None, ge=1)
    source_class: str | None = Field(default=None, max_length=64)


class EntityMentionRequest(BaseModel):
    entity_name: str = Field(min_length=1, max_length=255)
    mentioned: bool = True
    is_client: bool = False
    is_competitor: bool = False
    position_hint: int | None = None


class ObservationRequest(BaseModel):
    engine_code: str = Field(min_length=1, max_length=64)
    prompt_text: str = Field(min_length=1, max_length=4000)
    answer_excerpt: str = Field(default="", max_length=50000)
    topic_label: str | None = Field(default=None, max_length=255)
    model_code: str | None = Field(default=None, max_length=128)
    citations: list[CitationRequest] = Field(default_factory=list)
    entities: list[EntityMentionRequest] = Field(default_factory=list)


class CitationGraphRequest(BaseModel):
    website_id: str
    workspace_id: str | None = None
    name: str = Field(min_length=2, max_length=255)
    topic_cluster: str = Field(min_length=1, max_length=255)
    client_brand: str = Field(min_length=1, max_length=255)
    competitor_brands: list[str] = Field(default_factory=list)
    client_domains: list[str] = Field(default_factory=list)
    competitor_domains: list[str] = Field(default_factory=list)
    observations: list[ObservationRequest] = Field(min_length=1)
    notes: str | None = None
    cis_weights: dict[str, float] | None = None


class DomainScoreResponse(BaseModel):
    cited_domain: str
    source_class: str
    is_citation_hub: bool
    is_competitor_owned: bool
    is_client_owned: bool
    citation_influence_score: float
    components: dict[str, float]
    explanations: dict[str, str]
    citation_count: int
    engine_count: int
    page_count: int
    observation_share: float
    client_mention_rate: float
    competitor_mention_rate: float
    top_competitor_name: str | None = None
    top_competitor_mention_rate: float = 0.0


class PathwayResponse(BaseModel):
    engine_code: str
    prompt_fingerprint: str
    answer_id: str
    cited_url: str
    cited_domain: str
    page_path: str | None
    entity_name: str | None
    topic_label: str
    source_class: str
    pathway_key: str


class OpportunityResponse(BaseModel):
    cited_domain: str
    source_class: str
    opportunity_type: str
    priority: str
    domain_answer_influence_pct: float
    client_mention_pct: float
    top_competitor_name: str | None
    top_competitor_mention_pct: float
    title: str
    rationale: str
    recommended_actions: list[str]
    manipulative_spam_rejected: bool


class CitationGraphResponse(BaseModel):
    analysis_id: str
    topic_cluster: str
    client_brand: str
    methodology: str
    observation_count: int
    citation_count: int
    domain_count: int
    pathway_count: int
    pathway_chain: list[str]
    domains: list[DomainScoreResponse]
    hubs: list[DomainScoreResponse]
    pathways_sample: list[PathwayResponse]
    opportunities: list[OpportunityResponse]
    source_class_breakdown: dict[str, int]
    cis_weights: dict[str, float]
    manipulative_spam_rejected: bool
    example_opportunity: dict | None = None


class CitationGraphCatalogResponse(BaseModel):
    pathway_chain: list[str]
    source_classes: list[str]
    cis_components: list[str]
    default_cis_weights: dict[str, float]
    opportunity_types: list[str]
    forbidden_tactics: list[str]
    methodology_note: str
