"""Typed specs for Deep Competitor Intelligence."""

from __future__ import annotations

from dataclasses import dataclass, field

from deep_competitor.delta import CompetitiveDelta, DimensionScoreInput
from deep_competitor.discovery import DiscoveredCompetitor, DiscoverySignalInput
from deep_competitor.reverse_content import ContentDiffResult, ContentDimensionInput
from deep_competitor.strategy import DifferentiatedStrategy


@dataclass
class DeepCompetitorSpec:
    website_id: str
    name: str
    client_brand: str
    client_domain: str
    discovery_candidates: list[DiscoverySignalInput] = field(default_factory=list)
    dimension_scores: list[DimensionScoreInput] = field(default_factory=list)
    content_comparisons: list[ContentDimensionInput] = field(default_factory=list)
    topic_cluster: str | None = None
    notes: str | None = None
    min_rivalry: float = 0.25


@dataclass(frozen=True)
class DeepCompetitorReport:
    analysis_id: str
    client_brand: str
    client_domain: str
    methodology: str
    copy_competitor_content_rejected: bool
    competitors: list[DiscoveredCompetitor]
    deltas: list[CompetitiveDelta]
    content_diffs: list[ContentDiffResult]
    strategies: list[DifferentiatedStrategy]
    category_breakdown: dict[str, int]
    example_discovery: list[dict]
    example_delta: dict | None
