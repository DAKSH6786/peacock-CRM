"""Automatic competitor discovery across categories and overlap signals."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from db_models.deep_competitor import COMPETITOR_CATEGORIES, DISCOVERY_SIGNALS


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass
class DiscoverySignalInput:
    domain: str
    name: str | None = None
    serp_overlap: float = 0.0
    keyword_overlap: float = 0.0
    topic_overlap: float = 0.0
    ai_mention_overlap: float = 0.0
    citation_overlap: float = 0.0
    entity_similarity: float = 0.0
    product_similarity: float = 0.0
    # Optional hint that this is a known business rival
    known_business_competitor: bool = False


@dataclass(slots=True)
class DiscoveredCompetitor:
    name: str
    domain: str
    categories: list[str]
    discovery_method: str
    signals: dict[str, float]
    overall_rivalry_score: float
    is_direct_business_competitor: bool
    discovery_rationale: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def categories_csv(self) -> str:
        return ",".join(self.categories)


# Thresholds for category membership (explainable)
CATEGORY_RULES: dict[str, tuple[str, float]] = {
    "business_competitor": ("product_similarity", 0.55),
    "search_competitor": ("keyword_overlap", 0.45),
    "content_competitor": ("topic_overlap", 0.45),
    "ai_visibility_competitor": ("ai_mention_overlap", 0.35),
    "citation_competitor": ("citation_overlap", 0.35),
    "entity_competitor": ("entity_similarity", 0.45),
    "serp_competitor": ("serp_overlap", 0.4),
}

SIGNAL_WEIGHTS: dict[str, float] = {
    "serp_overlap": 0.16,
    "keyword_overlap": 0.16,
    "topic_overlap": 0.14,
    "ai_mention_overlap": 0.14,
    "citation_overlap": 0.14,
    "entity_similarity": 0.13,
    "product_similarity": 0.13,
}


def classify_categories(signals: dict[str, float], *, known_business: bool) -> list[str]:
    cats: list[str] = []
    for category, (signal, threshold) in CATEGORY_RULES.items():
        if category == "business_competitor" and known_business:
            cats.append(category)
            continue
        if signals.get(signal, 0.0) >= threshold:
            cats.append(category)
    # Ensure category codes are valid
    return [c for c in cats if c in COMPETITOR_CATEGORIES]


def rivalry_score(signals: dict[str, float]) -> float:
    return _clamp01(
        sum(SIGNAL_WEIGHTS[k] * _clamp01(signals.get(k, 0.0)) for k in SIGNAL_WEIGHTS)
    )


def discover_competitors(
    candidates: list[DiscoverySignalInput],
    *,
    min_rivalry: float = 0.25,
) -> list[DiscoveredCompetitor]:
    """Discover competitors dynamically from overlap / similarity signals.

    Not limited to a fixed set of manually entered domains — any candidate
    with sufficient signal strength is classified into one or more categories.
    """
    discovered: list[DiscoveredCompetitor] = []
    for cand in candidates:
        domain = cand.domain.strip().lower().removeprefix("www.")
        if not domain:
            continue
        signals = {
            "serp_overlap": _clamp01(cand.serp_overlap),
            "keyword_overlap": _clamp01(cand.keyword_overlap),
            "topic_overlap": _clamp01(cand.topic_overlap),
            "ai_mention_overlap": _clamp01(cand.ai_mention_overlap),
            "citation_overlap": _clamp01(cand.citation_overlap),
            "entity_similarity": _clamp01(cand.entity_similarity),
            "product_similarity": _clamp01(cand.product_similarity),
        }
        assert set(signals) == set(DISCOVERY_SIGNALS)
        categories = classify_categories(
            signals, known_business=cand.known_business_competitor
        )
        score = rivalry_score(signals)
        if not categories and score < min_rivalry:
            continue
        if not categories and score >= min_rivalry:
            # Weak multi-signal rival without a single dominant category
            categories = ["content_competitor"] if signals["topic_overlap"] >= signals["serp_overlap"] else ["serp_competitor"]

        is_business = "business_competitor" in categories
        top_signals = sorted(signals.items(), key=lambda kv: kv[1], reverse=True)[:3]
        rationale = (
            f"Dynamically discovered via {', '.join(f'{k}={v:.2f}' for k, v in top_signals)}. "
            f"Categories: {', '.join(categories)}. "
            f"{'Direct business competitor.' if is_business else 'Not necessarily a direct business competitor — may be SEO/AI/content rivalry only.'}"
        )
        discovered.append(
            DiscoveredCompetitor(
                name=cand.name or domain.split(".")[0].title(),
                domain=domain,
                categories=categories,
                discovery_method="automatic",
                signals=signals,
                overall_rivalry_score=round(score, 4),
                is_direct_business_competitor=is_business,
                discovery_rationale=rationale,
            )
        )

    discovered.sort(key=lambda d: d.overall_rivalry_score, reverse=True)
    return discovered
