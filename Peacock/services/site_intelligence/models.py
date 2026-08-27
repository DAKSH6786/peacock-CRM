"""Evidence-first result models for the Peacock Site Intelligence engine.

Every score in this package is built from a list of ``ScoreFactor`` records —
metric, observed value, benchmark, weight, contribution, and the literal
evidence that produced it — so the frontend can always answer
"Why did I get this score?" instead of showing an opaque number.

Nothing here invents a value. Where a real data source (backlinks, search
volume, CrUX/PageSpeed field data, verified competitor discovery) is not
configured, callers must set the corresponding field to ``None`` /
``DATA_UNAVAILABLE`` rather than fabricate a plausible-looking number.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

DATA_UNAVAILABLE = "Data unavailable"

CONFIDENCE_HIGH = "high"
CONFIDENCE_MEDIUM = "medium"
CONFIDENCE_EXPERIMENTAL = "experimental"

PRIORITY_CRITICAL = "Critical"
PRIORITY_HIGH = "High"
PRIORITY_MEDIUM = "Medium"
PRIORITY_LOW = "Low"


@dataclass(slots=True)
class ScoreFactor:
    """One measurable ingredient of a score — always traceable to evidence."""

    metric: str
    observed_value: Any
    benchmark: Any
    weight: float
    score_contribution: float
    evidence: str
    confidence: str = CONFIDENCE_HIGH

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ExplainedScore:
    """A 0-100 score plus the exact factors that produced it."""

    score: float
    label: str
    factors: list[ScoreFactor] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "label": self.label,
            "summary": self.summary,
            "factors": [f.to_dict() for f in self.factors],
        }


@dataclass(slots=True)
class GeoScoreBreakdown:
    """GEO Score = Entity Authority + Citation Readiness + Answerability +
    Evidence + Topical Coverage + Technical AI Accessibility + Brand Authority
    (each 0-100, equally weighted, transparently shown).
    """

    geo_score: float
    entity_authority: ExplainedScore
    citation_readiness: ExplainedScore
    answerability: ExplainedScore
    evidence: ExplainedScore
    topical_coverage: ExplainedScore
    technical_ai_accessibility: ExplainedScore
    brand_authority: ExplainedScore
    formula: str = (
        "GEO Score = (Entity Authority + Citation Readiness + Answerability + "
        "Evidence + Topical Coverage + Technical AI Accessibility + Brand "
        "Authority) / 7"
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "geo_score": self.geo_score,
            "formula": self.formula,
            "entity_authority": self.entity_authority.to_dict(),
            "citation_readiness": self.citation_readiness.to_dict(),
            "answerability": self.answerability.to_dict(),
            "evidence": self.evidence.to_dict(),
            "topical_coverage": self.topical_coverage.to_dict(),
            "technical_ai_accessibility": self.technical_ai_accessibility.to_dict(),
            "brand_authority": self.brand_authority.to_dict(),
        }


@dataclass(slots=True)
class PageOpportunity:
    """Per-page opportunity card: 8 scores + the exact-fix narrative."""

    url: str
    title: str | None
    seo_score: float
    aeo_score: float
    geo_score: float
    content_score: float
    technical_score: float
    authority_score: float
    information_gain_score: float
    ai_citation_potential: float
    whats_wrong: list[str]
    why_it_matters: list[str]
    evidence_found: list[str]
    competitor_doing_better: str
    exact_fix: list[str]
    expected_impact: str
    difficulty: str
    priority: str
    confidence: str
    peacock_impact_score: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ExactFix:
    """A concrete, non-published suggestion — never auto-applied."""

    fix_type: str
    target_url: str
    title: str
    detail: str
    draft: str
    confidence: str = CONFIDENCE_MEDIUM

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ImpactAction:
    """One ranked entry in the TOP 10 ACTIONS list."""

    rank: int
    title: str
    impact_score: float
    difficulty: str
    seo_opportunity: str
    geo_opportunity: str
    competitors_winning: int
    llms_showing_gap: list[str]
    detail: str
    confidence: str
    day_bucket: int  # 30 | 60 | 90

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class LlmKeywordMapEntry:
    term: str
    per_engine_present: dict[str, bool]
    opportunity: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "term": self.term,
            "per_engine_present": dict(self.per_engine_present),
            "opportunity": self.opportunity,
        }


@dataclass(slots=True)
class CompetitiveAssociationGap:
    competitor: str
    competitor_topics: list[str]
    brand_topics: list[str]
    missing_topics: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class LlmKeywordMap:
    entries: list[LlmKeywordMapEntry]
    universal_terms: list[str]
    platform_specific_terms: dict[str, list[str]]
    missing_semantic_entities: list[str]
    competitive_association_gaps: list[CompetitiveAssociationGap]

    def to_dict(self) -> dict[str, Any]:
        return {
            "entries": [e.to_dict() for e in self.entries],
            "universal_terms": list(self.universal_terms),
            "platform_specific_terms": {k: list(v) for k, v in self.platform_specific_terms.items()},
            "missing_semantic_entities": list(self.missing_semantic_entities),
            "competitive_association_gaps": [g.to_dict() for g in self.competitive_association_gaps],
        }


@dataclass(slots=True)
class CompetitorComparison:
    competitor_url: str | None
    available: bool
    reason_unavailable: str | None
    seo_visibility: str
    content_coverage: str
    keyword_coverage: str
    entity_coverage: str
    backlink_signals: str
    topical_authority: str
    structured_data: str
    question_coverage: str
    ai_mentions: str
    ai_citations: str
    cited_domain_overlap: str
    source_authority: str
    content_freshness: str
    page_depth: str
    information_gain_comparison: str
    why_competitor_is_winning: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PerLlmGeoScore:
    """ChatGPT/Gemini/Claude/Perplexity/DeepSeek GEO Score — never fabricated.

    When the plugin has no live API key, ``score`` is ``None`` and
    ``available`` is ``False`` — Peacock never computes a numeric LLM
    visibility score from placeholder/simulated text.
    """

    engine_code: str
    engine_name: str
    available: bool
    score: float | None
    reason_unavailable: str | None
    brand_mentioned: bool
    entities_mentioned: list[str]
    questions_raised: list[str]
    citations: list[str]
    opportunities: list[str]
    confidence: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DataAvailability:
    """Explicit honesty ledger — what was measured vs. not available."""

    measured: list[str]
    unavailable: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {"measured": list(self.measured), "unavailable": list(self.unavailable)}


@dataclass(slots=True)
class SiteIntelligenceReport:
    """The full SEO + GEO Report — every field traceable to real crawl/LLM evidence."""

    url: str
    brand: str
    crawled_pages_count: int
    crawl_status: str
    executive_summary: str
    peacock_visibility_score: float
    seo_score: float
    aeo_score: float
    geo_score: float
    geo_score_breakdown: GeoScoreBreakdown
    technical_health: dict[str, Any]
    ai_visibility: list[PerLlmGeoScore]
    ai_citation_presence: dict[str, Any]
    information_gain_score: float
    competitor_gap: CompetitorComparison
    llm_by_llm_visibility: list[dict[str, Any]]
    critical_issues: list[str]
    top_actions: list[ImpactAction]
    keyword_opportunities: LlmKeywordMap
    entity_opportunities: list[str]
    content_gaps: list[str]
    citation_opportunities: list[str]
    backlink_opportunities: str
    top_performing_pages: list[PageOpportunity]
    weak_pages: list[PageOpportunity]
    thirty_day_plan: list[ImpactAction]
    sixty_day_plan: list[ImpactAction]
    ninety_day_plan: list[ImpactAction]
    data_availability: DataAvailability
    pages: list[PageOpportunity]
    disclaimer: str = (
        "Scores and recommendations are derived from a real crawl of the analysed pages and, where "
        "configured, real AI plugin responses. GEO/AI-visibility signals are opportunities, not "
        "guarantees of ranking, mention, or citation on any search or AI platform."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "brand": self.brand,
            "crawled_pages_count": self.crawled_pages_count,
            "crawl_status": self.crawl_status,
            "executive_summary": self.executive_summary,
            "peacock_visibility_score": self.peacock_visibility_score,
            "seo_score": self.seo_score,
            "aeo_score": self.aeo_score,
            "geo_score": self.geo_score,
            "geo_score_breakdown": self.geo_score_breakdown.to_dict(),
            "technical_health": self.technical_health,
            "ai_visibility": [a.to_dict() for a in self.ai_visibility],
            "ai_citation_presence": self.ai_citation_presence,
            "information_gain_score": self.information_gain_score,
            "competitor_gap": self.competitor_gap.to_dict(),
            "llm_by_llm_visibility": self.llm_by_llm_visibility,
            "critical_issues": list(self.critical_issues),
            "top_actions": [a.to_dict() for a in self.top_actions],
            "keyword_opportunities": self.keyword_opportunities.to_dict(),
            "entity_opportunities": list(self.entity_opportunities),
            "content_gaps": list(self.content_gaps),
            "citation_opportunities": list(self.citation_opportunities),
            "backlink_opportunities": self.backlink_opportunities,
            "top_performing_pages": [p.to_dict() for p in self.top_performing_pages],
            "weak_pages": [p.to_dict() for p in self.weak_pages],
            "thirty_day_plan": [a.to_dict() for a in self.thirty_day_plan],
            "sixty_day_plan": [a.to_dict() for a in self.sixty_day_plan],
            "ninety_day_plan": [a.to_dict() for a in self.ninety_day_plan],
            "data_availability": self.data_availability.to_dict(),
            "pages": [p.to_dict() for p in self.pages],
            "disclaimer": self.disclaimer,
        }
