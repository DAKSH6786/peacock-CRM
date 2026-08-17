"""Deep Competitor Intelligence — discovery, deltas, reverse content, leapfrog."""

from db_models.deep_competitor import (
    COMPETITOR_CATEGORIES,
    CONTENT_COMPARE_DIMENSIONS,
    DISCOVERY_SIGNALS,
    FORBIDDEN_RECOMMENDATION_MODES,
)
from deep_competitor.delta import compute_deltas
from deep_competitor.discovery import discover_competitors
from deep_competitor.models import DeepCompetitorReport, DeepCompetitorSpec
from deep_competitor.reverse_content import reverse_engineer_content
from deep_competitor.service import DeepCompetitorService
from deep_competitor.strategy import generate_differentiated_strategies

__all__ = [
    "COMPETITOR_CATEGORIES",
    "CONTENT_COMPARE_DIMENSIONS",
    "DISCOVERY_SIGNALS",
    "FORBIDDEN_RECOMMENDATION_MODES",
    "DeepCompetitorReport",
    "DeepCompetitorService",
    "DeepCompetitorSpec",
    "compute_deltas",
    "discover_competitors",
    "generate_differentiated_strategies",
    "reverse_engineer_content",
]
