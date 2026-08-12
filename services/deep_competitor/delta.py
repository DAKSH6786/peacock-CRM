"""Competitive Delta Engine — where rivals are stronger and how to leapfrog."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


DELTA_DIMENSIONS: tuple[str, ...] = (
    "search_visibility",
    "content_depth",
    "ai_visibility",
    "citation_authority",
    "entity_ownership",
    "product_coverage",
    "serp_presence",
)


@dataclass
class DimensionScoreInput:
    competitor_domain: str
    competitor_name: str
    dimension: str
    client_score: float
    competitor_score: float
    evidence: str | None = None


@dataclass(slots=True)
class CompetitiveDelta:
    competitor_domain: str
    competitor_name: str
    dimension: str
    where_stronger: str
    why_stronger: str
    gap_difficulty: str
    gap_difficulty_score: float
    how_to_close: str
    how_to_leapfrog: str
    client_score: float
    competitor_score: float
    delta: float
    evidence: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _difficulty(delta: float) -> tuple[str, float]:
    d = abs(delta)
    if d >= 0.45:
        return "hard", round(d, 4)
    if d >= 0.25:
        return "moderate", round(d, 4)
    if d >= 0.1:
        return "achievable", round(d, 4)
    return "easy", round(d, 4)


_CLOSE: dict[str, str] = {
    "search_visibility": "Expand high-intent keyword coverage and fix technical/index gaps on priority URLs.",
    "content_depth": "Fill missing subtopics and evidence blocks with original research — do not rewrite their pages.",
    "ai_visibility": "Improve answer extractability, entity clarity, and citable primary sources.",
    "citation_authority": "Earn ethical citations via original data, expert contribution, and accurate listings.",
    "entity_ownership": "Strengthen brand↔concept association with unambiguous ownership content.",
    "product_coverage": "Document differentiated capabilities tied to customer problems you uniquely solve.",
    "serp_presence": "Win featured SERP real estate with intent-matched formats (not cloned competitor SERP pages).",
}

_LEAPFROG: dict[str, str] = {
    "search_visibility": "Own a narrower high-value intent cluster with superior proof density competitors under-serve.",
    "content_depth": "Publish proprietary datasets or frameworks that redefine the topic narrative.",
    "ai_visibility": "Become the cited primary source for a contested concept via corroboration and structure.",
    "citation_authority": "Ship reference-grade assets other publishers prefer over secondary roundups.",
    "entity_ownership": "Bind executive/product/customer entities into a denser ownership graph than rivals.",
    "product_coverage": "Leapfrog with a category-defining offer angle, not feature parity copy.",
    "serp_presence": "Introduce a superior content type (calculator, map, benchmark) that changes SERP expectations.",
}

_WHY: dict[str, str] = {
    "search_visibility": "Higher observed keyword/SERP overlap performance and ranking footprint.",
    "content_depth": "Broader topical completeness and supporting evidence density.",
    "ai_visibility": "Stronger AI mention / selection patterns in generative answers.",
    "citation_authority": "More frequent citation ownership across generative and web sources.",
    "entity_ownership": "Stronger entity association to contested concepts.",
    "product_coverage": "Closer product/feature similarity coverage of buyer problems.",
    "serp_presence": "More consistent presence across overlapping SERP opportunities.",
}


def compute_deltas(inputs: list[DimensionScoreInput]) -> list[CompetitiveDelta]:
    """Answer: Where are they stronger? Why? How hard? How to close? How to leapfrog?"""
    deltas: list[CompetitiveDelta] = []
    for item in inputs:
        client = _clamp01(item.client_score)
        rival = _clamp01(item.competitor_score)
        delta = round(rival - client, 4)
        if delta <= 0.05:
            continue  # not meaningfully stronger
        difficulty, diff_score = _difficulty(delta)
        dim = item.dimension if item.dimension in DELTA_DIMENSIONS else item.dimension
        deltas.append(
            CompetitiveDelta(
                competitor_domain=item.competitor_domain,
                competitor_name=item.competitor_name,
                dimension=dim,
                where_stronger=(
                    f"{item.competitor_name} leads on {dim.replace('_', ' ')} "
                    f"(competitor {rival:.2f} vs client {client:.2f}, delta +{delta:.2f})."
                ),
                why_stronger=_WHY.get(dim, "Observed comparative performance advantage."),
                gap_difficulty=difficulty,
                gap_difficulty_score=diff_score,
                how_to_close=_CLOSE.get(
                    dim,
                    "Close the gap with differentiated proof and coverage — never by copying their pages.",
                ),
                how_to_leapfrog=_LEAPFROG.get(
                    dim,
                    "Leapfrog with original assets and a distinct narrative angle.",
                ),
                client_score=client,
                competitor_score=rival,
                delta=delta,
                evidence=item.evidence,
            )
        )
    deltas.sort(key=lambda d: d.delta, reverse=True)
    return deltas
