"""Typed specs for Peacock Citation Graph."""

from __future__ import annotations

from dataclasses import dataclass, field

from citation_graph.opportunity import SourceOpportunity
from citation_graph.scoring import DEFAULT_CIS_WEIGHTS, DomainInfluenceBreakdown


@dataclass(frozen=True)
class CitationSpec:
    cited_url: str
    prominence: float = 0.5
    freshness_days: int | None = None
    authority_proxy: float | None = None
    position_in_answer: int | None = None
    source_class: str | None = None


@dataclass(frozen=True)
class EntityMentionSpec:
    entity_name: str
    mentioned: bool = True
    is_client: bool = False
    is_competitor: bool = False
    position_hint: int | None = None


@dataclass(frozen=True)
class ObservationSpec:
    engine_code: str
    prompt_text: str
    answer_excerpt: str = ""
    topic_label: str | None = None
    model_code: str | None = None
    citations: list[CitationSpec] = field(default_factory=list)
    entities: list[EntityMentionSpec] = field(default_factory=list)
    # When citations empty, URLs are extracted from answer_excerpt


@dataclass
class CitationGraphSpec:
    website_id: str
    name: str
    topic_cluster: str
    client_brand: str
    competitor_brands: list[str] = field(default_factory=list)
    client_domains: list[str] = field(default_factory=list)
    competitor_domains: list[str] = field(default_factory=list)
    observations: list[ObservationSpec] = field(default_factory=list)
    notes: str | None = None
    cis_weights: dict[str, float] | None = None


@dataclass(frozen=True)
class PathwayView:
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


@dataclass(frozen=True)
class CitationGraphReport:
    analysis_id: str
    topic_cluster: str
    client_brand: str
    methodology: str
    observation_count: int
    citation_count: int
    domain_count: int
    pathway_count: int
    domains: list[DomainInfluenceBreakdown]
    hubs: list[DomainInfluenceBreakdown]
    pathways_sample: list[PathwayView]
    opportunities: list[SourceOpportunity]
    source_class_breakdown: dict[str, int]
    cis_weights: dict[str, float]
    manipulative_spam_rejected: bool = True

    def most_influential_domains(self, *, limit: int = 10) -> list[DomainInfluenceBreakdown]:
        return list(self.domains[:limit])
