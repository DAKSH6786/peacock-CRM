"""Typed contracts for Probabilistic AI Visibility."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


# Hard anti-abuse ceilings — never allow uncontrolled traffic
HARD_MAX_REPETITIONS = 50
HARD_MAX_CALLS_PER_MINUTE = 30
HARD_MAX_CONCURRENT = 3
HARD_MAX_TOTAL_CALLS = 2_000
HARD_MIN_INTERVAL_MS = 500
DEFAULT_REPETITIONS = 5


@dataclass(slots=True)
class RateLimitPolicy:
    max_calls_per_minute: int = 6
    max_concurrent: int = 1
    max_total_calls: int = 500
    min_interval_ms: int = 1500
    target_repetitions: int = DEFAULT_REPETITIONS
    max_repetitions: int = 20

    def clamped(self) -> RateLimitPolicy:
        return RateLimitPolicy(
            max_calls_per_minute=min(max(1, self.max_calls_per_minute), HARD_MAX_CALLS_PER_MINUTE),
            max_concurrent=min(max(1, self.max_concurrent), HARD_MAX_CONCURRENT),
            max_total_calls=min(max(1, self.max_total_calls), HARD_MAX_TOTAL_CALLS),
            min_interval_ms=max(self.min_interval_ms, HARD_MIN_INTERVAL_MS),
            target_repetitions=min(max(1, self.target_repetitions), HARD_MAX_REPETITIONS),
            max_repetitions=min(
                max(self.target_repetitions, self.max_repetitions), HARD_MAX_REPETITIONS
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ProbeCellSpec:
    prompt_text: str
    engine_code: str
    model_code: str | None = None
    location_code: str = "global"
    persona_code: str = "default"
    config_code: str = "temp_0.2"
    temperature: float = 0.2
    time_bucket: str = "current"
    target_repetitions: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CampaignSpec:
    website_id: str
    name: str
    brand_name: str
    cells: list[ProbeCellSpec]
    competitors: list[str] = field(default_factory=list)
    rate_limit: RateLimitPolicy = field(default_factory=RateLimitPolicy)
    notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "website_id": self.website_id,
            "name": self.name,
            "brand_name": self.brand_name,
            "cells": [c.to_dict() for c in self.cells],
            "competitors": list(self.competitors),
            "rate_limit": self.rate_limit.to_dict(),
            "notes": self.notes,
        }


@dataclass(slots=True)
class ProbeOutcome:
    brand_mentioned: bool
    brand_cited: bool
    brand_top3: bool
    brand_position: int | None = None
    competitor_mentions: list[str] = field(default_factory=list)
    raw_excerpt: str | None = None
    structured_summary: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DistributionMetric:
    metric_key: str
    subject_key: str
    probability: float
    variance: float
    ci_low: float
    ci_high: float
    sample_size: int
    engine_disagreement: float
    temporal_volatility: float
    success_count: int = 0
    scope_key: str = "campaign"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class VisibilityScoreCardView:
    ai_visibility_score: float
    measurement_confidence: str
    peacock_visibility_confidence: float
    observation_count: int
    engine_count: int
    prompt_count: int
    period_count: int
    brand_mention_probability: float
    citation_probability: float
    top3_probability: float
    competitor_probabilities: dict[str, float] = field(default_factory=dict)
    distributions: list[DistributionMetric] = field(default_factory=list)
    summary: str = ""
    computed_at: datetime | None = None
    single_shot_rejected: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "ai_visibility_score": self.ai_visibility_score,
            "measurement_confidence": self.measurement_confidence,
            "peacock_visibility_confidence": self.peacock_visibility_confidence,
            "based_on": {
                "observations": self.observation_count,
                "engines": self.engine_count,
                "prompts": self.prompt_count,
                "observation_periods": self.period_count,
            },
            "brand_mention_probability": self.brand_mention_probability,
            "citation_probability": self.citation_probability,
            "top3_recommendation_probability": self.top3_probability,
            "competitor_probabilities": self.competitor_probabilities,
            "distributions": [d.to_dict() for d in self.distributions],
            "summary": self.summary,
            "computed_at": self.computed_at.isoformat() if self.computed_at else None,
            "single_shot_rejected": True,
            "defensible": self.measurement_confidence in {"HIGH", "MEDIUM"}
            and self.observation_count >= 5,
        }
