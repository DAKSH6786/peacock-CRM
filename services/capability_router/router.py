"""Dynamic PINE capability router — no permanent provider role locks."""

from __future__ import annotations

from capability_router.models import (
    CapabilityMetrics,
    CapabilityProfile,
    CapabilityTaskType,
    RoutingCandidate,
    RoutingDecision,
    RoutingWeights,
)
from capability_router.priors import GATEWAY_ROLE_TASK_DEFAULTS, SOFT_CAPABILITY_PRIORS
from capability_router.repository import CapabilityProfileRepository


class CapabilityRouter:
    """Select provider/model for a task from observed profiles + soft priors.

    Soft priors (e.g. Perplexity→research) are **defaults only**. Once a
    workspace has enough samples, observed metrics dominate routing.
    """

    def __init__(
        self,
        repository: CapabilityProfileRepository,
        *,
        weights: RoutingWeights | None = None,
        min_samples_for_trust: int = 5,
        prior_blend_until_samples: int = 20,
    ) -> None:
        self.repository = repository
        self.weights = weights or RoutingWeights()
        self.min_samples_for_trust = min_samples_for_trust
        self.prior_blend_until_samples = prior_blend_until_samples

    @staticmethod
    def task_type_for_gateway_role(role: str, explicit: str | None = None) -> str:
        if explicit:
            return explicit
        return GATEWAY_ROLE_TASK_DEFAULTS.get(role, "STRATEGY")

    def route(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        task_type: str | CapabilityTaskType,
        allowed_providers: set[str] | None = None,
    ) -> RoutingDecision:
        task = str(task_type)
        try:
            CapabilityTaskType(task)
        except ValueError as exc:
            raise ValueError(f"Unsupported task_type: {task}") from exc

        observed = self.repository.list_profiles(
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            task_type=task,
        )
        priors = self.repository.list_priors(task_type=task)
        if not priors:
            # Fall back to in-code soft priors if DB not seeded yet
            priors = [
                CapabilityProfile(
                    provider_code=p.provider_code,
                    model_code=p.model_code,
                    task_type=p.task_type,
                    metrics=CapabilityMetrics(
                        quality=p.quality_score,
                        latency_ms=p.latency_ms,
                        cost_usd_micros=float(p.cost_usd_micros),
                        failure_rate=p.failure_rate,
                        json_compliance=p.json_compliance_rate,
                        citation_accuracy=p.citation_accuracy,
                        historical_agreement=p.historical_agreement,
                    ),
                    source="prior",
                    prior_weight=p.prior_weight,
                )
                for p in SOFT_CAPABILITY_PRIORS
                if p.task_type == task
            ]

        blended = self._blend_candidates(observed=observed, priors=priors)
        if allowed_providers:
            blended = [c for c in blended if c.provider_code in allowed_providers]

        if not blended:
            # Absolute last resort — still not a permanent lock
            fallback = RoutingCandidate(
                provider_code="null",
                model_code="null",
                task_type=task,
                score=0.0,
                metrics=CapabilityMetrics(),
                sample_size=0,
                source="fallback",
                breakdown={"reason": 0.0},
            )
            return RoutingDecision(
                task_type=task,
                selected=fallback,
                candidates=[fallback],
                used_prior_only=True,
                min_samples_for_trust=self.min_samples_for_trust,
                rationale="No capability profiles or priors available; null fallback.",
            )

        ranked = sorted(blended, key=lambda c: c.score, reverse=True)
        selected = ranked[0]
        used_prior_only = selected.source in {"prior", "fallback"} or selected.sample_size == 0
        rationale = (
            f"Selected {selected.provider_code}/{selected.model_code} for {task} "
            f"via dynamic score={selected.score:.3f} (source={selected.source}, "
            f"samples={selected.sample_size}). Soft priors are not permanent locks."
        )
        return RoutingDecision(
            task_type=task,
            selected=selected,
            candidates=ranked,
            used_prior_only=used_prior_only,
            min_samples_for_trust=self.min_samples_for_trust,
            rationale=rationale,
        )

    def _blend_candidates(
        self,
        *,
        observed: list[CapabilityProfile],
        priors: list[CapabilityProfile],
    ) -> list[RoutingCandidate]:
        by_key: dict[tuple[str, str], CapabilityProfile] = {
            (p.provider_code, p.model_code): p for p in priors
        }
        for row in observed:
            key = (row.provider_code, row.model_code)
            prior = by_key.get(key)
            if prior is None or row.sample_size >= self.prior_blend_until_samples:
                by_key[key] = row
                continue
            # Blend prior → observed until enough samples accumulate
            t = row.sample_size / float(self.prior_blend_until_samples)
            by_key[key] = CapabilityProfile(
                provider_code=row.provider_code,
                model_code=row.model_code,
                task_type=row.task_type,
                metrics=CapabilityMetrics(
                    quality=_lerp(prior.metrics.quality, row.metrics.quality, t),
                    latency_ms=_lerp(prior.metrics.latency_ms, row.metrics.latency_ms, t),
                    cost_usd_micros=_lerp(
                        prior.metrics.cost_usd_micros, row.metrics.cost_usd_micros, t
                    ),
                    failure_rate=_lerp(prior.metrics.failure_rate, row.metrics.failure_rate, t),
                    json_compliance=_lerp(
                        prior.metrics.json_compliance, row.metrics.json_compliance, t
                    ),
                    citation_accuracy=_lerp(
                        prior.metrics.citation_accuracy, row.metrics.citation_accuracy, t
                    ),
                    historical_agreement=_lerp(
                        prior.metrics.historical_agreement,
                        row.metrics.historical_agreement,
                        t,
                    ),
                ),
                sample_size=row.sample_size,
                success_count=row.success_count,
                failure_count=row.failure_count,
                source="blended",
                id=row.id,
                last_observed_at=row.last_observed_at,
                prior_weight=prior.prior_weight,
            )

        # Include observed models that had no prior
        for row in observed:
            key = (row.provider_code, row.model_code)
            if key not in by_key:
                by_key[key] = row

        candidates: list[RoutingCandidate] = []
        metrics_list = [p.metrics for p in by_key.values()]
        for profile in by_key.values():
            score, breakdown = self._score(profile.metrics, metrics_list)
            # Slight trust bonus once enough samples exist — still not a lock
            if profile.sample_size >= self.min_samples_for_trust:
                score += 0.02
                breakdown["sample_trust_bonus"] = 0.02
            elif profile.source == "prior":
                score *= 0.92  # soft-prior discount vs observed
                breakdown["prior_discount"] = -0.08
            candidates.append(
                RoutingCandidate(
                    provider_code=profile.provider_code,
                    model_code=profile.model_code,
                    task_type=str(profile.task_type),
                    score=score,
                    metrics=profile.metrics,
                    sample_size=profile.sample_size,
                    source=profile.source,
                    breakdown=breakdown,
                )
            )
        return candidates

    def _score(
        self,
        metrics: CapabilityMetrics,
        cohort: list[CapabilityMetrics],
    ) -> tuple[float, dict[str, float]]:
        w = self.weights
        lat_norm = _normalise_costlike(metrics.latency_ms, [m.latency_ms for m in cohort])
        cost_norm = _normalise_costlike(
            metrics.cost_usd_micros, [m.cost_usd_micros for m in cohort]
        )
        breakdown = {
            "quality": w.quality * metrics.quality,
            "json_compliance": w.json_compliance * metrics.json_compliance,
            "citation_accuracy": w.citation_accuracy * metrics.citation_accuracy,
            "historical_agreement": w.historical_agreement * metrics.historical_agreement,
            "latency_penalty": -w.latency * lat_norm,
            "cost_penalty": -w.cost * cost_norm,
            "failure_penalty": -w.failure * metrics.failure_rate,
        }
        return sum(breakdown.values()), breakdown


def _lerp(a: float, b: float, t: float) -> float:
    t = max(0.0, min(1.0, t))
    return a * (1.0 - t) + b * t


def _normalise_costlike(value: float, cohort: list[float]) -> float:
    if not cohort:
        return 0.0
    lo = min(cohort)
    hi = max(cohort)
    if hi <= lo:
        return 0.0
    return (value - lo) / (hi - lo)
