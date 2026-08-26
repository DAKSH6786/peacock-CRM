"""Peacock GEO Intelligence API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProviderResponseSchema(BaseModel):
    engine_code: str
    engine_name: str
    provider_code: str
    content: str
    simulated: bool
    model: str | None = None
    latency_ms: int = 0
    error: str | None = None


class KeywordSignalSchema(BaseModel):
    phrase: str
    frequency: int
    engine_codes: list[str] = Field(default_factory=list)


class EntityMentionSchema(BaseModel):
    name: str
    kind: str
    frequency: int
    engine_codes: list[str] = Field(default_factory=list)


class QuestionSignalSchema(BaseModel):
    question: str
    engine_code: str


class CitationSignalSchema(BaseModel):
    url: str
    domain: str
    source_class: str
    engine_code: str


class TerminologyProfileSchema(BaseModel):
    engine_code: str
    engine_name: str
    top_terms: list[str] = Field(default_factory=list)


class TopicSignalSchema(BaseModel):
    topic: str
    associated_entity: str | None = None
    frequency: int


class PlatformRecommendationSchema(BaseModel):
    engine_code: str
    engine_name: str
    platform_label: str
    opportunities: list[str] = Field(default_factory=list)
    signal_strength: str


class GeoIntelligenceResponse(BaseModel):
    client_brand: str
    research_prompt: str
    competitors: list[str] = Field(default_factory=list)
    site_topics: list[str] = Field(default_factory=list)
    provider_responses: list[ProviderResponseSchema] = Field(default_factory=list)
    keywords: list[KeywordSignalSchema] = Field(default_factory=list)
    entities: list[EntityMentionSchema] = Field(default_factory=list)
    questions: list[QuestionSignalSchema] = Field(default_factory=list)
    citations: list[CitationSignalSchema] = Field(default_factory=list)
    competitor_mentions: list[EntityMentionSchema] = Field(default_factory=list)
    terminology_by_engine: list[TerminologyProfileSchema] = Field(default_factory=list)
    top_brand_topics: list[TopicSignalSchema] = Field(default_factory=list)
    missing_topics: list[str] = Field(default_factory=list)
    recommendations: list[PlatformRecommendationSchema] = Field(default_factory=list)
    disclaimer: str
    methodology_note: str


class GeoIntelligenceAnalysisRequest(BaseModel):
    client_brand: str = "Acme"
    competitors: list[str] = Field(default_factory=list)
    site_topics: list[str] = Field(default_factory=list)
    research_prompt: str | None = None
    engine_codes: list[str] | None = None
    client_domains: list[str] = Field(default_factory=list)
    competitor_domains: list[str] = Field(default_factory=list)


class AiPluginStatusSchema(BaseModel):
    engine_code: str
    engine_name: str
    provider_code: str
    live: bool


class AiGatewayCatalogResponse(BaseModel):
    plugins: list[AiPluginStatusSchema]
    disclaimer: str
    methodology_note: str
