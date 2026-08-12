"""Citation Influence Score — proprietary, fully explainable components.

Never use opaque black-box scores. Each component is named, weighted,
and accompanied by a human-readable explanation string.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from typing import Any
from urllib.parse import urlparse


DEFAULT_CIS_WEIGHTS: dict[str, float] = {
    "citation_frequency": 0.18,
    "cross_engine_citation": 0.14,
    "topic_coverage": 0.12,
    "prominence": 0.12,
    "freshness": 0.10,
    "authority_proxy": 0.12,
    "brand_association": 0.12,
    "citation_diversity": 0.10,
}

# Hub: cited in ≥ this share of observations (relative threshold also applied)
HUB_OBSERVATION_SHARE = 0.15
HUB_MIN_CITATIONS = 3


@dataclass(slots=True)
class CitationEvent:
    """One citation occurrence inside one observation."""

    observation_id: str
    engine_code: str
    prompt_text: str
    topic_label: str
    cited_url: str
    cited_domain: str
    page_path: str | None
    source_class: str
    is_competitor_owned: bool
    is_client_owned: bool
    prominence: float
    freshness_days: int | None
    authority_proxy: float
    position_in_answer: int | None
    client_mentioned: bool
    competitor_names_mentioned: list[str] = field(default_factory=list)


@dataclass(slots=True)
class DomainInfluenceBreakdown:
    cited_domain: str
    source_class: str
    is_citation_hub: bool
    is_competitor_owned: bool
    is_client_owned: bool
    citation_influence_score: float
    components: dict[str, float]
    explanations: dict[str, str]
    citation_count: int
    engine_count: int
    page_count: int
    observation_share: float
    client_mention_rate: float
    competitor_mention_rate: float
    top_competitor_name: str | None
    top_competitor_mention_rate: float
    engines: list[str]
    pages: list[str]
    topics: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def explanations_json(self) -> str:
        return json.dumps(self.explanations, sort_keys=True)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def freshness_score(freshness_days: int | None) -> float:
    """Fresher content scores higher. Unknown → neutral 0.5."""
    if freshness_days is None:
        return 0.5
    if freshness_days <= 30:
        return 1.0
    if freshness_days <= 90:
        return 0.85
    if freshness_days <= 180:
        return 0.7
    if freshness_days <= 365:
        return 0.5
    if freshness_days <= 730:
        return 0.3
    return 0.15


def normalise_domain(url_or_domain: str) -> str:
    raw = (url_or_domain or "").strip().lower()
    if not raw:
        return ""
    if "://" not in raw and "/" not in raw:
        return raw.removeprefix("www.")
    parsed = urlparse(raw if "://" in raw else f"https://{raw}")
    host = (parsed.netloc or parsed.path.split("/")[0]).lower()
    return host.removeprefix("www.")


def page_path_from_url(url: str) -> str:
    parsed = urlparse(url if "://" in url else f"https://{url}")
    path = parsed.path or "/"
    if parsed.query:
        return f"{path}?{parsed.query}"
    return path


def compute_domain_influence(
    *,
    cited_domain: str,
    events: list[CitationEvent],
    total_observations: int,
    all_topics_in_analysis: set[str],
    weights: dict[str, float] | None = None,
) -> DomainInfluenceBreakdown:
    """Compute Citation Influence Score for one domain from its citation events."""
    if not events:
        raise ValueError("events required")
    if total_observations <= 0:
        raise ValueError("total_observations must be > 0")

    w = dict(weights or DEFAULT_CIS_WEIGHTS)
    total_w = sum(w.values()) or 1.0
    w = {k: v / total_w for k, v in w.items()}

    obs_ids = {e.observation_id for e in events}
    engines = sorted({e.engine_code for e in events})
    pages = sorted({(e.page_path or e.cited_url) for e in events})
    topics = sorted({e.topic_label for e in events if e.topic_label})
    source_class = _majority_source_class(events)
    is_competitor = any(e.is_competitor_owned for e in events)
    is_client = any(e.is_client_owned for e in events)

    # --- Components (all 0–1, explainable) ---
    citation_frequency = _clamp01(len(events) / max(1, total_observations))
    cross_engine = _clamp01(len(engines) / 4.0)  # 4+ engines → full credit
    topic_cov = (
        _clamp01(len(topics) / max(1, len(all_topics_in_analysis)))
        if all_topics_in_analysis
        else _clamp01(len(topics) / 3.0)
    )
    prominence = _clamp01(sum(e.prominence for e in events) / len(events))
    freshness = _clamp01(
        sum(freshness_score(e.freshness_days) for e in events) / len(events)
    )
    authority = _clamp01(sum(e.authority_proxy for e in events) / len(events))

    client_hits = sum(1 for e in events if e.client_mentioned)
    client_mention_rate = client_hits / len(events)
    # Brand association: how often client is co-mentioned when this domain is cited
    brand_association = _clamp01(client_mention_rate)

    # Diversity: unique pages + engines relative to citation volume (hub breadth)
    diversity = _clamp01(
        0.5 * (len(pages) / max(1, len(events))) + 0.5 * (len(engines) / max(1, len(events)))
    )
    # Prefer domains that appear across many pages without being a single-URL spam spike
    if len(pages) == 1 and len(events) >= 5:
        diversity = min(diversity, 0.35)

    components = {
        "citation_frequency": round(citation_frequency, 4),
        "cross_engine_citation": round(cross_engine, 4),
        "topic_coverage": round(topic_cov, 4),
        "prominence": round(prominence, 4),
        "freshness": round(freshness, 4),
        "authority_proxy": round(authority, 4),
        "brand_association": round(brand_association, 4),
        "citation_diversity": round(diversity, 4),
    }

    explanations = {
        "citation_frequency": (
            f"Cited {len(events)} times across {len(obs_ids)} of "
            f"{total_observations} observations "
            f"({100 * citation_frequency:.1f}% observation intensity)."
        ),
        "cross_engine_citation": (
            f"Appears on {len(engines)} generative engine(s): {', '.join(engines) or 'none'}."
        ),
        "topic_coverage": (
            f"Covers {len(topics)} topic label(s) of "
            f"{len(all_topics_in_analysis) or len(topics)} in this analysis."
        ),
        "prominence": (
            f"Mean in-answer prominence {prominence:.2f} "
            f"(1.0 = lead citation / highly emphasised)."
        ),
        "freshness": (
            f"Mean freshness score {freshness:.2f} from known publish/age signals "
            f"(unknown age contributes a neutral 0.5)."
        ),
        "authority_proxy": (
            f"Mean authority proxy {authority:.2f} from source-class priors "
            f"and optional trust signals (explainable heuristic, not a secret score)."
        ),
        "brand_association": (
            f"Client brand co-mentioned in {100 * client_mention_rate:.1f}% of "
            f"observations that cite this domain."
        ),
        "citation_diversity": (
            f"{len(pages)} distinct page(s) and {len(engines)} engine(s) relative "
            f"to {len(events)} citation event(s)."
        ),
    }

    score01 = sum(w.get(k, 0.0) * v for k, v in components.items())
    cis = round(100.0 * _clamp01(score01), 4)

    observation_share = len(obs_ids) / total_observations
    is_hub = observation_share >= HUB_OBSERVATION_SHARE and len(events) >= HUB_MIN_CITATIONS

    # Competitor mention stats among observations citing this domain
    competitor_counter: dict[str, int] = defaultdict(int)
    for e in events:
        for name in e.competitor_names_mentioned:
            competitor_counter[name] += 1
    top_comp = None
    top_comp_rate = 0.0
    if competitor_counter:
        top_comp, top_count = max(competitor_counter.items(), key=lambda kv: kv[1])
        top_comp_rate = top_count / len(events)
    competitor_mention_rate = sum(
        1 for e in events if e.competitor_names_mentioned
    ) / len(events)

    return DomainInfluenceBreakdown(
        cited_domain=cited_domain,
        source_class=source_class,
        is_citation_hub=is_hub,
        is_competitor_owned=is_competitor,
        is_client_owned=is_client,
        citation_influence_score=cis,
        components=components,
        explanations=explanations,
        citation_count=len(events),
        engine_count=len(engines),
        page_count=len(pages),
        observation_share=round(observation_share, 4),
        client_mention_rate=round(client_mention_rate, 4),
        competitor_mention_rate=round(competitor_mention_rate, 4),
        top_competitor_name=top_comp,
        top_competitor_mention_rate=round(top_comp_rate, 4),
        engines=engines,
        pages=pages[:50],
        topics=topics,
    )


def _majority_source_class(events: list[CitationEvent]) -> str:
    counts: dict[str, int] = defaultdict(int)
    for e in events:
        counts[e.source_class] += 1
    return max(counts.items(), key=lambda kv: kv[1])[0]


def aggregate_domain_scores(
    *,
    events: list[CitationEvent],
    total_observations: int,
    weights: dict[str, float] | None = None,
) -> list[DomainInfluenceBreakdown]:
    """Aggregate all citation events into per-domain Citation Influence Scores."""
    by_domain: dict[str, list[CitationEvent]] = defaultdict(list)
    topics: set[str] = set()
    for e in events:
        by_domain[e.cited_domain].append(e)
        if e.topic_label:
            topics.add(e.topic_label)

    scores = [
        compute_domain_influence(
            cited_domain=domain,
            events=domain_events,
            total_observations=total_observations,
            all_topics_in_analysis=topics,
            weights=weights,
        )
        for domain, domain_events in by_domain.items()
    ]
    scores.sort(key=lambda s: s.citation_influence_score, reverse=True)
    return scores
