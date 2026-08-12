"""Peacock execution modes — Fast, Standard, Deep, Council, Lab.

Every mode declares hard envelopes:
``max_cost``, ``max_calls``, ``max_iterations``, ``max_runtime``.

Modes are operational policies for PINE — not permanent model-role locks.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from time import perf_counter
from typing import Any

from intelligence.models import StrategicLayer, ThinkingDepth


class PeacockMode(StrEnum):
    FAST = "peacock_fast"
    STANDARD = "peacock_standard"
    DEEP = "peacock_deep"
    COUNCIL = "peacock_council"
    LAB = "peacock_lab"


@dataclass(slots=True)
class ModeBudget:
    """Hard resource envelope shared by every Peacock mode."""

    max_cost: int  # USD micros
    max_calls: int
    max_iterations: int
    max_runtime: float  # seconds

    # Aliases used in APIs / docs
    @property
    def max_cost_usd_micros(self) -> int:
        return self.max_cost

    @property
    def max_runtime_seconds(self) -> float:
        return self.max_runtime

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_cost": self.max_cost,
            "max_cost_usd_micros": self.max_cost,
            "max_calls": self.max_calls,
            "max_iterations": self.max_iterations,
            "max_runtime": self.max_runtime,
            "max_runtime_seconds": self.max_runtime,
        }


@dataclass(slots=True)
class ModeCapabilities:
    """What a mode is allowed / expected to do."""

    single_pass: bool = False
    multiple_evidence_sources: bool = False
    primary_reasoning_models: int = 1
    agent_count_hint: int = 1
    enable_research: bool = False
    enable_critic: bool = False
    enable_verification: bool = False
    verification_when_required: bool = False
    independent_models: bool = False
    adversarial_reasoning: bool = False
    evidence_reconciliation: bool = False
    # Lab-only experimental toolkit
    allow_repeated_measurements: bool = False
    allow_prompt_experiments: bool = False
    allow_content_simulations: bool = False
    allow_controlled_comparisons: bool = False
    allow_hypothesis_tests: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ModeProfile:
    mode: PeacockMode
    display_name: str
    summary: str
    budget: ModeBudget
    capabilities: ModeCapabilities
    thinking_depth: ThinkingDepth
    token_budget: int
    skip_layers: list[int] = field(default_factory=list)
    model_router_complexity: str = "medium"
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode.value,
            "display_name": self.display_name,
            "summary": self.summary,
            "budget": self.budget.to_dict(),
            "capabilities": self.capabilities.to_dict(),
            "thinking_depth": self.thinking_depth.value,
            "token_budget": self.token_budget,
            "skip_layers": list(self.skip_layers),
            "model_router_complexity": self.model_router_complexity,
            "notes": self.notes,
        }


PEACOCK_MODE_PROFILES: dict[PeacockMode, ModeProfile] = {
    PeacockMode.FAST: ModeProfile(
        mode=PeacockMode.FAST,
        display_name="Peacock Fast",
        summary="Single-pass, low-cost path for simple analyses.",
        budget=ModeBudget(max_cost=5_000, max_calls=12, max_iterations=1, max_runtime=30.0),
        capabilities=ModeCapabilities(
            single_pass=True,
            multiple_evidence_sources=False,
            primary_reasoning_models=1,
            agent_count_hint=1,
            enable_research=False,
            enable_critic=False,
            enable_verification=False,
            verification_when_required=False,
        ),
        thinking_depth=ThinkingDepth.SHALLOW,
        token_budget=1_500,
        # Skip research, adversarial, simulation — keep the path short
        skip_layers=[
            int(StrategicLayer.RESEARCH),
            int(StrategicLayer.ADVERSARIAL_ANALYSIS),
            int(StrategicLayer.SIMULATION),
        ],
        model_router_complexity="low",
        notes="Prefer cheapest capable model; one pass only.",
    ),
    PeacockMode.STANDARD: ModeProfile(
        mode=PeacockMode.STANDARD,
        display_name="Peacock Standard",
        summary="Multiple evidence sources, one primary reasoning model, verification when required.",
        budget=ModeBudget(max_cost=25_000, max_calls=12, max_iterations=3, max_runtime=120.0),
        capabilities=ModeCapabilities(
            single_pass=False,
            multiple_evidence_sources=True,
            primary_reasoning_models=1,
            agent_count_hint=2,
            enable_research=True,
            enable_critic=False,
            enable_verification=True,
            verification_when_required=True,
        ),
        thinking_depth=ThinkingDepth.STANDARD,
        token_budget=4_000,
        skip_layers=[],
        model_router_complexity="medium",
        notes="Default production mode for most strategic requests.",
    ),
    PeacockMode.DEEP: ModeProfile(
        mode=PeacockMode.DEEP,
        display_name="Peacock Deep",
        summary="Several agents, multiple models, research, critic, and verification.",
        budget=ModeBudget(max_cost=100_000, max_calls=40, max_iterations=8, max_runtime=600.0),
        capabilities=ModeCapabilities(
            single_pass=False,
            multiple_evidence_sources=True,
            primary_reasoning_models=3,
            agent_count_hint=5,
            enable_research=True,
            enable_critic=True,
            enable_verification=True,
            verification_when_required=False,  # always on
            adversarial_reasoning=True,
        ),
        thinking_depth=ThinkingDepth.DEEP,
        token_budget=8_000,
        skip_layers=[],
        model_router_complexity="high",
        notes="Multi-agent depth for complex visibility / SEO / GEO work.",
    ),
    PeacockMode.COUNCIL: ModeProfile(
        mode=PeacockMode.COUNCIL,
        display_name="Peacock Council",
        summary="Strategic decisions via independent models, adversarial reasoning, and evidence reconciliation.",
        budget=ModeBudget(max_cost=200_000, max_calls=60, max_iterations=12, max_runtime=900.0),
        capabilities=ModeCapabilities(
            single_pass=False,
            multiple_evidence_sources=True,
            primary_reasoning_models=4,
            agent_count_hint=7,
            enable_research=True,
            enable_critic=True,
            enable_verification=True,
            independent_models=True,
            adversarial_reasoning=True,
            evidence_reconciliation=True,
        ),
        thinking_depth=ThinkingDepth.COUNCIL,
        token_budget=12_000,
        skip_layers=[],
        model_router_complexity="critical",
        notes="Board-level / high-risk decisions; reconcile conflicting evidence.",
    ),
    PeacockMode.LAB: ModeProfile(
        mode=PeacockMode.LAB,
        display_name="Peacock Lab",
        summary="Experimental research mode for measurements, prompt experiments, simulations, comparisons, and hypothesis tests.",
        budget=ModeBudget(max_cost=150_000, max_calls=80, max_iterations=20, max_runtime=1_200.0),
        capabilities=ModeCapabilities(
            single_pass=False,
            multiple_evidence_sources=True,
            primary_reasoning_models=3,
            agent_count_hint=6,
            enable_research=True,
            enable_critic=True,
            enable_verification=True,
            independent_models=True,
            adversarial_reasoning=True,
            evidence_reconciliation=True,
            allow_repeated_measurements=True,
            allow_prompt_experiments=True,
            allow_content_simulations=True,
            allow_controlled_comparisons=True,
            allow_hypothesis_tests=True,
        ),
        thinking_depth=ThinkingDepth.DEEP,  # deepest non-council depth class for context budgets
        token_budget=10_000,
        skip_layers=[],
        model_router_complexity="high",
        notes="Sandbox for experimental PINE research — still budget-capped.",
    ),
}


@dataclass(slots=True)
class LabExperimentPlan:
    """Optional Lab workplan — only valid when mode is Peacock Lab."""

    repeated_measurements: bool = False
    prompt_experiments: bool = False
    content_simulations: bool = False
    controlled_comparisons: bool = False
    hypothesis_tests: bool = False
    hypotheses: list[str] = field(default_factory=list)
    comparison_arms: list[str] = field(default_factory=list)
    measurement_rounds: int = 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ModeBudgetUsage:
    cost_usd_micros: int = 0
    calls: int = 0
    iterations: int = 0
    runtime_seconds: float = 0.0
    stopped_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ModeBudgetTracker:
    """Enforce max_cost / max_calls / max_iterations / max_runtime for a run."""

    def __init__(self, budget: ModeBudget) -> None:
        self.budget = budget
        self.usage = ModeBudgetUsage()
        self._started = perf_counter()

    def record_call(self, *, cost_usd_micros: int = 0) -> None:
        self.usage.calls += 1
        self.usage.cost_usd_micros += max(0, cost_usd_micros)
        self._refresh_runtime()

    def record_iteration(self) -> None:
        self.usage.iterations += 1
        self._refresh_runtime()

    def _refresh_runtime(self) -> None:
        self.usage.runtime_seconds = perf_counter() - self._started

    def remaining(self) -> dict[str, float | int]:
        self._refresh_runtime()
        return {
            "cost": max(0, self.budget.max_cost - self.usage.cost_usd_micros),
            "calls": max(0, self.budget.max_calls - self.usage.calls),
            "iterations": max(0, self.budget.max_iterations - self.usage.iterations),
            "runtime": max(0.0, self.budget.max_runtime - self.usage.runtime_seconds),
        }

    def exhausted(self) -> str | None:
        self._refresh_runtime()
        if self.usage.cost_usd_micros >= self.budget.max_cost:
            return "max_cost"
        if self.usage.calls >= self.budget.max_calls:
            return "max_calls"
        if self.usage.iterations >= self.budget.max_iterations:
            return "max_iterations"
        if self.usage.runtime_seconds >= self.budget.max_runtime:
            return "max_runtime"
        return None

    def checkpoint(self) -> bool:
        """Return True if the run may continue; False if a budget was hit."""
        reason = self.exhausted()
        if reason:
            self.usage.stopped_reason = reason
            return False
        return True

    def snapshot(self) -> dict[str, Any]:
        self._refresh_runtime()
        return {
            "budget": self.budget.to_dict(),
            "usage": self.usage.to_dict(),
            "remaining": self.remaining(),
            "exhausted": self.exhausted(),
        }


def resolve_mode(
    *,
    explicit: str | PeacockMode | None = None,
    thinking_depth: ThinkingDepth | None = None,
    request_text: str = "",
) -> PeacockMode:
    """Resolve Peacock mode from explicit override, depth, or request text cues."""
    if explicit is not None:
        return PeacockMode(str(explicit))

    lower = request_text.lower()
    if any(k in lower for k in ("peacock lab", "lab mode", "experiment", "hypothesis test", "a/b test", "prompt experiment")):
        return PeacockMode.LAB
    if any(k in lower for k in ("council", "board", "strategic decision", "adversarial council")):
        return PeacockMode.COUNCIL
    if any(k in lower for k in ("deep dive", "multi-agent", "peacock deep")):
        return PeacockMode.DEEP
    if any(k in lower for k in ("quick", "fast", "summary", "peacock fast", "single pass")):
        return PeacockMode.FAST

    if thinking_depth == ThinkingDepth.SHALLOW:
        return PeacockMode.FAST
    if thinking_depth == ThinkingDepth.DEEP:
        return PeacockMode.DEEP
    if thinking_depth == ThinkingDepth.COUNCIL:
        return PeacockMode.COUNCIL
    return PeacockMode.STANDARD


def profile_for(mode: PeacockMode | str) -> ModeProfile:
    return PEACOCK_MODE_PROFILES[PeacockMode(str(mode))]


def list_mode_catalog() -> list[dict[str, Any]]:
    return [profile_for(mode).to_dict() for mode in PeacockMode]
