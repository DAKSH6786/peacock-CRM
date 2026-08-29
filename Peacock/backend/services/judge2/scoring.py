"""Peacock Judge 2.0 — deterministic multi-signal scoring outside the LLM."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from db_models.judge2 import (
    DEFAULT_JUDGE_WEIGHTS,
    JUDGE_SIGNAL_FAMILIES,
    METHODOLOGY_NOTE,
    SCORING_OUTSIDE_LLM,
)


def _clamp100(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


def _normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    total = sum(max(0.0, float(weights.get(k, 0.0))) for k in JUDGE_SIGNAL_FAMILIES) or 1.0
    return {k: max(0.0, float(weights.get(k, 0.0))) / total for k in JUDGE_SIGNAL_FAMILIES}


# Signals where higher raw value is worse
_INVERTED = frozenset({"cost", "risk"})


@dataclass
class EvidenceInput:
    evidence_type: str
    statement: str
    source_ref: str | None = None
    reliability: float = 50.0
    signal_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ReversalConditionInput:
    """Explicit trigger that would change the recommendation."""

    condition_key: str
    metric_code: str
    operator: str  # gt|lt|gte|lte|change_pct_down|change_pct_up
    threshold: float
    statement: str
    unit: str | None = None
    reevaluate_action: str = "re-evaluate"
    priority: float = 50.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class JudgeBrief:
    decision_question: str
    client_brand: str
    # Signal inputs 0–100 (cost/risk: higher = worse)
    signals: dict[str, float] = field(default_factory=dict)
    evidence: list[EvidenceInput] = field(default_factory=list)
    # Optional explicit reversal conditions; defaults generated if empty
    reversal_conditions: list[ReversalConditionInput] = field(default_factory=list)
    # Optional narrative hints (not used for score)
    business_goal_summary: str | None = None
    alternative_hint: str | None = None
    council2_session_id: str | None = None
    custom_weights: dict[str, float] | None = None


@dataclass(slots=True)
class SignalScoreResult:
    signal_code: str
    raw_value: float
    weight: float
    inverted: bool
    contribution: float
    explanation: str
    computed_outside_llm: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class EvidenceResult:
    evidence_type: str
    statement: str
    source_ref: str | None
    reliability: float
    signal_code: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ReversalConditionResult:
    condition_key: str
    metric_code: str
    operator: str
    threshold: float
    unit: str | None
    statement: str
    reevaluate_action: str
    priority: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class JudgeResult:
    recommended_action: str
    why: str
    evidence: list[EvidenceResult]
    expected_upside: str
    expected_upside_score: float
    risk_summary: str
    risk_score: float
    confidence: float
    alternative: str
    what_would_change_decision: str
    reversal_conditions: list[ReversalConditionResult]
    signal_scores: list[SignalScoreResult]
    composite_score: float
    action_code: str
    scoring_outside_llm: bool
    scoring_note: str
    methodology_note: str
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommended_action": self.recommended_action,
            "why": self.why,
            "evidence": [e.to_dict() for e in self.evidence],
            "expected_upside": self.expected_upside,
            "expected_upside_score": self.expected_upside_score,
            "risk_summary": self.risk_summary,
            "risk_score": self.risk_score,
            "confidence": self.confidence,
            "alternative": self.alternative,
            "what_would_change_decision": self.what_would_change_decision,
            "reversal_conditions": [r.to_dict() for r in self.reversal_conditions],
            "signal_scores": [s.to_dict() for s in self.signal_scores],
            "composite_score": self.composite_score,
            "action_code": self.action_code,
            "scoring_outside_llm": self.scoring_outside_llm,
            "scoring_note": self.scoring_note,
            "methodology_note": self.methodology_note,
            "summary": self.summary,
        }


def _default_reversals(brief: JudgeBrief) -> list[ReversalConditionResult]:
    """Canonical «What Would Change Our Decision» triggers."""
    brand = brief.client_brand
    return [
        ReversalConditionResult(
            condition_key="keyword_demand_decline",
            metric_code="keyword_demand",
            operator="change_pct_down",
            threshold=40.0,
            unit="percent",
            statement=(
                "If keyword demand declines >40%, re-evaluate this recommendation."
            ),
            reevaluate_action="re-evaluate",
            priority=90.0,
        ),
        ReversalConditionResult(
            condition_key="competitor_citation_dominance_loss",
            metric_code="competitor_citation_share",
            operator="change_pct_down",
            threshold=25.0,
            unit="percent",
            statement=(
                "If Competitor A loses citation dominance, re-evaluate this recommendation."
            ),
            reevaluate_action="re-evaluate",
            priority=85.0,
        ),
        ReversalConditionResult(
            condition_key="cost_overrun",
            metric_code="projected_cost",
            operator="gt",
            threshold=max(brief.signals.get("cost", 50.0) * 1.5, 75.0),
            unit="score",
            statement=(
                f"If projected cost for {brand} exceeds the agreed envelope, re-evaluate."
            ),
            reevaluate_action="re-evaluate",
            priority=80.0,
        ),
        ReversalConditionResult(
            condition_key="risk_spike",
            metric_code="risk",
            operator="gte",
            threshold=80.0,
            unit="score",
            statement="If risk score rises to ≥80/100, re-evaluate or defer.",
            reevaluate_action="re-evaluate",
            priority=88.0,
        ),
        ReversalConditionResult(
            condition_key="confidence_collapse",
            metric_code="confidence",
            operator="lt",
            threshold=40.0,
            unit="score",
            statement="If confidence falls below 40/100 on refreshed evidence, re-evaluate.",
            reevaluate_action="re-evaluate",
            priority=75.0,
        ),
    ]


def _action_from_score(
    composite: float,
    risk: float,
    cost: float,
) -> tuple[str, str]:
    """Map deterministic composite to action code + recommended action text."""
    if composite >= 70 and risk < 70 and cost < 85:
        return (
            "proceed",
            "Proceed with the proposed action under stated guardrails and measurement gates.",
        )
    if composite >= 55:
        return (
            "conditional",
            "Proceed conditionally: pilot a bounded slice, measure, then expand if gates pass.",
        )
    if composite >= 40:
        return (
            "defer",
            "Defer the primary action; gather stronger evidence and reduce risk/cost first.",
        )
    return (
        "reject",
        "Do not proceed with the primary action given current downside and weak signal support.",
    )


def _alternative_for(action_code: str, brief: JudgeBrief) -> str:
    if brief.alternative_hint:
        return brief.alternative_hint
    alts = {
        "proceed": (
            "Alternative: stage a smaller controlled experiment (GEO Lab / content twin) "
            "before full rollout."
        ),
        "conditional": (
            "Alternative: full proceed only after risk mitigations and cost controls land."
        ),
        "defer": (
            "Alternative: pursue a lower-cost content refresh on decaying pages while "
            "evidence matures."
        ),
        "reject": (
            "Alternative: reallocate budget to higher-confidence opportunities already "
            "ranked by Peacock Opportunities."
        ),
    }
    return alts.get(action_code, "Alternative: revisit with updated evidence pack.")


def judge_decision(brief: JudgeBrief) -> JudgeResult:
    """Deterministic Judge 2.0 scoring — outside the LLM."""
    if not brief.decision_question.strip():
        raise ValueError("decision_question is required")
    if not brief.client_brand.strip():
        raise ValueError("client_brand is required")

    weights = _normalize_weights(brief.custom_weights or DEFAULT_JUDGE_WEIGHTS)
    # Fill missing signals with neutral 50
    raw: dict[str, float] = {}
    for code in JUDGE_SIGNAL_FAMILIES:
        val = brief.signals.get(code)
        if val is None:
            raw[code] = 50.0
        else:
            raw[code] = _clamp100(val)

    signal_scores: list[SignalScoreResult] = []
    composite = 0.0
    for code in JUDGE_SIGNAL_FAMILIES:
        inverted = code in _INVERTED
        effective = 100.0 - raw[code] if inverted else raw[code]
        contrib = weights[code] * effective
        composite += contrib
        signal_scores.append(
            SignalScoreResult(
                signal_code=code,
                raw_value=raw[code],
                weight=weights[code],
                inverted=inverted,
                contribution=contrib,
                explanation=(
                    f"{code}={raw[code]:.1f}"
                    + (" (inverted)" if inverted else "")
                    + f" × {weights[code]:.3f} → {contrib:.2f} [deterministic, outside LLM]"
                ),
                computed_outside_llm=True,
            )
        )
    composite = _clamp100(composite)

    action_code, recommended_action = _action_from_score(
        composite, raw["risk"], raw["cost"]
    )

    # Upside estimate from supportive signals
    upside_score = _clamp100(
        0.35 * raw["business_goals"]
        + 0.25 * raw["historical_outcomes"]
        + 0.20 * raw["statistical_evidence"]
        + 0.20 * raw["multi_model_findings"]
    )
    expected_upside = (
        f"Expected upside {upside_score:.0f}/100 for {brief.client_brand} on "
        f"«{brief.decision_question}» — driven by business goals, historical outcomes, "
        f"and statistical/multi-model support."
    )

    risk_score = raw["risk"]
    risk_summary = (
        f"Risk {risk_score:.0f}/100 (cost {raw['cost']:.0f}/100). "
        + (
            "Downside is material; keep guardrails tight."
            if risk_score >= 60
            else "Downside is manageable under current assumptions."
        )
    )

    confidence = raw["confidence"]
    # Slightly discount confidence if source reliability is weak
    confidence = _clamp100(0.7 * confidence + 0.3 * raw["source_reliability"])

    why = (
        f"Deterministic composite {composite:.1f}/100 from nine signal families "
        f"(scoring outside LLM). Action={action_code}. "
        f"Top contributors: "
        + ", ".join(
            f"{s.signal_code}={s.contribution:.1f}"
            for s in sorted(signal_scores, key=lambda x: x.contribution, reverse=True)[:3]
        )
        + "."
        + (f" Goal context: {brief.business_goal_summary}" if brief.business_goal_summary else "")
    )

    evidence = [
        EvidenceResult(
            evidence_type=e.evidence_type,
            statement=e.statement,
            source_ref=e.source_ref,
            reliability=_clamp100(e.reliability),
            signal_code=e.signal_code,
        )
        for e in brief.evidence
    ]
    # Always include a deterministic score evidence row
    evidence.append(
        EvidenceResult(
            evidence_type="deterministic_score",
            statement=(
                f"Composite judge score {composite:.1f}/100 computed outside LLM "
                f"from weighted signals { {s.signal_code: s.raw_value for s in signal_scores} }."
            ),
            source_ref="judge2:deterministic_blend",
            reliability=90.0,
            signal_code="deterministic_data",
        )
    )

    # Reversal conditions — critical product surface
    if brief.reversal_conditions:
        reversals = [
            ReversalConditionResult(
                condition_key=r.condition_key,
                metric_code=r.metric_code,
                operator=r.operator,
                threshold=r.threshold,
                unit=r.unit,
                statement=r.statement,
                reevaluate_action=r.reevaluate_action,
                priority=r.priority,
            )
            for r in brief.reversal_conditions
        ]
    else:
        reversals = _default_reversals(brief)

    # Ensure examples from the product brief are present when using defaults path
    # (already included). Format the narrative field.
    what_would_change = "WHAT WOULD CHANGE THIS RECOMMENDATION?\n\n" + "\n\nor\n\n".join(
        r.statement for r in sorted(reversals, key=lambda x: -x.priority)[:4]
    )

    alternative = _alternative_for(action_code, brief)

    summary = (
        f"Judge 2.0 → {action_code} (composite {composite:.0f}/100, confidence "
        f"{confidence:.0f}/100, risk {risk_score:.0f}/100). "
        f"{len(reversals)} reversal condition(s) defined. Scoring outside LLM."
    )

    return JudgeResult(
        recommended_action=recommended_action,
        why=why,
        evidence=evidence,
        expected_upside=expected_upside,
        expected_upside_score=upside_score,
        risk_summary=risk_summary,
        risk_score=risk_score,
        confidence=confidence,
        alternative=alternative,
        what_would_change_decision=what_would_change,
        reversal_conditions=reversals,
        signal_scores=signal_scores,
        composite_score=composite,
        action_code=action_code,
        scoring_outside_llm=True,
        scoring_note=SCORING_OUTSIDE_LLM,
        methodology_note=METHODOLOGY_NOTE,
        summary=summary,
    )
