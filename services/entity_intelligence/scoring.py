"""Entity Association Strength — explainable multi-signal scoring."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any


DEFAULT_ASSOCIATION_WEIGHTS: dict[str, float] = {
    "co_occurrence": 0.20,
    "semantic_proximity": 0.16,
    "ownership_signal": 0.18,
    "citation_linkage": 0.12,
    "topical_centrality": 0.12,
    "recency": 0.10,
    "cross_source_consistency": 0.12,
}


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass(slots=True)
class AssociationSignal:
    """Raw signals for one brand/entity ↔ target entity pair."""

    source_entity_name: str
    source_entity_type: str
    target_entity_name: str
    target_entity_type: str
    is_client_owned: bool = False
    is_competitor_owned: bool = False
    co_occurrence: float = 0.0
    semantic_proximity: float = 0.0
    ownership_signal: float = 0.0
    citation_linkage: float = 0.0
    topical_centrality: float = 0.0
    recency: float = 0.5
    cross_source_consistency: float = 0.0
    observation_count: int = 0


@dataclass(slots=True)
class AssociationScore:
    source_entity_name: str
    source_entity_type: str
    target_entity_name: str
    target_entity_type: str
    is_client_owned: bool
    is_competitor_owned: bool
    association_strength: float
    components: dict[str, float]
    explanations: dict[str, str]
    observation_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def explanations_json(self) -> str:
        return json.dumps(self.explanations, sort_keys=True)


def compute_association_strength(
    signal: AssociationSignal,
    *,
    weights: dict[str, float] | None = None,
) -> AssociationScore:
    """Compute Entity Association Strength (0–1) with explainable components."""
    w = dict(weights or DEFAULT_ASSOCIATION_WEIGHTS)
    total = sum(w.values()) or 1.0
    w = {k: v / total for k, v in w.items()}

    components = {
        "co_occurrence": _clamp01(signal.co_occurrence),
        "semantic_proximity": _clamp01(signal.semantic_proximity),
        "ownership_signal": _clamp01(signal.ownership_signal),
        "citation_linkage": _clamp01(signal.citation_linkage),
        "topical_centrality": _clamp01(signal.topical_centrality),
        "recency": _clamp01(signal.recency),
        "cross_source_consistency": _clamp01(signal.cross_source_consistency),
    }
    strength = sum(w.get(k, 0.0) * v for k, v in components.items())

    explanations = {
        "co_occurrence": (
            f"Observed co-occurrence intensity {components['co_occurrence']:.2f} "
            f"across {signal.observation_count} observations."
        ),
        "semantic_proximity": (
            f"Semantic proximity {components['semantic_proximity']:.2f} between "
            f"{signal.source_entity_name} and {signal.target_entity_name}."
        ),
        "ownership_signal": (
            f"Ownership / product-line language strength {components['ownership_signal']:.2f}."
        ),
        "citation_linkage": (
            f"Citation / source linkage {components['citation_linkage']:.2f}."
        ),
        "topical_centrality": (
            f"Topical centrality of the pair {components['topical_centrality']:.2f}."
        ),
        "recency": f"Recency of supporting observations {components['recency']:.2f}.",
        "cross_source_consistency": (
            f"Consistency across sources/engines {components['cross_source_consistency']:.2f}."
        ),
    }

    return AssociationScore(
        source_entity_name=signal.source_entity_name,
        source_entity_type=signal.source_entity_type,
        target_entity_name=signal.target_entity_name,
        target_entity_type=signal.target_entity_type,
        is_client_owned=signal.is_client_owned,
        is_competitor_owned=signal.is_competitor_owned,
        association_strength=round(_clamp01(strength), 4),
        components={k: round(v, 4) for k, v in components.items()},
        explanations=explanations,
        observation_count=signal.observation_count,
    )


def score_associations(
    signals: list[AssociationSignal],
    *,
    weights: dict[str, float] | None = None,
) -> list[AssociationScore]:
    scores = [compute_association_strength(s, weights=weights) for s in signals]
    scores.sort(key=lambda s: s.association_strength, reverse=True)
    return scores


@dataclass(slots=True)
class EntityGapResult:
    target_concept: str
    target_entity_type: str
    client_brand: str
    client_association: float
    competitor_associations: dict[str, float]
    leading_competitor_name: str | None
    leading_competitor_association: float
    gap_size: float
    severity: str
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def severity_for_gap(gap_size: float, client_association: float) -> str:
    if gap_size >= 0.35 and client_association < 0.5:
        return "critical"
    if gap_size >= 0.25:
        return "high"
    if gap_size >= 0.12:
        return "medium"
    return "low"


def compute_entity_gaps(
    *,
    client_brand: str,
    associations: list[AssociationScore],
    target_concepts: list[str] | None = None,
) -> list[EntityGapResult]:
    """Compare client vs competitor association strength for each target concept."""
    # Index: (owner_brand, target) -> strength
    by_target: dict[str, dict[str, float]] = {}
    target_types: dict[str, str] = {}

    for a in associations:
        target = a.target_entity_name
        target_types[target] = a.target_entity_type
        owner = a.source_entity_name
        by_target.setdefault(target, {})[owner] = a.association_strength

    concepts = target_concepts or sorted(by_target.keys())
    gaps: list[EntityGapResult] = []
    for concept in concepts:
        owners = by_target.get(concept, {})
        client_score = owners.get(client_brand, 0.0)
        competitors = {
            name: score
            for name, score in owners.items()
            if name.lower() != client_brand.lower()
        }
        if not competitors and client_score <= 0:
            continue
        leading_name = None
        leading_score = 0.0
        if competitors:
            leading_name, leading_score = max(competitors.items(), key=lambda kv: kv[1])
        gap_size = max(0.0, leading_score - client_score)
        sev = severity_for_gap(gap_size, client_score)
        summary = (
            f"Target Concept: {concept}. "
            + (
                " ".join(
                    f"{name} association {score:.2f}."
                    for name, score in sorted(
                        competitors.items(), key=lambda kv: kv[1], reverse=True
                    )
                )
                + " "
                if competitors
                else ""
            )
            + f"Client association {client_score:.2f}."
        )
        gaps.append(
            EntityGapResult(
                target_concept=concept,
                target_entity_type=target_types.get(concept, "concept"),
                client_brand=client_brand,
                client_association=round(client_score, 4),
                competitor_associations={k: round(v, 4) for k, v in competitors.items()},
                leading_competitor_name=leading_name,
                leading_competitor_association=round(leading_score, 4),
                gap_size=round(gap_size, 4),
                severity=sev,
                summary=summary,
            )
        )

    gaps.sort(key=lambda g: (g.gap_size, -g.client_association), reverse=True)
    return gaps
