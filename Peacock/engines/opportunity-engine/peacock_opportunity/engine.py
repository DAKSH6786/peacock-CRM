"""Peacock Impact Score:

    Impact = Visibility Opportunity x Business Relevance x Competitive Gap
             x Confidence / Implementation Difficulty

An estimate for prioritisation, not a guaranteed outcome. Reuses the same
formula already validated in ``site_intelligence.impact`` — this package
exposes it as a standalone, reusable engine with the explicit fields
(action/reason/affected page/SEO/AEO/GEO/AI-visibility opportunity/business
value/competitor gap/difficulty/confidence/priority) the Growth Loop needs.
"""

from __future__ import annotations

from peacock_opportunity.models import Opportunity

_DIFFICULTY_DIVISOR = {"Low": 1.0, "Medium": 2.0, "High": 3.0}
_CONFIDENCE_FACTOR = {"high": 0.9, "medium": 0.65, "experimental": 0.4}
_LEVEL_SCORE = {"Low": 0.25, "Medium": 0.55, "High": 0.8, "Critical": 1.0}


def peacock_impact_score(
    *,
    visibility_opportunity: float,
    business_relevance: float,
    competitive_gap: float,
    confidence: float,
    implementation_difficulty: float,
) -> float:
    raw = (
        visibility_opportunity
        * business_relevance
        * competitive_gap
        * confidence
        / max(0.5, implementation_difficulty)
    )
    return round(min(100.0, raw * 100.0), 2)


def build_opportunity(
    *,
    action: str,
    reason: str,
    affected_page: str,
    seo_opportunity: str,
    aeo_opportunity: str,
    geo_opportunity: str,
    ai_visibility_opportunity: str,
    business_value: str,
    competitor_gap: str,
    implementation_difficulty: str,
    confidence: str,
) -> Opportunity:
    visibility = max(
        _LEVEL_SCORE.get(seo_opportunity, 0.5),
        _LEVEL_SCORE.get(aeo_opportunity, 0.5),
        _LEVEL_SCORE.get(geo_opportunity, 0.5),
        _LEVEL_SCORE.get(ai_visibility_opportunity, 0.5),
    )
    business = _LEVEL_SCORE.get(business_value, 0.5)
    gap = _LEVEL_SCORE.get(competitor_gap, 0.3)
    conf = _CONFIDENCE_FACTOR.get(confidence, 0.65)
    difficulty = _DIFFICULTY_DIVISOR.get(implementation_difficulty, 2.0)

    score = peacock_impact_score(
        visibility_opportunity=visibility,
        business_relevance=business,
        competitive_gap=gap,
        confidence=conf,
        implementation_difficulty=difficulty,
    )
    if score >= 70:
        priority = "Critical"
    elif score >= 45:
        priority = "High"
    elif score >= 20:
        priority = "Medium"
    else:
        priority = "Low"

    return Opportunity(
        action=action,
        reason=reason,
        affected_page=affected_page,
        seo_opportunity=seo_opportunity,
        aeo_opportunity=aeo_opportunity,
        geo_opportunity=geo_opportunity,
        ai_visibility_opportunity=ai_visibility_opportunity,
        business_value=business_value,
        competitor_gap=competitor_gap,
        implementation_difficulty=implementation_difficulty,
        confidence=confidence,
        priority=priority,
        peacock_impact_score=score,
    )


def rank_opportunities(opportunities: list[Opportunity], *, limit: int = 10) -> list[Opportunity]:
    return sorted(opportunities, key=lambda o: o.peacock_impact_score, reverse=True)[:limit]
