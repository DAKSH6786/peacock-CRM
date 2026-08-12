"""Typed contracts for dynamic model capability profiles."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class CapabilityTaskType(StrEnum):
    RESEARCH = "RESEARCH"
    SEO_REASONING = "SEO_REASONING"
    GEO_REASONING = "GEO_REASONING"
    ENTITY_EXTRACTION = "ENTITY_EXTRACTION"
    CITATION_EXTRACTION = "CITATION_EXTRACTION"
    STRUCTURED_OUTPUT = "STRUCTURED_OUTPUT"
    CRITICAL_ANALYSIS = "CRITICAL_ANALYSIS"
    SUMMARISATION = "SUMMARISATION"
    STRATEGY = "STRATEGY"
    CONTENT_ANALYSIS = "CONTENT_ANALYSIS"
    COMPETITOR_ANALYSIS = "COMPETITOR_ANALYSIS"
    FACT_VERIFICATION = "FACT_VERIFICATION"
    LONG_CONTEXT_ANALYSIS = "LONG_CONTEXT_ANALYSIS"


@dataclass(slots=True)
class CapabilityMetrics:
    quality: float = 0.0
    latency_ms: float = 0.0
    cost_usd_micros: float = 0.0
    failure_rate: float = 0.0
    json_compliance: float = 0.0
    citation_accuracy: float = 0.0
    historical_agreement: float = 0.0

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass(slots=True)
class CapabilityProfile:
    provider_code: str
    model_code: str
    task_type: CapabilityTaskType | str
    metrics: CapabilityMetrics
    sample_size: int = 0
    success_count: int = 0
    failure_count: int = 0
    source: str = "observed"  # observed | prior | blended
    id: str | None = None
    last_observed_at: datetime | None = None
    prior_weight: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "provider_code": self.provider_code,
            "model_code": self.model_code,
            "task_type": str(self.task_type),
            "metrics": self.metrics.to_dict(),
            "sample_size": self.sample_size,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "source": self.source,
            "prior_weight": self.prior_weight,
            "last_observed_at": self.last_observed_at.isoformat()
            if self.last_observed_at
            else None,
        }


@dataclass(slots=True)
class CapabilityObservation:
    provider_code: str
    model_code: str
    task_type: CapabilityTaskType | str
    latency_ms: float
    cost_usd_micros: int = 0
    succeeded: bool = True
    quality_score: float | None = None
    json_compliant: bool | None = None
    citation_accuracy: float | None = None
    historical_agreement: float | None = None
    gateway_role: str | None = None
    template_id: str | None = None
    llm_request_id: str | None = None
    notes: str | None = None
    id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["task_type"] = str(self.task_type)
        return payload


@dataclass(slots=True)
class RoutingWeights:
    """Weights for dynamic routing score. Tunable; not provider locks."""

    quality: float = 0.35
    json_compliance: float = 0.15
    citation_accuracy: float = 0.1
    historical_agreement: float = 0.1
    latency: float = 0.15
    cost: float = 0.1
    failure: float = 0.15


@dataclass(slots=True)
class RoutingCandidate:
    provider_code: str
    model_code: str
    task_type: str
    score: float
    metrics: CapabilityMetrics
    sample_size: int
    source: str
    breakdown: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_code": self.provider_code,
            "model_code": self.model_code,
            "task_type": self.task_type,
            "score": self.score,
            "metrics": self.metrics.to_dict(),
            "sample_size": self.sample_size,
            "source": self.source,
            "breakdown": self.breakdown,
        }


@dataclass(slots=True)
class RoutingDecision:
    task_type: str
    selected: RoutingCandidate
    candidates: list[RoutingCandidate]
    used_prior_only: bool
    min_samples_for_trust: int
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_type": self.task_type,
            "selected": self.selected.to_dict(),
            "candidates": [c.to_dict() for c in self.candidates],
            "used_prior_only": self.used_prior_only,
            "min_samples_for_trust": self.min_samples_for_trust,
            "rationale": self.rationale,
            "permanent_role_locks": False,
        }
