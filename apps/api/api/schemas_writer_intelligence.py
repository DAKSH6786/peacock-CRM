"""Writer Intelligence 2.0 API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class WriterCandidateRequest(BaseModel):
    writer_key: str = Field(min_length=1, max_length=128)
    display_name: str = Field(min_length=1, max_length=255)
    dna_traits: dict[str, float] = Field(default_factory=dict)
    dna_evidence: dict[str, str] = Field(default_factory=dict)
    subject_tags: list[str] = Field(default_factory=list)
    style_notes: str | None = None
    tone_notes: str | None = None
    prior_clients: list[str] = Field(default_factory=list)
    prior_industries: list[str] = Field(default_factory=list)
    prior_topics: list[str] = Field(default_factory=list)
    prior_audiences: list[str] = Field(default_factory=list)


class ArticleHistoryRequest(BaseModel):
    article_key: str = Field(min_length=1, max_length=128)
    writer_key: str = Field(min_length=1, max_length=128)
    client_key: str = Field(min_length=1, max_length=128)
    industry: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    audience: str | None = None
    title: str | None = None
    approval: float | None = None
    revision_rounds: float | None = None
    ranking: float | None = None
    impressions: float | None = None
    ai_citations: float | None = None
    engagement: float | None = None
    links_earned: float | None = None
    conversion: float | None = None


class DecisionContextRequest(BaseModel):
    client_brand: str = Field(min_length=1, max_length=255)
    industry: str = Field(min_length=1, max_length=255)
    topic: str = Field(min_length=1, max_length=512)
    audience: str = Field(min_length=1, max_length=512)
    required_traits: list[str] = Field(default_factory=list)
    preferred_tone: str | None = None
    needs_seo: bool = True
    needs_aeo: bool = True
    needs_geo: bool = True


class WriterIntelligenceRequest(BaseModel):
    website_id: str
    workspace_id: str | None = None
    name: str = Field(min_length=2, max_length=255)
    context: DecisionContextRequest
    writers: list[WriterCandidateRequest] = Field(min_length=1)
    history: list[ArticleHistoryRequest] = Field(default_factory=list)
    notes: str | None = None


class DnaTraitResponse(BaseModel):
    trait_code: str
    score: float
    evidence: str


class WriterDnaResponse(BaseModel):
    writer_key: str
    display_name: str
    traits: list[DnaTraitResponse]
    dna_composite_score: float
    dna_summary: str


class RecommendationResponse(BaseModel):
    writer_key: str
    display_name: str
    rank: int
    predicted_outcome_score: float
    dna_fit_score: float
    topic_fit_score: float
    client_fit_score: float
    audience_fit_score: float
    historical_outcome_score: float
    similarity_score_unused: float | None
    similarity_not_used_as_primary: bool
    rationale: str
    decision_answer: str


class OutcomeNodeResponse(BaseModel):
    node_kind: str
    node_key: str
    label: str
    attributes: dict


class OutcomeEdgeResponse(BaseModel):
    edge_type: str
    from_node_kind: str
    from_node_key: str
    to_node_kind: str
    to_node_key: str
    weight: float


class PerformanceRecordResponse(BaseModel):
    article_key: str
    writer_key: str
    client_key: str
    industry: str
    topic: str
    metrics: dict
    composite_outcome: float


class WriterIntelligenceResponse(BaseModel):
    analysis_id: str
    name: str
    client_brand: str
    industry: str
    topic: str
    audience: str
    methodology: str
    decision_question: str
    methodology_note: str
    similarity_only_rejected: bool
    similarity_rejection_note: str
    dna_profiles: list[WriterDnaResponse]
    recommendations: list[RecommendationResponse]
    outcome_nodes: list[OutcomeNodeResponse]
    outcome_edges: list[OutcomeEdgeResponse]
    performance_records: list[PerformanceRecordResponse]
    top_writer_key: str | None
    top_outcome_score: float | None
    summary: str


class WriterIntelligenceCatalogResponse(BaseModel):
    dna_traits: list[str]
    outcome_node_kinds: list[str]
    outcome_edge_types: list[str]
    performance_metrics: list[str]
    methodology: str
    methodology_note: str
    similarity_only_rejected: bool
    similarity_rejection_note: str
    decision_question_template: str
