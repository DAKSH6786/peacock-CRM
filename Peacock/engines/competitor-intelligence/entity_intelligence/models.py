"""Typed specs for Peacock Entity Intelligence."""

from __future__ import annotations

from dataclasses import dataclass, field

from entity_intelligence.scoring import (
    DEFAULT_ASSOCIATION_WEIGHTS,
    AssociationScore,
    AssociationSignal,
    EntityGapResult,
)
from entity_intelligence.strategy import EntityStrategy


@dataclass(frozen=True)
class EntityNodeSpec:
    canonical_name: str
    entity_type: str
    is_client: bool = False
    is_competitor: bool = False
    aliases: list[str] = field(default_factory=list)
    description: str | None = None
    ownership_brand: str | None = None


@dataclass(frozen=True)
class AssociationInputSpec:
    """Either provide full signals or a precomputed strength hint."""

    source_entity_name: str
    source_entity_type: str
    target_entity_name: str
    target_entity_type: str
    is_client_owned: bool = False
    is_competitor_owned: bool = False
    co_occurrence: float = 0.0
    semantic_proximity: float = 0.0
    ownership_signal: float = 0.0
    citation_linkage: float = 0.0
    topical_centrality: float = 0.0
    recency: float = 0.5
    cross_source_consistency: float = 0.0
    observation_count: int = 0


@dataclass
class EntityIntelligenceSpec:
    website_id: str
    name: str
    client_brand: str
    entities: list[EntityNodeSpec] = field(default_factory=list)
    associations: list[AssociationInputSpec] = field(default_factory=list)
    target_concepts: list[str] = field(default_factory=list)
    industry: str | None = None
    notes: str | None = None
    association_weights: dict[str, float] | None = None


@dataclass(frozen=True)
class EntityIntelligenceReport:
    analysis_id: str
    client_brand: str
    methodology: str
    entity_count: int
    association_count: int
    associations: list[AssociationScore]
    client_ownership: list[AssociationScore]
    gaps: list[EntityGapResult]
    strategies: list[EntityStrategy]
    association_weights: dict[str, float]
    example_ownership: list[dict]
    example_gap: dict | None

    def ownership_for(self, brand: str) -> list[AssociationScore]:
        return [
            a
            for a in self.associations
            if a.source_entity_name.lower() == brand.lower()
        ]
