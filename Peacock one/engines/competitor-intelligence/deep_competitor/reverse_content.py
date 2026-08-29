"""Reverse-engineer winning competitor content — evidence only, never copy."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from db_models.deep_competitor import CONTENT_COMPARE_DIMENSIONS, FORBIDDEN_RECOMMENDATION_MODES


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass
class ContentDimensionInput:
    competitor_domain: str
    competitor_url: str
    client_url: str | None
    dimension: str
    client_score: float
    competitor_score: float
    evidence_summary: str


@dataclass(slots=True)
class ContentDiffResult:
    competitor_domain: str
    competitor_url: str
    client_url: str | None
    dimension: str
    competitor_advantage: bool
    client_score: float
    competitor_score: float
    evidence_summary: str
    differentiated_recommendation: str
    copy_rejected: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_DIFF_REC: dict[str, str] = {
    "topical_completeness": "Cover missing sub-intents with original outlines tied to your product proof — do not mirror their section order.",
    "entities": "Strengthen your entity graph (brand, features, customers) with unambiguous ownership language.",
    "structure": "Improve scannable hierarchy and answer blocks uniquely shaped to your narrative.",
    "freshness": "Ship dated updates and new primary evidence on a cadence competitors cannot trivially match.",
    "original_data": "Publish proprietary benchmarks or datasets rather than restating their figures.",
    "references": "Cite primary sources and your own research; avoid cloning their reference list.",
    "schema": "Implement accurate structured data for your entities and offers.",
    "internal_linking": "Build hub-and-spoke links that reinforce your entity ownership, not their IA.",
    "backlinks": "Earn links via original assets and partnerships — never spam or scrapes.",
    "citations": "Become a preferred generative citation via extractability and corroboration.",
    "author_signals": "Surface real expert authorship with verifiable credentials.",
    "content_type": "Choose a differentiated format (tool, map, dataset) that better satisfies intent.",
    "intent_satisfaction": "Map each section to unmet user jobs-to-be-done you uniquely solve.",
    "page_ux": "Improve clarity, speed, and trust cues without imitating their layout.",
}


def reverse_engineer_content(
    comparisons: list[ContentDimensionInput],
) -> list[ContentDiffResult]:
    """Compare dimensions where a competitor repeatedly performs better.

    Returns evidence-backed differences and **differentiated** recommendations.
    Explicitly rejects copy/paraphrase modes.
    """
    results: list[ContentDiffResult] = []
    for item in comparisons:
        if item.dimension not in CONTENT_COMPARE_DIMENSIONS:
            continue
        client = _clamp01(item.client_score)
        rival = _clamp01(item.competitor_score)
        advantage = rival > client + 0.05
        if not advantage:
            continue
        rec = _DIFF_REC[item.dimension]
        # Guardrail language always appended
        rec = (
            f"{rec} Forbidden: {', '.join(FORBIDDEN_RECOMMENDATION_MODES)}."
        )
        results.append(
            ContentDiffResult(
                competitor_domain=item.competitor_domain,
                competitor_url=item.competitor_url,
                client_url=item.client_url,
                dimension=item.dimension,
                competitor_advantage=True,
                client_score=client,
                competitor_score=rival,
                evidence_summary=item.evidence_summary,
                differentiated_recommendation=rec,
                copy_rejected=True,
            )
        )
    results.sort(key=lambda r: r.competitor_score - r.client_score, reverse=True)
    return results
