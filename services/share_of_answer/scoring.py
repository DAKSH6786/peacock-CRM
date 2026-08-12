"""Share of Answer multi-indicator scoring.

Do not pretend token count alone equals influence.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


# Default weights — sum to 1.0. Token span is intentionally excluded here;
# it may only contribute via a tiny diagnostic residual if explicitly enabled.
DEFAULT_INDICATOR_WEIGHTS: dict[str, float] = {
    "mention": 0.12,
    "position": 0.14,
    "recommendation_strength": 0.18,
    "answer_space": 0.10,  # structural space, not raw tokens
    "citation_ownership": 0.14,
    "semantic_prominence": 0.12,
    "claim_balance": 0.10,
    "comparison_outcome": 0.10,
}

# Hard cap: even if callers try to smuggle token weight in, keep it tiny
MAX_TOKEN_SPAN_WEIGHT = 0.05

COMPARISON_SCORES: dict[str, float] = {
    "win": 1.0,
    "tie": 0.55,
    "mixed": 0.45,
    "lose": 0.15,
    "absent": 0.0,
}


@dataclass(slots=True)
class EntityIndicatorReading:
    entity_name: str
    is_client: bool = False
    mention: bool = False
    mention_count: int = 0
    position: int | None = None
    recommendation_strength: float = 0.0
    answer_space: float = 0.0
    citation_ownership: float = 0.0
    semantic_prominence: float = 0.0
    positive_claims: int = 0
    negative_claims: int = 0
    neutral_claims: int = 0
    comparison_outcome: str = "absent"
    token_span_ratio: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class InfluenceBreakdown:
    entity_name: str
    influence: float
    components: dict[str, float]
    claim_balance: float
    position_score: float
    comparison_score: float
    token_span_used_as_sole_signal: bool = False


def position_to_score(position: int | None, *, max_rank: int = 10) -> float:
    """Higher ranks (1) score higher; unranked → 0."""
    if position is None or position < 1:
        return 0.0
    return max(0.0, min(1.0, (max_rank - position + 1) / max_rank))


def claim_balance_score(positive: int, negative: int, neutral: int) -> float:
    """Map claim polarity to [0, 1]. Neutral is mild positive evidence of presence."""
    total = positive + negative + neutral
    if total <= 0:
        return 0.0
    # Signed balance shifted into [0, 1]
    signed = (positive - negative) / total
    neutral_boost = 0.1 * (neutral / total)
    return max(0.0, min(1.0, 0.5 + 0.5 * signed + neutral_boost))


def comparison_to_score(outcome: str) -> float:
    return COMPARISON_SCORES.get(outcome.lower().strip(), 0.0)


def compute_influence(
    reading: EntityIndicatorReading,
    *,
    weights: dict[str, float] | None = None,
    include_token_span_residual: bool = False,
    token_span_weight: float = 0.0,
) -> InfluenceBreakdown:
    """Composite influence from multiple indicators.

    Token span is never accepted as the sole signal. If
    ``include_token_span_residual`` is True, a capped residual weight may be
    mixed in — still never enough to dominate.
    """
    w = dict(weights or DEFAULT_INDICATOR_WEIGHTS)
    # Renormalise provided weights
    total_w = sum(w.values()) or 1.0
    w = {k: v / total_w for k, v in w.items()}

    position_score = position_to_score(reading.position)
    claim_bal = claim_balance_score(
        reading.positive_claims, reading.negative_claims, reading.neutral_claims
    )
    comparison_score = comparison_to_score(reading.comparison_outcome)
    mention_score = 1.0 if reading.mention else 0.0

    components = {
        "mention": mention_score,
        "position": position_score,
        "recommendation_strength": _clamp01(reading.recommendation_strength),
        "answer_space": _clamp01(reading.answer_space),
        "citation_ownership": _clamp01(reading.citation_ownership),
        "semantic_prominence": _clamp01(reading.semantic_prominence),
        "claim_balance": claim_bal,
        "comparison_outcome": comparison_score,
    }

    influence = sum(w.get(k, 0.0) * v for k, v in components.items())

    token_as_sole = False
    if include_token_span_residual:
        tw = min(MAX_TOKEN_SPAN_WEIGHT, max(0.0, token_span_weight))
        if tw > 0:
            # Dilute existing influence then add residual — still multi-indicator
            influence = (1.0 - tw) * influence + tw * _clamp01(reading.token_span_ratio)
            components["token_span_residual"] = _clamp01(reading.token_span_ratio)

    # Guardrail: if somehow only token span were non-zero and weights abused,
    # flag it. Influence from token alone is rejected as primary methodology.
    non_token = [
        components["mention"],
        components["position"],
        components["recommendation_strength"],
        components["answer_space"],
        components["citation_ownership"],
        components["semantic_prominence"],
        components["claim_balance"],
        components["comparison_outcome"],
    ]
    if sum(non_token) <= 1e-9 and reading.token_span_ratio > 0:
        token_as_sole = True
        # Do not award influence for token-only presence under default methodology
        influence = 0.0

    return InfluenceBreakdown(
        entity_name=reading.entity_name,
        influence=max(0.0, min(1.0, influence)),
        components=components,
        claim_balance=claim_bal,
        position_score=position_score,
        comparison_score=comparison_score,
        token_span_used_as_sole_signal=token_as_sole,
    )


def normalise_share_of_answer(influences: dict[str, float]) -> dict[str, float]:
    """Convert raw influences to percentage Share of Answer (sums to ~100)."""
    total = sum(max(0.0, v) for v in influences.values())
    if total <= 0:
        return {k: 0.0 for k in influences}
    return {k: 100.0 * max(0.0, v) / total for k, v in influences.items()}


def token_only_shares(token_span_ratios: dict[str, float]) -> dict[str, float]:
    """Diagnostic: what Share would look like if tokens alone were used."""
    return normalise_share_of_answer(token_span_ratios)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass
class BrandAggregate:
    entity_name: str
    is_client: bool
    share_of_answer: float
    mention_rate: float
    avg_position_score: float
    avg_recommendation_strength: float
    avg_answer_space: float
    avg_citation_ownership: float
    avg_semantic_prominence: float
    avg_claim_balance: float
    avg_comparison_score: float
    avg_token_span_ratio: float
    token_only_share: float
    token_vs_influence_gap: float
    positive_claims_total: int
    negative_claims_total: int
    neutral_claims_total: int
    observation_sample_size: int
    mean_influence: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def aggregate_brand_scores(
    *,
    entity_readings_per_observation: list[list[EntityIndicatorReading]],
    weights: dict[str, float] | None = None,
) -> list[BrandAggregate]:
    """Aggregate multi-observation readings into cluster Share of Answer scores."""
    if not entity_readings_per_observation:
        return []

    # Per-entity accumulators
    names: set[str] = set()
    client_flags: dict[str, bool] = {}
    for obs in entity_readings_per_observation:
        for r in obs:
            names.add(r.entity_name)
            client_flags[r.entity_name] = client_flags.get(r.entity_name, False) or r.is_client

    # Mean influence across observations (0 if absent in an observation)
    sum_influence: dict[str, float] = {n: 0.0 for n in names}
    sum_mention: dict[str, float] = {n: 0.0 for n in names}
    sum_pos: dict[str, float] = {n: 0.0 for n in names}
    sum_rec: dict[str, float] = {n: 0.0 for n in names}
    sum_space: dict[str, float] = {n: 0.0 for n in names}
    sum_cite: dict[str, float] = {n: 0.0 for n in names}
    sum_sem: dict[str, float] = {n: 0.0 for n in names}
    sum_claim: dict[str, float] = {n: 0.0 for n in names}
    sum_cmp: dict[str, float] = {n: 0.0 for n in names}
    sum_token: dict[str, float] = {n: 0.0 for n in names}
    pos_claims: dict[str, int] = {n: 0 for n in names}
    neg_claims: dict[str, int] = {n: 0 for n in names}
    neu_claims: dict[str, int] = {n: 0 for n in names}
    n_obs = len(entity_readings_per_observation)

    # Also accumulate token spans for diagnostic token-only share
    mean_token: dict[str, float] = {n: 0.0 for n in names}

    for obs in entity_readings_per_observation:
        by_name = {r.entity_name: r for r in obs}
        for name in names:
            reading = by_name.get(name)
            if reading is None:
                reading = EntityIndicatorReading(entity_name=name, is_client=client_flags[name])
            breakdown = compute_influence(reading, weights=weights)
            sum_influence[name] += breakdown.influence
            sum_mention[name] += 1.0 if reading.mention else 0.0
            sum_pos[name] += breakdown.position_score
            sum_rec[name] += _clamp01(reading.recommendation_strength)
            sum_space[name] += _clamp01(reading.answer_space)
            sum_cite[name] += _clamp01(reading.citation_ownership)
            sum_sem[name] += _clamp01(reading.semantic_prominence)
            sum_claim[name] += breakdown.claim_balance
            sum_cmp[name] += breakdown.comparison_score
            sum_token[name] += _clamp01(reading.token_span_ratio)
            mean_token[name] += _clamp01(reading.token_span_ratio)
            pos_claims[name] += reading.positive_claims
            neg_claims[name] += reading.negative_claims
            neu_claims[name] += reading.neutral_claims

    mean_inf = {n: sum_influence[n] / n_obs for n in names}
    shares = normalise_share_of_answer(mean_inf)
    token_shares = token_only_shares({n: mean_token[n] / n_obs for n in names})

    out: list[BrandAggregate] = []
    for name in names:
        soa = shares[name]
        tok = token_shares.get(name, 0.0)
        out.append(
            BrandAggregate(
                entity_name=name,
                is_client=client_flags[name],
                share_of_answer=round(soa, 4),
                mention_rate=sum_mention[name] / n_obs,
                avg_position_score=sum_pos[name] / n_obs,
                avg_recommendation_strength=sum_rec[name] / n_obs,
                avg_answer_space=sum_space[name] / n_obs,
                avg_citation_ownership=sum_cite[name] / n_obs,
                avg_semantic_prominence=sum_sem[name] / n_obs,
                avg_claim_balance=sum_claim[name] / n_obs,
                avg_comparison_score=sum_cmp[name] / n_obs,
                avg_token_span_ratio=sum_token[name] / n_obs,
                token_only_share=round(tok, 4),
                token_vs_influence_gap=round(soa - tok, 4),
                positive_claims_total=pos_claims[name],
                negative_claims_total=neg_claims[name],
                neutral_claims_total=neu_claims[name],
                observation_sample_size=n_obs,
                mean_influence=mean_inf[name],
            )
        )

    out.sort(key=lambda b: b.share_of_answer, reverse=True)
    return out
