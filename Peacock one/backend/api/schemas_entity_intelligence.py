"""Entity Intelligence API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class EntityNodeRequest(BaseModel):
    canonical_name: str = Field(min_length=1, max_length=255)
    entity_type: str = Field(min_length=1, max_length=64)
    is_client: bool = False
    is_competitor: bool = False
    aliases: list[str] = Field(default_factory=list)
    description: str | None = None
    ownership_brand: str | None = None


class AssociationRequest(BaseModel):
    source_entity_name: str = Field(min_length=1, max_length=255)
    source_entity_type: str = Field(min_length=1, max_length=64)
    target_entity_name: str = Field(min_length=1, max_length=255)
    target_entity_type: str = Field(min_length=1, max_length=64)
    is_client_owned: bool = False
    is_competitor_owned: bool = False
    co_occurrence: float = Field(default=0.0, ge=0.0, le=1.0)
    semantic_proximity: float = Field(default=0.0, ge=0.0, le=1.0)
    ownership_signal: float = Field(default=0.0, ge=0.0, le=1.0)
    citation_linkage: float = Field(default=0.0, ge=0.0, le=1.0)
    topical_centrality: float = Field(default=0.0, ge=0.0, le=1.0)
    recency: float = Field(default=0.5, ge=0.0, le=1.0)
    cross_source_consistency: float = Field(default=0.0, ge=0.0, le=1.0)
    observation_count: int = Field(default=0, ge=0)


class EntityIntelligenceRequest(BaseModel):
    website_id: str
    workspace_id: str | None = None
    name: str = Field(min_length=2, max_length=255)
    client_brand: str = Field(min_length=1, max_length=255)
    industry: str | None = None
    entities: list[EntityNodeRequest] = Field(default_factory=list)
    associations: list[AssociationRequest] = Field(default_factory=list)
    target_concepts: list[str] = Field(default_factory=list)
    notes: str | None = None
    association_weights: dict[str, float] | None = None


class AssociationResponse(BaseModel):
    source_entity_name: str
    source_entity_type: str
    target_entity_name: str
    target_entity_type: str
    is_client_owned: bool
    is_competitor_owned: bool
    association_strength: float
    components: dict[str, float]
    explanations: dict[str, str]
    observation_count: int


class EntityGapResponse(BaseModel):
    target_concept: str
    target_entity_type: str
    client_brand: str
    client_association: float
    competitor_associations: dict[str, float]
    leading_competitor_name: str | None
    leading_competitor_association: float
    gap_size: float
    severity: str
    summary: str


class StrategyResponse(BaseModel):
    target_concept: str
    action_type: str
    priority: str
    title: str
    rationale: str
    recommended_moves: list[str]
    expected_association_lift: float


class EntityIntelligenceResponse(BaseModel):
    analysis_id: str
    client_brand: str
    methodology: str
    entity_count: int
    association_count: int
    associations: list[AssociationResponse]
    client_ownership: list[AssociationResponse]
    gaps: list[EntityGapResponse]
    strategies: list[StrategyResponse]
    association_weights: dict[str, float]
    example_ownership: list[dict]
    example_gap: dict | None


class EntityIntelligenceCatalogResponse(BaseModel):
    entity_types: list[str]
    association_components: list[str]
    default_weights: dict[str, float]
    strategy_actions: list[str]
    methodology_note: str
