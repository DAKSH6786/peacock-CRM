"""Peacock AI Visibility Command Center.

Generates realistic, intent-varied queries (informational, comparison,
purchase, commercial) about a brand's category, broadcasts them to every
configured AI plugin through the Peacock AI Gateway, and reports brand
mentions, competitor mentions, recommendation position, citations, brand
attributes, sentiment, share of answer, and AI share of voice — per platform
and aggregated ("universal"). Never fabricates a number for a plugin with no
live API key.
"""

from ai_visibility.models import (
    AI_VISIBILITY_DISCLAIMER,
    AiVisibilityCommandCenterReport,
    EngineVisibilityReport,
    GeneratedQuery,
    QueryObservation,
)
from ai_visibility.queries import build_queries
from ai_visibility.service import run_ai_visibility_scan

__all__ = [
    "AI_VISIBILITY_DISCLAIMER",
    "AiVisibilityCommandCenterReport",
    "EngineVisibilityReport",
    "GeneratedQuery",
    "QueryObservation",
    "build_queries",
    "run_ai_visibility_scan",
]
