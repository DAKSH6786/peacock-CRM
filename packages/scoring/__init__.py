"""Deterministic SEO scoring framework for Peacock SEO Engine.

Numeric scores are computed from crawl/connector metrics only.
LLMs may interpret results later — they must never invent the score.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Mapping, Sequence


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def weighted_score(impact: float, confidence: float, effort: float) -> float:
    """Explainable recommendation priority (0–1)."""
    return clamp(impact) * clamp(confidence) * (1.0 - 0.5 * clamp(effort))


def ratio_score(good: float, total: float, *, empty: float = 100.0) -> float:
    """Map a success ratio to 0–100. Empty population yields ``empty``."""
    if total <= 0:
        return empty
    return round(100.0 * clamp(good / total), 2)


def penalty_score(base: float, penalties: Sequence[float]) -> float:
    """Apply additive penalties (each typically 0–100 points) and clamp."""
    value = base - sum(penalties)
    return round(clamp(value, 0.0, 100.0), 2)


# Fixed section weights for Peacock SEO Score — transparent and deterministic.
PEACOCK_SEO_WEIGHTS: dict[str, float] = {
    "technical_seo": 0.18,
    "content_quality": 0.18,
    "on_page_seo": 0.16,
    "internal_linking": 0.14,
    "structured_data": 0.10,
    "performance": 0.12,
    "indexability": 0.12,
}


@dataclass(slots=True)
class ScoreResult:
    """Explainable section or overall score."""

    code: str
    label: str
    score: float
    confidence: float
    inputs_used: list[str] = field(default_factory=list)
    major_positive_factors: list[str] = field(default_factory=list)
    major_negative_factors: list[str] = field(default_factory=list)
    recommended_actions: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.score = round(clamp(float(self.score), 0.0, 100.0), 2)
        self.confidence = round(clamp(float(self.confidence), 0.0, 1.0), 4)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def peacock_seo_score(sections: Mapping[str, ScoreResult]) -> ScoreResult:
    """Roll up section scores into Peacock SEO Score (0–100).

    Missing sections contribute 0 with reduced overall confidence rather than
    inventing numbers. Weights are fixed in ``PEACOCK_SEO_WEIGHTS``.
    """
    weighted_total = 0.0
    weight_sum = 0.0
    confidence_acc = 0.0
    inputs: list[str] = ["PEACOCK_SEO_WEIGHTS"]
    positives: list[str] = []
    negatives: list[str] = []
    actions: list[str] = []

    for code, weight in PEACOCK_SEO_WEIGHTS.items():
        section = sections.get(code)
        inputs.append(f"weight:{code}={weight}")
        if section is None:
            negatives.append(f"Missing section score: {code}")
            continue
        weighted_total += section.score * weight
        weight_sum += weight
        confidence_acc += section.confidence * weight
        inputs.extend(section.inputs_used[:5])
        positives.extend(section.major_positive_factors[:2])
        negatives.extend(section.major_negative_factors[:2])
        actions.extend(section.recommended_actions[:2])

    score = round(weighted_total / weight_sum, 2) if weight_sum else 0.0
    confidence = round(confidence_acc / weight_sum, 4) if weight_sum else 0.0
    # Penalise incomplete rollups
    present = sum(1 for c in PEACOCK_SEO_WEIGHTS if c in sections)
    coverage = present / len(PEACOCK_SEO_WEIGHTS)
    confidence = round(confidence * coverage, 4)

    if score >= 80:
        positives.insert(0, f"Strong overall Peacock SEO Score ({score})")
    elif score < 50:
        negatives.insert(0, f"Weak overall Peacock SEO Score ({score})")
        actions.insert(0, "Prioritise critical and high-impact recommendations first")

    return ScoreResult(
        code="peacock_seo_score",
        label="Peacock SEO Score",
        score=score,
        confidence=confidence,
        inputs_used=list(dict.fromkeys(inputs))[:40],
        major_positive_factors=list(dict.fromkeys(positives))[:8],
        major_negative_factors=list(dict.fromkeys(negatives))[:8],
        recommended_actions=list(dict.fromkeys(actions))[:8],
    )


def aggregate_finding_penalties(
    findings: Iterable[Any],
    *,
    critical: float = 12.0,
    warning: float = 5.0,
    opportunity: float = 2.0,
) -> list[float]:
    """Convert finding severities into score penalties."""
    penalties: list[float] = []
    for finding in findings:
        severity = getattr(finding, "severity", "warning")
        if severity == "critical":
            penalties.append(critical)
        elif severity == "warning":
            penalties.append(warning)
        else:
            penalties.append(opportunity)
    return penalties
