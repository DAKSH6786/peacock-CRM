"""Per-response AI Visibility extraction — reuses existing real deterministic parsers.

Brand mention / citation / recommendation-position detection reuses
``geo_engine.llm_visibility_probe.parse_visibility_text`` (already used by the
probabilistic AI Visibility campaigns) so the same tested logic powers both
features. Domain/URL citation classification reuses ``citation_graph``.
Sentiment and brand-attribute extraction are new, explicitly-labelled
lexicon heuristics — not a certified NLP model.
"""

from __future__ import annotations

import re

from citation_graph.classify import extract_urls, host_from_url
from geo_engine.llm_visibility_probe import parse_visibility_text

from ai_visibility.models import QueryObservation

_RECOMMEND_RE = re.compile(
    r"\b(recommend|best choice|top pick|top choice|go with|great option|ideal for)\b", re.IGNORECASE
)
_POSITIVE_WORDS = {
    "best", "excellent", "trusted", "reliable", "leading", "popular", "innovative",
    "powerful", "affordable", "flexible", "robust", "great", "strong", "top-rated",
}
_NEGATIVE_WORDS = {
    "poor", "bad", "unreliable", "expensive", "lacking", "weak", "limited",
    "outdated", "difficult", "confusing", "disappointing",
}
_ATTRIBUTE_RE = re.compile(r"\b([a-z-]{4,20})\s+(?:platform|tool|solution|option|choice|provider)\b", re.IGNORECASE)


def _sentiment_near(text: str, brand: str, *, window: int = 200) -> str:
    lower = text.lower()
    brand_l = brand.strip().lower()
    idx = lower.find(brand_l)
    if idx < 0:
        return "unknown"
    start = max(0, idx - window)
    end = min(len(lower), idx + len(brand_l) + window)
    snippet = lower[start:end]
    positive = sum(1 for w in _POSITIVE_WORDS if w in snippet)
    negative = sum(1 for w in _NEGATIVE_WORDS if w in snippet)
    if positive > negative:
        return "positive"
    if negative > positive:
        return "negative"
    return "neutral" if (positive or negative) else "unknown"


def _brand_attributes(text: str, brand: str, *, window: int = 120) -> list[str]:
    lower = text.lower()
    brand_l = brand.strip().lower()
    idx = lower.find(brand_l)
    if idx < 0:
        return []
    start = max(0, idx - window)
    end = min(len(text), idx + len(brand_l) + window)
    snippet = text[start:end]
    found = [m.group(1).lower() for m in _ATTRIBUTE_RE.finditer(snippet)]
    return list(dict.fromkeys(found))[:5]


def analyse_response(
    *,
    intent: str,
    query_text: str,
    engine_code: str,
    engine_name: str,
    content: str,
    simulated: bool,
    brand: str,
    competitors: list[str],
    client_domains: list[str] | None = None,
    competitor_domains: list[str] | None = None,
) -> QueryObservation:
    outcome = parse_visibility_text(content, brand_name=brand, competitors=competitors)

    urls = extract_urls(content)
    cited_domains = sorted({host_from_url(u) for u in urls})
    recommended = bool(outcome.brand_mentioned and _RECOMMEND_RE.search(content or ""))

    return QueryObservation(
        intent=intent,
        query_text=query_text,
        engine_code=engine_code,
        engine_name=engine_name,
        simulated=simulated,
        brand_mentioned=outcome.brand_mentioned,
        recommended=recommended,
        recommendation_position=outcome.brand_position,
        competitor_mentions=outcome.competitor_mentions,
        cited_domains=cited_domains,
        cited_urls=urls[:10],
        brand_attributes=_brand_attributes(content, brand),
        sentiment=_sentiment_near(content, brand) if not simulated and content.strip() else "unknown",
    )
