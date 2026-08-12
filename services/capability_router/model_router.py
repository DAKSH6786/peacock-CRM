"""ModelRouter — constrained multi-model selection for PINE.

Builds on capability profiles. Soft priors are defaults only; observed
workspace performance and organisation policy drive the final choice.
Never permanently locks Claude=critic / Perplexity=research / GPT=strategy.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any

from capability_router.models import CapabilityTaskType, RoutingCandidate
from capability_router.router import CapabilityRouter
from sqlalchemy import select
from sqlalchemy.orm import Session

from db_models import AiProvider, AiProviderModel


class TaskComplexity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FreshnessRequirement(StrEnum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    REALTIME = "realtime"


# Soft catalog hints when DB context windows are missing — not routing locks
_MODEL_CONTEXT_HINTS: dict[tuple[str, str], int] = {
    ("openai", "gpt-4.1"): 128_000,
    ("anthropic", "claude-sonnet"): 200_000,
    ("gemini", "gemini-2.0-flash"): 1_000_000,
    ("perplexity", "sonar"): 128_000,
    ("deepseek", "deepseek-chat"): 64_000,
}

_WEB_GROUNDING_PROVIDERS = frozenset({"perplexity"})


@dataclass(slots=True)
class OrganisationPolicy:
    """Tenant policy constraints for model selection."""

    allowed_providers: list[str] = field(default_factory=list)
    denied_providers: list[str] = field(default_factory=list)
    allowed_models: list[str] = field(default_factory=list)  # "provider/model"
    denied_models: list[str] = field(default_factory=list)
    max_cost_usd_micros: int | None = None
    prefer_observed: bool = True
    require_json_capable: bool = False
    prefer_eu_compatible: bool = False
    notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ModelRouterRequest:
    task_type: str | CapabilityTaskType
    complexity: TaskComplexity | str = TaskComplexity.MEDIUM
    freshness_requirement: FreshnessRequirement | str = FreshnessRequirement.NONE
    required_capabilities: list[str] = field(default_factory=list)
    expected_context_size: int = 8_000
    accuracy_requirement: float = 0.7
    latency_target: float = 5_000.0  # ms
    budget: int = 50_000  # USD micros ceiling for a single call
    organisation_policy: OrganisationPolicy = field(default_factory=OrganisationPolicy)
    organisation_id: str | None = None
    workspace_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_type": str(self.task_type),
            "complexity": str(self.complexity),
            "freshness_requirement": str(self.freshness_requirement),
            "required_capabilities": list(self.required_capabilities),
            "expected_context_size": self.expected_context_size,
            "accuracy_requirement": self.accuracy_requirement,
            "latency_target": self.latency_target,
            "budget": self.budget,
            "organisation_policy": self.organisation_policy.to_dict(),
            "organisation_id": self.organisation_id,
            "workspace_id": self.workspace_id,
        }


@dataclass(slots=True)
class ModelChoice:
    provider_code: str
    model_code: str
    score: float
    source: str
    sample_size: int = 0
    estimated_latency_ms: float = 0.0
    estimated_cost_usd_micros: float = 0.0
    estimated_quality: float = 0.0
    context_window_tokens: int | None = None
    fits_constraints: bool = True
    constraint_notes: list[str] = field(default_factory=list)

    @property
    def key(self) -> str:
        return f"{self.provider_code}/{self.model_code}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_code": self.provider_code,
            "model_code": self.model_code,
            "key": self.key,
            "score": self.score,
            "source": self.source,
            "sample_size": self.sample_size,
            "estimated_latency_ms": self.estimated_latency_ms,
            "estimated_cost_usd_micros": self.estimated_cost_usd_micros,
            "estimated_quality": self.estimated_quality,
            "context_window_tokens": self.context_window_tokens,
            "fits_constraints": self.fits_constraints,
            "constraint_notes": list(self.constraint_notes),
        }


@dataclass(slots=True)
class ModelRouterResult:
    primary_model: ModelChoice
    secondary_model: ModelChoice | None
    fallback_model: ModelChoice | None
    reason: str
    task_type: str
    candidates_considered: int = 0
    constraints_applied: list[str] = field(default_factory=list)
    permanent_role_locks: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "primary_model": self.primary_model.to_dict(),
            "secondary_model": self.secondary_model.to_dict() if self.secondary_model else None,
            "fallback_model": self.fallback_model.to_dict() if self.fallback_model else None,
            "reason": self.reason,
            "task_type": self.task_type,
            "candidates_considered": self.candidates_considered,
            "constraints_applied": list(self.constraints_applied),
            "permanent_role_locks": False,
        }


class ModelRouter:
    """Select primary / secondary / fallback models under request constraints."""

    def __init__(
        self,
        capability_router: CapabilityRouter,
        session: Session | None = None,
    ) -> None:
        self.capability_router = capability_router
        self.session = session

    def route(self, request: ModelRouterRequest) -> ModelRouterResult:
        if not request.organisation_id or not request.workspace_id:
            raise ValueError("organisation_id and workspace_id are required")

        task_type = str(request.task_type)
        complexity = TaskComplexity(str(request.complexity))
        freshness = FreshnessRequirement(str(request.freshness_requirement))
        policy = request.organisation_policy

        allowed = set(policy.allowed_providers) or None
        if policy.denied_providers and allowed is not None:
            allowed = {p for p in allowed if p not in set(policy.denied_providers)}

        base = self.capability_router.route(
            organisation_id=request.organisation_id,
            workspace_id=request.workspace_id,
            task_type=task_type,
            allowed_providers=allowed,
        )
        candidates = list(base.candidates)

        # Expand thin pools so secondary/fallback can diversify across providers
        if len(candidates) < 3:
            seen = {(c.provider_code, c.model_code) for c in candidates}
            for extra_task in self._adjacent_tasks(task_type):
                extra = self.capability_router.route(
                    organisation_id=request.organisation_id,
                    workspace_id=request.workspace_id,
                    task_type=extra_task,
                    allowed_providers=allowed,
                )
                for candidate in extra.candidates:
                    key = (candidate.provider_code, candidate.model_code)
                    if key in seen:
                        continue
                    candidates.append(
                        RoutingCandidate(
                            provider_code=candidate.provider_code,
                            model_code=candidate.model_code,
                            task_type=candidate.task_type,
                            score=candidate.score * 0.85,
                            metrics=candidate.metrics,
                            sample_size=candidate.sample_size,
                            source=candidate.source,
                            breakdown={
                                **candidate.breakdown,
                                "adjacent_task_penalty": -0.15,
                            },
                        )
                    )
                    seen.add(key)
                if len(candidates) >= 5:
                    break

        catalog = self._load_catalog()
        constraints_applied: list[str] = [
            f"task_type={task_type}",
            f"complexity={complexity.value}",
            f"freshness={freshness.value}",
            f"accuracy>={request.accuracy_requirement:.2f}",
            f"latency_target_ms<={request.latency_target:.0f}",
            f"budget_usd_micros<={request.budget}",
            f"context_tokens>={request.expected_context_size}",
        ]
        if request.required_capabilities:
            constraints_applied.append(
                "required_capabilities=" + ",".join(request.required_capabilities)
            )
        if policy.denied_providers:
            constraints_applied.append("denied_providers=" + ",".join(policy.denied_providers))
        if policy.allowed_providers:
            constraints_applied.append("allowed_providers=" + ",".join(policy.allowed_providers))

        scored: list[ModelChoice] = []
        for candidate in candidates:
            if candidate.provider_code in set(policy.denied_providers):
                continue
            key = f"{candidate.provider_code}/{candidate.model_code}"
            if policy.denied_models and key in set(policy.denied_models):
                continue
            if policy.allowed_models and key not in set(policy.allowed_models):
                continue
            if allowed is not None and candidate.provider_code not in allowed:
                continue

            choice = self._evaluate_candidate(
                candidate=candidate,
                request=request,
                complexity=complexity,
                freshness=freshness,
                catalog=catalog,
            )
            # Hard filter: must meet accuracy if we have signal
            if (
                choice.estimated_quality < request.accuracy_requirement
                and choice.sample_size > 0
                and choice.source != "prior"
            ):
                choice.fits_constraints = False
                choice.constraint_notes.append("below_accuracy_requirement")
            scored.append(choice)

        # Prefer constraint-fitting candidates for primary; keep others for failover
        fitting = [c for c in scored if c.fits_constraints]
        primary_pool = sorted(fitting if fitting else scored, key=lambda c: c.score, reverse=True)
        diversity_pool = sorted(scored, key=lambda c: c.score, reverse=True)

        if not primary_pool:
            null_choice = ModelChoice(
                provider_code="null",
                model_code="null",
                score=0.0,
                source="fallback",
                constraint_notes=["no_candidates"],
            )
            return ModelRouterResult(
                primary_model=null_choice,
                secondary_model=None,
                fallback_model=None,
                reason="No models satisfied organisation policy or capability priors.",
                task_type=task_type,
                candidates_considered=0,
                constraints_applied=constraints_applied,
            )

        primary = primary_pool[0]
        secondary = self._next_diverse(diversity_pool, primary, start=0)
        fallback = self._next_diverse(
            diversity_pool,
            primary,
            start=0,
            also_avoid=secondary.key if secondary else None,
        )

        reason = self._build_reason(
            request=request,
            complexity=complexity,
            freshness=freshness,
            primary=primary,
            secondary=secondary,
            fallback=fallback,
            constraints_applied=constraints_applied,
        )
        return ModelRouterResult(
            primary_model=primary,
            secondary_model=secondary,
            fallback_model=fallback,
            reason=reason,
            task_type=task_type,
            candidates_considered=len(scored),
            constraints_applied=constraints_applied,
        )

    def _evaluate_candidate(
        self,
        *,
        candidate: RoutingCandidate,
        request: ModelRouterRequest,
        complexity: TaskComplexity,
        freshness: FreshnessRequirement,
        catalog: dict[tuple[str, str], dict[str, Any]],
    ) -> ModelChoice:
        meta = catalog.get((candidate.provider_code, candidate.model_code), {})
        context_window = meta.get("context_window_tokens") or _MODEL_CONTEXT_HINTS.get(
            (candidate.provider_code, candidate.model_code)
        )
        web_grounded = bool(meta.get("supports_web_grounding")) or (
            candidate.provider_code in _WEB_GROUNDING_PROVIDERS
        )

        notes: list[str] = []
        score = candidate.score
        fits = True

        # Complexity re-weights quality vs cost/latency
        if complexity in {TaskComplexity.HIGH, TaskComplexity.CRITICAL}:
            score += 0.25 * candidate.metrics.quality
            score -= 0.05 * _clamp01(candidate.metrics.cost_usd_micros / max(request.budget, 1))
            notes.append("complexity_boost_quality")
        elif complexity == TaskComplexity.LOW:
            score += 0.15 * (1.0 - _clamp01(candidate.metrics.latency_ms / max(request.latency_target, 1)))
            score += 0.1 * (1.0 - _clamp01(candidate.metrics.cost_usd_micros / max(request.budget, 1)))
            notes.append("complexity_boost_efficiency")

        # Freshness prefers web-grounded providers; does not permanently lock Perplexity
        if freshness in {FreshnessRequirement.HIGH, FreshnessRequirement.REALTIME}:
            if web_grounded:
                score += 0.18
                notes.append("freshness_web_grounding_bonus")
            else:
                score -= 0.12
                notes.append("freshness_no_web_grounding_penalty")
                if freshness == FreshnessRequirement.REALTIME:
                    fits = False
                    notes.append("realtime_requires_web_grounding")
        elif freshness == FreshnessRequirement.MEDIUM and web_grounded:
            score += 0.06
            notes.append("freshness_mild_web_bonus")

        # Required capabilities (task codes or feature flags)
        for capability in request.required_capabilities:
            cap = capability.strip().upper()
            if cap in {"WEB_GROUNDING", "FRESH_WEB", "LIVE_WEB"}:
                if web_grounded:
                    score += 0.08
                else:
                    fits = False
                    notes.append(f"missing_capability:{cap}")
            elif cap in {"STRUCTURED_OUTPUT", "JSON"}:
                if candidate.metrics.json_compliance >= 0.75:
                    score += 0.08
                else:
                    score -= 0.1
                    notes.append("weak_json_compliance")
                    if request.organisation_policy.require_json_capable:
                        fits = False
            elif cap == "LONG_CONTEXT":
                if context_window and context_window >= max(100_000, request.expected_context_size):
                    score += 0.08
                else:
                    notes.append("weak_long_context")
            elif cap in {t.value for t in CapabilityTaskType}:
                # Extra task affinity already partly in base score; small bonus if prior/observed
                if candidate.task_type == cap:
                    score += 0.04

        # Context window hard/soft constraints
        if context_window is not None:
            if context_window < request.expected_context_size:
                fits = False
                notes.append("context_window_too_small")
                score -= 0.25
            else:
                headroom = context_window / max(request.expected_context_size, 1)
                if headroom >= 2:
                    score += 0.04
        else:
            notes.append("context_window_unknown")

        # Latency target
        if candidate.metrics.latency_ms > request.latency_target:
            overshoot = candidate.metrics.latency_ms / max(request.latency_target, 1.0)
            score -= min(0.3, 0.12 * overshoot)
            notes.append("above_latency_target")
            if overshoot > 2.0 and complexity == TaskComplexity.LOW:
                fits = False

        # Budget
        policy_cap = request.organisation_policy.max_cost_usd_micros
        budget = request.budget
        if policy_cap is not None:
            budget = min(budget, policy_cap)
        if candidate.metrics.cost_usd_micros > budget:
            score -= 0.2
            notes.append("above_budget")
            if candidate.metrics.cost_usd_micros > budget * 1.5:
                fits = False

        # Accuracy requirement soft pressure
        if candidate.metrics.quality + 1e-9 < request.accuracy_requirement:
            gap = request.accuracy_requirement - candidate.metrics.quality
            score -= 0.35 * gap
            notes.append("below_accuracy_requirement")

        # Prefer observed when policy asks
        if request.organisation_policy.prefer_observed and candidate.source == "observed":
            score += 0.05
            notes.append("observed_preference")
        elif request.organisation_policy.prefer_observed and candidate.source == "prior":
            score -= 0.03

        return ModelChoice(
            provider_code=candidate.provider_code,
            model_code=candidate.model_code,
            score=score,
            source=candidate.source,
            sample_size=candidate.sample_size,
            estimated_latency_ms=candidate.metrics.latency_ms,
            estimated_cost_usd_micros=candidate.metrics.cost_usd_micros,
            estimated_quality=candidate.metrics.quality,
            context_window_tokens=context_window,
            fits_constraints=fits,
            constraint_notes=notes,
        )

    def _load_catalog(self) -> dict[tuple[str, str], dict[str, Any]]:
        if self.session is None:
            return {}
        rows = self.session.execute(
            select(
                AiProvider.code,
                AiProvider.supports_web_grounding,
                AiProviderModel.model_code,
                AiProviderModel.context_window_tokens,
                AiProviderModel.is_active,
            ).join(AiProviderModel, AiProviderModel.provider_id == AiProvider.id)
        ).all()
        out: dict[tuple[str, str], dict[str, Any]] = {}
        for provider_code, web, model_code, ctx, is_active in rows:
            if not is_active:
                continue
            out[(provider_code, model_code)] = {
                "supports_web_grounding": bool(web),
                "context_window_tokens": ctx,
            }
        return out

    @staticmethod
    def _adjacent_tasks(task_type: str) -> list[str]:
        adjacency: dict[str, list[str]] = {
            "RESEARCH": ["CITATION_EXTRACTION", "FACT_VERIFICATION", "STRATEGY"],
            "STRATEGY": ["SUMMARISATION", "CRITICAL_ANALYSIS", "SEO_REASONING"],
            "CRITICAL_ANALYSIS": ["FACT_VERIFICATION", "STRATEGY", "CONTENT_ANALYSIS"],
            "SEO_REASONING": ["CONTENT_ANALYSIS", "COMPETITOR_ANALYSIS", "STRATEGY"],
            "GEO_REASONING": ["RESEARCH", "CITATION_EXTRACTION", "STRATEGY"],
            "LONG_CONTEXT_ANALYSIS": ["SUMMARISATION", "STRATEGY", "CONTENT_ANALYSIS"],
            "STRUCTURED_OUTPUT": ["STRATEGY", "ENTITY_EXTRACTION", "SUMMARISATION"],
        }
        return adjacency.get(task_type, ["STRATEGY", "SUMMARISATION", "CONTENT_ANALYSIS"])

    @staticmethod
    def _next_diverse(
        pool: list[ModelChoice],
        primary: ModelChoice,
        *,
        start: int,
        also_avoid: str | None = None,
    ) -> ModelChoice | None:
        for choice in pool[start:]:
            if choice.key == primary.key:
                continue
            if also_avoid and choice.key == also_avoid:
                continue
            # Prefer a different provider for resilience when possible
            if choice.provider_code != primary.provider_code:
                return choice
        for choice in pool[start:]:
            if choice.key != primary.key and choice.key != also_avoid:
                return choice
        return None

    @staticmethod
    def _build_reason(
        *,
        request: ModelRouterRequest,
        complexity: TaskComplexity,
        freshness: FreshnessRequirement,
        primary: ModelChoice,
        secondary: ModelChoice | None,
        fallback: ModelChoice | None,
        constraints_applied: list[str],
    ) -> str:
        parts = [
            f"Primary {primary.key} selected for {request.task_type} "
            f"(score={primary.score:.3f}, source={primary.source}, samples={primary.sample_size}).",
            f"Constraints: complexity={complexity.value}, freshness={freshness.value}, "
            f"accuracy>={request.accuracy_requirement:.2f}, latency<={request.latency_target:.0f}ms, "
            f"budget<={request.budget}µ$, context>={request.expected_context_size}.",
        ]
        if primary.constraint_notes:
            parts.append("Primary notes: " + ", ".join(primary.constraint_notes) + ".")
        if secondary:
            parts.append(
                f"Secondary {secondary.key} (score={secondary.score:.3f}) for failover diversity."
            )
        if fallback:
            parts.append(
                f"Fallback {fallback.key} (score={fallback.score:.3f}) as last resort."
            )
        parts.append(
            "Selection is dynamic from capability profiles + policy; "
            "no permanent provider role locks were applied."
        )
        if constraints_applied:
            parts.append("Applied: " + "; ".join(constraints_applied[:8]) + ".")
        return " ".join(parts)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))
