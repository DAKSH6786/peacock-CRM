"""Share of Answer API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AnswerObservationRequest(BaseModel):
    prompt_text: str = Field(min_length=1, max_length=4000)
    engine_code: str = Field(min_length=1, max_length=64)
    raw_excerpt: str = Field(min_length=1, max_length=50000)
    model_code: str | None = Field(default=None, max_length=128)
    answer_token_count: int | None = Field(default=None, ge=0)


class ShareOfAnswerRequest(BaseModel):
    website_id: str
    workspace_id: str | None = None
    name: str = Field(min_length=2, max_length=255)
    query_cluster: str = Field(min_length=1, max_length=255)
    client_brand: str = Field(min_length=1, max_length=255)
    competitor_brands: list[str] = Field(default_factory=list)
    observations: list[AnswerObservationRequest] = Field(min_length=1)
    notes: str | None = None
    indicator_weights: dict[str, float] | None = None


class BrandShareResponse(BaseModel):
    entity_name: str
    is_client: bool
    share_of_answer: float
    mention_rate: float
    avg_position_score: float
    avg_recommendation_strength: float
    avg_answer_space: float
    avg_citation_ownership: float
    avg_semantic_prominence: float
    avg_claim_balance: float
    avg_comparison_score: float
    avg_token_span_ratio: float
    token_only_share: float
    token_vs_influence_gap: float
    positive_claims_total: int
    negative_claims_total: int
    neutral_claims_total: int
    observation_sample_size: int
    mean_influence: float


class ShareOfAnswerResponse(BaseModel):
    analysis_id: str
    query_cluster: str
    client_brand: str
    methodology: str
    token_count_alone_rejected: bool
    observation_count: int
    brands: list[BrandShareResponse]
    indicator_weights: dict[str, float]
    example_display: list[dict]


class SoaCatalogResponse(BaseModel):
    indicators: list[str]
    default_weights: dict[str, float]
    comparison_outcomes: list[str]
    methodology_note: str
