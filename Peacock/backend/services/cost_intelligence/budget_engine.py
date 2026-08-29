"""Intelligence Budget Engine — pre-flight estimates + cheapest reliable choice."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

from db_models.cost_intelligence import (
    CHEAPEST_RELIABLE_POLICY,
    COST_POSITIONING,
    DECISION_VALUE_LABELS,
    DECISION_VALUES,
    METHOD_KIND_LABELS,
    METHOD_KINDS,
    METHOD_LADDER,
    METHODOLOGY_NOTE,
    VALUE_METHOD_CEILING,
    WORKFLOW_INTENTS,
)


# Intent → preferred minimum reliable method + decision value default
INTENT_DEFAULTS: dict[str, dict[str, Any]] = {
    "page_title_recommendation": {
        "decision_value": "trivial",
        "min_reliable": "deterministic",
        "notes": "Page titles are solved by rules + templates, not Council.",
    },
    "meta_description": {
        "decision_value": "trivial",
        "min_reliable": "deterministic",
        "notes": "Meta copy uses deterministic patterns first.",
    },
    "simple_seo_check": {
        "decision_value": "low",
        "min_reliable": "deterministic",
        "notes": "Crawl/SEO scores answer without multi-LLM.",
    },
    "share_of_answer_lookup": {
        "decision_value": "low",
        "min_reliable": "deterministic",
        "notes": "Stored indicators — no five-LLM stack.",
    },
    "citation_lookup": {
        "decision_value": "low",
        "min_reliable": "deterministic",
        "notes": "Citation graph query is deterministic data.",
    },
    "content_brief": {
        "decision_value": "medium",
        "min_reliable": "single_llm",
        "notes": "One synthesis pass is enough for most briefs.",
    },
    "writer_assignment": {
        "decision_value": "medium",
        "min_reliable": "deterministic",
        "notes": "Writer DNA + outcomes can rank without Council.",
    },
    "entity_gap_analysis": {
        "decision_value": "medium",
        "min_reliable": "single_llm",
        "notes": "Graph gaps + light synthesis.",
    },
    "competitor_response": {
        "decision_value": "high",
        "min_reliable": "multi_llm",
        "notes": "Competitive moves may need research + critic.",
    },
    "geo_strategy": {
        "decision_value": "high",
        "min_reliable": "multi_llm",
        "notes": "Industry-scoped GEO strategy — not universal; multi-LLM ok.",
    },
    "executive_brief": {
        "decision_value": "high",
        "min_reliable": "multi_llm",
        "notes": "Executive answers need synthesis + verification.",
    },
    "research_hypothesis": {
        "decision_value": "high",
        "min_reliable": "lab_experiment",
        "notes": "Controlled lab experiments are intentional spend.",
    },
    "council_strategy": {
        "decision_value": "critical",
        "min_reliable": "council",
        "notes": "Strategic bets justify adversarial Council.",
    },
    "custom": {
        "decision_value": "medium",
        "min_reliable": "single_llm",
        "notes": "Default custom intent — prefer single LLM over Council.",
    },
}

# Baseline resource profiles per method kind (expected units)
METHOD_PROFILES: dict[str, dict[str, Any]] = {
    "deterministic": {
        "calls": 0,
        "tokens": 0,
        "searches": 0,
        "runtime_seconds": 2.0,
        "cost_usd_micros": 50,
        "peacock_mode": "peacock_fast",
        "reliability_base": 0.92,
    },
    "web_search": {
        "calls": 2,
        "tokens": 1_500,
        "searches": 4,
        "runtime_seconds": 15.0,
        "cost_usd_micros": 2_500,
        "peacock_mode": "peacock_fast",
        "reliability_base": 0.78,
    },
    "single_llm": {
        "calls": 2,
        "tokens": 4_000,
        "searches": 0,
        "runtime_seconds": 25.0,
        "cost_usd_micros": 4_000,
        "peacock_mode": "peacock_standard",
        "reliability_base": 0.82,
    },
    "multi_llm": {
        "calls": 8,
        "tokens": 18_000,
        "searches": 3,
        "runtime_seconds": 180.0,
        "cost_usd_micros": 35_000,
        "peacock_mode": "peacock_deep",
        "reliability_base": 0.88,
    },
    "council": {
        "calls": 18,
        "tokens": 45_000,
        "searches": 6,
        "runtime_seconds": 420.0,
        "cost_usd_micros": 95_000,
        "peacock_mode": "peacock_council",
        "reliability_base": 0.91,
    },
    "lab_experiment": {
        "calls": 24,
        "tokens": 60_000,
        "searches": 10,
        "runtime_seconds": 900.0,
        "cost_usd_micros": 120_000,
        "peacock_mode": "peacock_lab",
        "reliability_base": 0.86,
    },
}

# Reliability boost when method meets/exceeds min_reliable for intent
RELIABILITY_FLOOR = 0.55


@dataclass
class BudgetEstimateSpec:
    client_brand: str
    question: str
    workflow_intent: str = "custom"
    decision_value: str | None = None
    analysed_at: datetime | None = None


@dataclass(slots=True)
class MethodCandidateResult:
    method_kind: str
    method_label: str
    peacock_mode: str | None
    reliable_enough: bool
    allowed_for_value: bool
    selected: bool
    expected_calls: int
    expected_tokens: int
    expected_searches: int
    expected_runtime_seconds: float
    expected_cost_usd_micros: int
    reliability_score: float
    cost_efficiency_score: float
    rejection_reason: str | None
    rank_order: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class BudgetEstimateResult:
    client_brand: str
    workflow_intent: str
    decision_value: str
    question: str
    selected_method_kind: str
    selected_method_label: str
    selected_peacock_mode: str | None
    selection_rationale: str
    rejected_expensive: bool
    expected_calls: int
    expected_tokens: int
    expected_searches: int
    expected_runtime_seconds: float
    expected_cost_usd_micros: int
    candidates: list[MethodCandidateResult]
    candidates_count: int
    cost_positioning: str
    policy_note: str
    methodology_note: str
    summary: str
    analysed_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "client_brand": self.client_brand,
            "workflow_intent": self.workflow_intent,
            "decision_value": self.decision_value,
            "question": self.question,
            "selected_method_kind": self.selected_method_kind,
            "selected_method_label": self.selected_method_label,
            "selected_peacock_mode": self.selected_peacock_mode,
            "selection_rationale": self.selection_rationale,
            "rejected_expensive": self.rejected_expensive,
            "expected_calls": self.expected_calls,
            "expected_tokens": self.expected_tokens,
            "expected_searches": self.expected_searches,
            "expected_runtime_seconds": self.expected_runtime_seconds,
            "expected_cost_usd_micros": self.expected_cost_usd_micros,
            "candidates": [c.to_dict() for c in self.candidates],
            "candidates_count": self.candidates_count,
            "cost_positioning": self.cost_positioning,
            "policy_note": self.policy_note,
            "methodology_note": self.methodology_note,
            "summary": self.summary,
            "analysed_at": self.analysed_at.isoformat(),
        }


def catalog() -> dict[str, Any]:
    return {
        "method_kinds": list(METHOD_KINDS),
        "method_kind_labels": dict(METHOD_KIND_LABELS),
        "decision_values": list(DECISION_VALUES),
        "decision_value_labels": dict(DECISION_VALUE_LABELS),
        "workflow_intents": list(WORKFLOW_INTENTS),
        "method_ladder": list(METHOD_LADDER),
        "value_method_ceiling": dict(VALUE_METHOD_CEILING),
        "method_profiles": {
            k: {
                "expected_calls": v["calls"],
                "expected_tokens": v["tokens"],
                "expected_searches": v["searches"],
                "expected_runtime_seconds": v["runtime_seconds"],
                "expected_cost_usd_micros": v["cost_usd_micros"],
                "peacock_mode": v["peacock_mode"],
            }
            for k, v in METHOD_PROFILES.items()
        },
        "cost_positioning": COST_POSITIONING,
        "policy_note": CHEAPEST_RELIABLE_POLICY,
        "methodology_note": METHODOLOGY_NOTE,
        "product_note": (
            "Intelligence Budget Engine — Peacock Cost Intelligence. "
            "Estimate before deep workflows; choose cheapest reliable method."
        ),
        "examples": [
            "Do NOT use five LLMs if deterministic data can answer.",
            "Do NOT run Council for a simple page-title recommendation.",
            "Reserve expensive reasoning for high-value decisions.",
        ],
    }


def _ladder_index(kind: str) -> int:
    try:
        return METHOD_LADDER.index(kind)
    except ValueError:
        return len(METHOD_LADDER)


def _allowed_for_value(method_kind: str, decision_value: str) -> bool:
    ceiling = VALUE_METHOD_CEILING.get(decision_value, "multi_llm")
    return _ladder_index(method_kind) <= _ladder_index(ceiling)


def _scale_for_intent(intent: str, profile: dict[str, Any]) -> dict[str, Any]:
    """Slight scaling: trivial intents shrink LLM profiles; lab grows experiments."""
    out = dict(profile)
    if intent in ("page_title_recommendation", "meta_description", "simple_seo_check"):
        if out["calls"] > 0:
            out["calls"] = max(1, out["calls"] // 2)
            out["tokens"] = max(500, out["tokens"] // 2)
            out["cost_usd_micros"] = max(100, out["cost_usd_micros"] // 2)
            out["runtime_seconds"] = max(1.0, out["runtime_seconds"] / 2)
    if intent == "research_hypothesis" and profile.get("peacock_mode") == "peacock_lab":
        out["searches"] = max(out["searches"], 12)
        out["calls"] = max(out["calls"], 30)
    return out


def _reliability(
    method_kind: str,
    *,
    min_reliable: str,
    decision_value: str,
) -> float:
    base = float(METHOD_PROFILES[method_kind]["reliability_base"])
    if _ladder_index(method_kind) < _ladder_index(min_reliable):
        # Too weak for the intent
        return round(max(RELIABILITY_FLOOR, base - 0.25), 3)
    if _ladder_index(method_kind) == _ladder_index(min_reliable):
        return round(min(0.98, base + 0.03), 3)
    # Overkill: slight reliability bump but policy may still reject
    bump = 0.02 if decision_value in ("high", "critical") else 0.0
    return round(min(0.99, base + bump), 3)


def _efficiency(cost: int, reliability: float) -> float:
    """Higher is better: reliability per dollar (micros)."""
    dollars = max(cost, 1) / 1_000_000.0
    return round(reliability / dollars, 4)


def estimate_budget(spec: BudgetEstimateSpec) -> BudgetEstimateResult:
    brand = (spec.client_brand or "").strip()
    if not brand:
        raise ValueError("client_brand is required")
    question = (spec.question or "").strip()
    if not question:
        raise ValueError("question is required")

    intent = (spec.workflow_intent or "custom").strip().lower()
    if intent not in WORKFLOW_INTENTS:
        raise ValueError(f"Unsupported workflow_intent: {intent}")

    defaults = INTENT_DEFAULTS[intent]
    decision_value = (spec.decision_value or defaults["decision_value"]).strip().lower()
    if decision_value not in DECISION_VALUES:
        raise ValueError(f"Unsupported decision_value: {decision_value}")

    min_reliable = str(defaults["min_reliable"])
    analysed_at = spec.analysed_at or datetime.now(tz=UTC)

    candidates: list[MethodCandidateResult] = []
    for i, kind in enumerate(METHOD_LADDER):
        raw = METHOD_PROFILES[kind]
        scaled = _scale_for_intent(intent, raw)
        reliability = _reliability(
            kind, min_reliable=min_reliable, decision_value=decision_value
        )
        allowed = _allowed_for_value(kind, decision_value)
        reliable_enough = reliability >= 0.70 and _ladder_index(kind) >= _ladder_index(
            min_reliable
        )
        cost = int(scaled["cost_usd_micros"])
        efficiency = _efficiency(cost, reliability)

        rejection: str | None = None
        if not allowed:
            rejection = (
                f"{METHOD_KIND_LABELS[kind]} exceeds ceiling for decision_value="
                f"{decision_value} (max {VALUE_METHOD_CEILING[decision_value]})."
            )
        elif not reliable_enough:
            rejection = (
                f"{METHOD_KIND_LABELS[kind]} is below minimum reliability for "
                f"intent={intent} (needs ≥ {METHOD_KIND_LABELS[min_reliable]})."
            )

        candidates.append(
            MethodCandidateResult(
                method_kind=kind,
                method_label=METHOD_KIND_LABELS[kind],
                peacock_mode=str(scaled["peacock_mode"]),
                reliable_enough=reliable_enough,
                allowed_for_value=allowed,
                selected=False,
                expected_calls=int(scaled["calls"]),
                expected_tokens=int(scaled["tokens"]),
                expected_searches=int(scaled["searches"]),
                expected_runtime_seconds=float(scaled["runtime_seconds"]),
                expected_cost_usd_micros=cost,
                reliability_score=reliability,
                cost_efficiency_score=efficiency,
                rejection_reason=rejection,
                rank_order=i,
            )
        )

    eligible = [
        c
        for c in candidates
        if c.allowed_for_value and c.reliable_enough and c.rejection_reason is None
    ]
    if not eligible:
        # Fallback: cheapest allowed method even if reliability soft-fails
        eligible = [c for c in candidates if c.allowed_for_value]
    if not eligible:
        eligible = [candidates[0]]

    # Cheapest among reliable; tie-break higher reliability then higher efficiency
    eligible.sort(
        key=lambda c: (
            c.expected_cost_usd_micros,
            -c.reliability_score,
            -c.cost_efficiency_score,
        )
    )
    selected = eligible[0]
    selected.selected = True

    expensive_kinds = {"multi_llm", "council", "lab_experiment"}
    rejected_expensive = any(
        c.method_kind in expensive_kinds and not c.selected and c.rejection_reason
        for c in candidates
    ) or (
        selected.method_kind not in expensive_kinds
        and intent in ("page_title_recommendation", "meta_description", "simple_seo_check", "share_of_answer_lookup")
    )

    rationale_parts = [
        f"Intent `{intent}` defaults to decision_value={decision_value}.",
        f"Minimum reliable method: {METHOD_KIND_LABELS[min_reliable]}.",
        f"Selected {selected.method_label} "
        f"(~{selected.expected_cost_usd_micros} µUSD, "
        f"{selected.expected_calls} calls, {selected.expected_tokens} tokens, "
        f"{selected.expected_searches} searches, "
        f"{selected.expected_runtime_seconds}s).",
    ]
    if selected.method_kind == "deterministic":
        rationale_parts.append(
            "Deterministic data can answer — skipping multi-LLM stacks."
        )
    if intent == "page_title_recommendation" and selected.method_kind != "council":
        rationale_parts.append(
            "Council mode rejected for a simple page-title recommendation."
        )
    if decision_value in ("trivial", "low") and selected.method_kind in expensive_kinds:
        pass  # shouldn't happen
    elif decision_value in ("trivial", "low"):
        rationale_parts.append(
            "Expensive reasoning reserved for high-value decisions."
        )
    rationale_parts.append(str(defaults["notes"]))

    summary = (
        f"Budget estimate for {brand}: choose {selected.method_label} "
        f"(${selected.expected_cost_usd_micros / 1_000_000:.4f}) for "
        f"{intent}/{decision_value}. {CHEAPEST_RELIABLE_POLICY}"
    )

    return BudgetEstimateResult(
        client_brand=brand,
        workflow_intent=intent,
        decision_value=decision_value,
        question=question,
        selected_method_kind=selected.method_kind,
        selected_method_label=selected.method_label,
        selected_peacock_mode=selected.peacock_mode,
        selection_rationale=" ".join(rationale_parts),
        rejected_expensive=bool(rejected_expensive),
        expected_calls=selected.expected_calls,
        expected_tokens=selected.expected_tokens,
        expected_searches=selected.expected_searches,
        expected_runtime_seconds=selected.expected_runtime_seconds,
        expected_cost_usd_micros=selected.expected_cost_usd_micros,
        candidates=candidates,
        candidates_count=len(candidates),
        cost_positioning=COST_POSITIONING,
        policy_note=CHEAPEST_RELIABLE_POLICY,
        methodology_note=METHODOLOGY_NOTE,
        summary=summary,
        analysed_at=analysed_at,
    )


def demo_estimate(brand: str = "Acme") -> BudgetEstimateResult:
    """Demo: page-title must not select Council."""
    return estimate_budget(
        BudgetEstimateSpec(
            client_brand=brand,
            workflow_intent="page_title_recommendation",
            question="Recommend a better title for /pricing",
            decision_value="trivial",
        )
    )
