"""Peacock Site Intelligence — the enterprise SEO + GEO reporting engine.

    Crawl -> Understand -> Benchmark -> Query LLMs -> Extract AI Signals ->
    Compare Competitors -> Identify Gaps -> Prioritize Opportunities ->
    Generate Exact Fixes -> Track Improvement

Composes the real crawler, the real SEO/AEO engines, and the Peacock AI
Gateway + GEO Intelligence Layer with new deterministic scoring (GEO Score,
Information Gain, page-level opportunities, Peacock Impact Score, LLM
Keyword Map, competitor diff, exact-fix drafts). Nothing here fabricates a
metric — anything not backed by a real signal is reported as
"Data unavailable".
"""

from site_intelligence.models import (
    CONFIDENCE_EXPERIMENTAL,
    CONFIDENCE_HIGH,
    CONFIDENCE_MEDIUM,
    DATA_UNAVAILABLE,
    PRIORITY_CRITICAL,
    PRIORITY_HIGH,
    PRIORITY_LOW,
    PRIORITY_MEDIUM,
    CompetitiveAssociationGap,
    CompetitorComparison,
    DataAvailability,
    ExactFix,
    ExplainedScore,
    GeoScoreBreakdown,
    ImpactAction,
    LlmKeywordMap,
    LlmKeywordMapEntry,
    PageOpportunity,
    PerLlmGeoScore,
    ScoreFactor,
    SiteIntelligenceReport,
)
from site_intelligence.report import DEFAULT_MAX_PAGES, run_site_intelligence_report

__all__ = [
    "CONFIDENCE_EXPERIMENTAL",
    "CONFIDENCE_HIGH",
    "CONFIDENCE_MEDIUM",
    "DATA_UNAVAILABLE",
    "DEFAULT_MAX_PAGES",
    "PRIORITY_CRITICAL",
    "PRIORITY_HIGH",
    "PRIORITY_LOW",
    "PRIORITY_MEDIUM",
    "CompetitiveAssociationGap",
    "CompetitorComparison",
    "DataAvailability",
    "ExactFix",
    "ExplainedScore",
    "GeoScoreBreakdown",
    "ImpactAction",
    "LlmKeywordMap",
    "LlmKeywordMapEntry",
    "PageOpportunity",
    "PerLlmGeoScore",
    "ScoreFactor",
    "SiteIntelligenceReport",
    "run_site_intelligence_report",
]
