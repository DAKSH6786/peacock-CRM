"""Peacock Impact Score — rank opportunities by expected business value, not raw severity.

    Opportunity Impact = Visibility Opportunity × Business Intent ×
                          Competitive Gap × Fix Confidence ÷ Implementation Difficulty

Every factor below is derived from real, already-measured signals (page
scores, crawl depth, detected commercial keywords, LLM Keyword Map gaps) —
never an arbitrary AI-generated number.
"""

from __future__ import annotations

import re

from geo_intelligence.models import GeoExtractionResult, PlatformRecommendation

from site_intelligence.models import (
    CONFIDENCE_EXPERIMENTAL,
    CONFIDENCE_HIGH,
    CONFIDENCE_MEDIUM,
    ImpactAction,
    LlmKeywordMap,
    PageOpportunity,
)

_DIFFICULTY_DIVISOR = {"Low": 1.0, "Medium": 2.0, "High": 3.0}
_PRIORITY_FIX_CONFIDENCE = {
    "Critical": CONFIDENCE_HIGH,
    "High": CONFIDENCE_HIGH,
    "Medium": CONFIDENCE_MEDIUM,
    "Low": CONFIDENCE_MEDIUM,
}
_CONFIDENCE_FACTOR = {CONFIDENCE_HIGH: 0.9, CONFIDENCE_MEDIUM: 0.65, CONFIDENCE_EXPERIMENTAL: 0.4}
_COMMERCIAL_KEYWORDS_RE = re.compile(
    r"\b(pricing|buy|demo|enterprise|security|compliance|plans?|contact sales|request a quote)\b",
    re.IGNORECASE,
)


def _business_intent(page: PageOpportunity, depth_by_url: dict[str, int]) -> float:
    depth = depth_by_url.get(page.url, 1)
    base = 1.0 if depth == 0 else (0.7 if depth == 1 else 0.4)
    text_blob = f"{page.title or ''} {' '.join(page.whats_wrong)}"
    if _COMMERCIAL_KEYWORDS_RE.search(text_blob):
        base = min(1.0, base + 0.2)
    return base


def _competitive_gap(page: PageOpportunity, missing_topics: list[str], page_text_tokens: set[str]) -> float:
    if not missing_topics:
        return 0.3
    uncovered = [t for t in missing_topics if not any(w in page_text_tokens for w in t.split())]
    return round(min(1.0, 0.3 + 0.7 * (len(uncovered) / max(1, len(missing_topics)))), 3)


def peacock_impact_score(
    *,
    visibility_opportunity: float,
    business_intent: float,
    competitive_gap: float,
    fix_confidence: float,
    implementation_difficulty: float,
) -> float:
    raw = (
        visibility_opportunity
        * business_intent
        * competitive_gap
        * fix_confidence
        / max(0.5, implementation_difficulty)
    )
    return round(min(100.0, raw * 100.0), 2)


def score_page_opportunities(
    pages: list[PageOpportunity],
    *,
    depth_by_url: dict[str, int],
    page_tokens_by_url: dict[str, set[str]],
    missing_topics: list[str],
) -> None:
    """Mutates each PageOpportunity in place, filling in ``peacock_impact_score``."""
    for page in pages:
        avg_score = (page.seo_score + page.aeo_score + page.geo_score) / 3.0
        visibility_opportunity = round((100.0 - avg_score) / 100.0, 3)
        business_intent = round(_business_intent(page, depth_by_url), 3)
        competitive_gap = _competitive_gap(page, missing_topics, page_tokens_by_url.get(page.url, set()))
        fix_confidence = _CONFIDENCE_FACTOR[_PRIORITY_FIX_CONFIDENCE.get(page.priority, CONFIDENCE_MEDIUM)]
        difficulty = _DIFFICULTY_DIVISOR.get(page.difficulty, 2.0)
        page.peacock_impact_score = peacock_impact_score(
            visibility_opportunity=visibility_opportunity,
            business_intent=business_intent,
            competitive_gap=competitive_gap,
            fix_confidence=fix_confidence,
            implementation_difficulty=difficulty,
        )


def build_top_actions(
    *,
    pages: list[PageOpportunity],
    keyword_map: LlmKeywordMap,
    extraction: GeoExtractionResult,
    recommendations: list[PlatformRecommendation],
    limit: int = 10,
) -> list[ImpactAction]:
    actions: list[ImpactAction] = []

    llms_by_missing_topic: dict[str, list[str]] = {}
    for rec in recommendations:
        for opp in rec.opportunities:
            for topic in extraction.missing_topics:
                if topic.lower() in opp.lower():
                    llms_by_missing_topic.setdefault(topic, []).append(rec.engine_name)

    for topic in extraction.missing_topics[:5]:
        llms = sorted(set(llms_by_missing_topic.get(topic, [])))
        competitors_winning = sum(
            1 for gap in keyword_map.competitive_association_gaps if topic in gap.missing_topics
        )
        impact = peacock_impact_score(
            visibility_opportunity=0.75,
            business_intent=0.8,
            competitive_gap=0.9 if competitors_winning else 0.5,
            fix_confidence=_CONFIDENCE_FACTOR[CONFIDENCE_EXPERIMENTAL],
            implementation_difficulty=3.0,
        )
        actions.append(
            ImpactAction(
                rank=0,
                title=f'Create a dedicated content cluster covering "{topic}"',
                impact_score=impact,
                difficulty="High",
                seo_opportunity="Medium",
                geo_opportunity="Very High" if llms else "High",
                competitors_winning=competitors_winning,
                llms_showing_gap=llms or [r.engine_name for r in recommendations][:3],
                detail=(
                    f'AI platforms associate "{topic}" with this category, and it is not represented in '
                    "the crawled site content. This is a GEO opportunity / AI visibility signal, not a "
                    "guaranteed ranking outcome."
                ),
                confidence=CONFIDENCE_EXPERIMENTAL,
                day_bucket=90,
            )
        )

    for page in pages:
        if page.peacock_impact_score <= 0:
            continue
        difficulty_bucket = {"Low": 30, "Medium": 60, "High": 90}.get(page.difficulty, 60)
        actions.append(
            ImpactAction(
                rank=0,
                title=f"Fix: {page.whats_wrong[0]}" if page.whats_wrong else f"Improve {page.url}",
                impact_score=page.peacock_impact_score,
                difficulty=page.difficulty,
                seo_opportunity="High" if page.seo_score < 60 else "Medium",
                geo_opportunity="High" if page.geo_score < 60 else "Medium",
                competitors_winning=0,
                llms_showing_gap=[],
                detail=f"{page.url} — {page.why_it_matters[0] if page.why_it_matters else ''}",
                confidence=page.confidence,
                day_bucket=difficulty_bucket,
            )
        )

    actions.sort(key=lambda a: a.impact_score, reverse=True)
    top = actions[:limit]
    for i, action in enumerate(top, start=1):
        action.rank = i
    return top


def thirty_sixty_ninety_plan(actions: list[ImpactAction]) -> dict[str, list[ImpactAction]]:
    plan: dict[str, list[ImpactAction]] = {"30_day": [], "60_day": [], "90_day": []}
    for action in actions:
        key = f"{action.day_bucket}_day"
        plan.setdefault(key, []).append(action)
    return plan
