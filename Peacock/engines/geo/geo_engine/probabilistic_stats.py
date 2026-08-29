"""Statistics for probabilistic AI visibility distributions."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(slots=True)
class BernoulliEstimate:
    probability: float
    variance: float
    ci_low: float
    ci_high: float
    sample_size: int
    success_count: int


def bernoulli_estimate(successes: int, n: int, *, z: float = 1.96) -> BernoulliEstimate:
    """Point estimate + normal-approx CI for a Bernoulli probability.

    Uses Wilson-ish continuity for small n by clamping CI to [0, 1].
    """
    if n <= 0:
        return BernoulliEstimate(0.0, 0.0, 0.0, 0.0, 0, 0)
    p = successes / n
    variance = p * (1.0 - p)
    se = math.sqrt(variance / n) if n > 0 else 0.0
    ci_low = max(0.0, p - z * se)
    ci_high = min(1.0, p + z * se)
    return BernoulliEstimate(
        probability=p,
        variance=variance,
        ci_low=ci_low,
        ci_high=ci_high,
        sample_size=n,
        success_count=successes,
    )


def population_variance(values: list[float]) -> float:
    if len(values) <= 1:
        return 0.0
    mean = sum(values) / len(values)
    return sum((v - mean) ** 2 for v in values) / len(values)


def engine_disagreement(per_engine_probabilities: list[float]) -> float:
    """0 = engines agree; higher = engines disagree on the Bernoulli rate."""
    if len(per_engine_probabilities) <= 1:
        return 0.0
    # Normalise variance of rates (max variance for [0,1] rates is 0.25)
    return min(1.0, population_variance(per_engine_probabilities) / 0.25)


def temporal_volatility(per_period_probabilities: list[float]) -> float:
    """Volatility of probabilities across observation periods."""
    return engine_disagreement(per_period_probabilities)


def peacock_visibility_confidence(
    *,
    sample_size: int,
    engine_count: int,
    prompt_count: int,
    period_count: int,
    mean_variance: float,
    mean_engine_disagreement: float,
    mean_temporal_volatility: float,
) -> tuple[float, str]:
    """Composite PEACOCK VISIBILITY CONFIDENCE in 0–1 + HIGH/MEDIUM/LOW label.

    Rewards larger samples, more engines/prompts/periods; penalises variance
    and disagreement. Never claims certainty from a single observation.
    """
    if sample_size <= 0:
        return 0.0, "LOW"

    sample_factor = min(1.0, math.log1p(sample_size) / math.log1p(500))
    engine_factor = min(1.0, engine_count / 5.0)
    prompt_factor = min(1.0, prompt_count / 50.0)
    period_factor = min(1.0, period_count / 4.0)
    stability = 1.0 - min(1.0, 0.5 * mean_variance + 0.3 * mean_engine_disagreement + 0.2 * mean_temporal_volatility)

    score = (
        0.35 * sample_factor
        + 0.2 * engine_factor
        + 0.15 * prompt_factor
        + 0.1 * period_factor
        + 0.2 * stability
    )
    score = max(0.0, min(1.0, score))

    # Single-shot hard cap — never HIGH from one observation
    if sample_size < 5 or engine_count < 2:
        score = min(score, 0.45)

    if score >= 0.75:
        label = "HIGH"
    elif score >= 0.5:
        label = "MEDIUM"
    else:
        label = "LOW"
    return score, label


def ai_visibility_score(
    *,
    brand_mention_p: float,
    citation_p: float,
    top3_p: float,
    competitor_gap: float = 0.0,
) -> float:
    """0–100 visibility score from distributional probabilities."""
    raw = (
        0.45 * brand_mention_p
        + 0.25 * citation_p
        + 0.25 * top3_p
        + 0.05 * max(0.0, 1.0 - competitor_gap)
    )
    return round(100.0 * max(0.0, min(1.0, raw)), 1)
