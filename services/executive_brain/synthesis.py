"""Executive Brain synthesis — CEO/CMO briefing without SEO complexity."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

from db_models.executive_brain import (
    EXECUTIVE_QUESTION_LABELS,
    EXECUTIVE_QUESTIONS,
    METHODOLOGY_NOTE,
    SUMMARY_ROLES,
)


@dataclass
class ExecutiveSignal:
    """Compact fact for executive synthesis (from graph / demo)."""

    key: str
    value: str
    polarity: str = "neutral"  # win | lose | change | action | cost | return | risk
    weight: float = 0.75


@dataclass
class ExecutiveBrainSpec:
    client_brand: str
    competitor_name: str = "Competitor A"
    budget_label: str = "₹10 lakh"
    horizon_days: int = 90
    signals: list[ExecutiveSignal] = field(default_factory=list)
    generated_at: datetime | None = None


@dataclass(slots=True)
class ExecutiveAnswerResult:
    question_key: str
    question_label: str
    answer: str
    evidence_note: str
    confidence: float
    rank_order: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RoleSummaryResult:
    role: str
    title: str
    body: str
    call_to_action: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExecutiveBrainResult:
    client_brand: str
    generated_at: datetime
    horizon_days: int
    budget_label: str
    overall_confidence: float
    headline: str
    answers: list[ExecutiveAnswerResult]
    role_summaries: list[RoleSummaryResult]
    methodology_note: str
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "client_brand": self.client_brand,
            "generated_at": self.generated_at.isoformat(),
            "horizon_days": self.horizon_days,
            "budget_label": self.budget_label,
            "overall_confidence": self.overall_confidence,
            "headline": self.headline,
            "answers": [a.to_dict() for a in self.answers],
            "role_summaries": [r.to_dict() for r in self.role_summaries],
            "methodology_note": self.methodology_note,
            "summary": self.summary,
        }


def catalog() -> dict[str, Any]:
    return {
        "executive_questions": list(EXECUTIVE_QUESTIONS),
        "executive_question_labels": dict(EXECUTIVE_QUESTION_LABELS),
        "summary_roles": list(SUMMARY_ROLES),
        "methodology_note": METHODOLOGY_NOTE,
        "product_note": (
            "Peacock Executive Brain is a special executive view — winning, "
            "losing, why, change, action, cost, return, and do-nothing risk — "
            "with CEO/CMO-ready summaries. Not an SEO complexity display."
        ),
    }


def demo_signals(brand: str, competitor: str) -> list[ExecutiveSignal]:
    return [
        ExecutiveSignal(
            "win_search",
            f"{brand} still leads category search visibility on branded + mid-funnel hubs",
            "win",
            0.82,
        ),
        ExecutiveSignal(
            "win_content_opp",
            "Content opportunity score is high — clear room to gain on comparison pages",
            "win",
            0.8,
        ),
        ExecutiveSignal(
            "lose_citations",
            f"{competitor} citation share rose 18% → 31% on research queries",
            "lose",
            0.9,
        ),
        ExecutiveSignal(
            "lose_ai",
            "AI visibility and Share of Answer softened this week (esp. Claude/Perplexity)",
            "lose",
            0.85,
        ),
        ExecutiveSignal(
            "why_driver",
            f"{competitor} shipped 3 research pages that answer engines now prefer",
            "change",
            0.88,
        ),
        ExecutiveSignal(
            "why_gap",
            "Our comparison hubs lack quotable evidence density and entity coverage",
            "change",
            0.84,
        ),
        ExecutiveSignal(
            "changed_week",
            "This week: citation surge for competitor, AI visibility dip, anomaly alerts",
            "change",
            0.86,
        ),
        ExecutiveSignal(
            "action_benchmark",
            "Publish a proprietary benchmark study + refresh /compare and /pricing",
            "action",
            0.87,
        ),
        ExecutiveSignal(
            "cost_90d",
            "Focused 90-day programme fits roughly one planning envelope at capacity",
            "cost",
            0.78,
        ),
        ExecutiveSignal(
            "return_soa",
            "Directional SoA recovery in a mid-single to low-double-digit pp range over 90 days",
            "return",
            0.62,
        ),
        ExecutiveSignal(
            "return_pipe",
            "Commercial prompt clusters tie to material but uncertain pipeline exposure",
            "return",
            0.58,
        ),
        ExecutiveSignal(
            "risk_nothing",
            "If we do nothing, competitor citation lead likely widens and AI presence keeps eroding",
            "risk",
            0.83,
        ),
    ]


def _by_polarity(signals: list[ExecutiveSignal], polarity: str) -> list[ExecutiveSignal]:
    return [s for s in signals if s.polarity == polarity]


def _join(signals: list[ExecutiveSignal], fallback: str) -> str:
    if not signals:
        return fallback
    return "; ".join(s.value for s in signals)


def _conf(signals: list[ExecutiveSignal], base: float) -> float:
    if not signals:
        return round(max(0.2, base * 0.5), 3)
    mean_w = sum(s.weight for s in signals) / len(signals)
    return round(max(0.2, min(0.95, base * 0.5 + mean_w * 0.5)), 3)


def synthesise_executive_brain(spec: ExecutiveBrainSpec) -> ExecutiveBrainResult:
    brand = (spec.client_brand or "").strip()
    if not brand:
        raise ValueError("client_brand is required")
    competitor = (spec.competitor_name or "Competitor A").strip()
    budget = (spec.budget_label or "₹10 lakh").strip()
    horizon = max(30, int(spec.horizon_days or 90))

    signals = list(spec.signals) or demo_signals(brand, competitor)
    wins = _by_polarity(signals, "win")
    losses = _by_polarity(signals, "lose")
    changes = _by_polarity(signals, "change")
    actions = _by_polarity(signals, "action")
    costs = _by_polarity(signals, "cost")
    returns = _by_polarity(signals, "return")
    risks = _by_polarity(signals, "risk")

    answers_spec = [
        (
            "where_winning",
            _join(
                wins,
                f"{brand} retains strength on branded search and high content-opportunity surfaces.",
            ),
            _join(wins, "Command Centre win signals"),
            _conf(wins, 0.8),
        ),
        (
            "where_losing",
            _join(
                losses,
                f"{brand} is losing generative citation share and AI answer presence.",
            ),
            _join(losses, "Command Centre loss signals"),
            _conf(losses, 0.84),
        ),
        (
            "why",
            _join(
                changes[:2] if changes else changes,
                f"Answer engines are rewarding {competitor}'s recent evidence-dense research pages "
                "while our comparison hubs under-deliver quotable proof.",
            ),
            _join(changes, "Driver signals"),
            _conf(changes, 0.82),
        ),
        (
            "what_changed",
            _join(
                [s for s in changes if "week" in s.key or "changed" in s.key] or changes,
                "This week shifted against us on citations and AI visibility.",
            ),
            "Temporal + anomaly movement",
            _conf(changes, 0.8),
        ),
        (
            "worth_doing",
            _join(
                actions,
                "Ship a proprietary benchmark and refresh the highest-leverage commercial hubs.",
            ),
            _join(actions, "Priority actions"),
            _conf(actions, 0.83),
        ),
        (
            "what_cost",
            (
                f"Plan around {budget} over the next {horizon} days, sized to capacity — "
                "citability content, entity/schema, citation outreach, and measurement. "
                + _join(costs, "")
            ).strip(),
            f"Budget envelope {budget} / {horizon}d",
            _conf(costs, 0.74),
        ),
        (
            "what_return",
            _join(
                returns,
                "Directional generative-visibility recovery and protected commercial demand — "
                "expressed as ranges, not guarantees.",
            ),
            _join(returns, "Return ranges"),
            _conf(returns, 0.6),
        ),
        (
            "if_do_nothing",
            _join(
                risks,
                f"Doing nothing likely lets {competitor} compound citation and AI-answer advantage.",
            ),
            _join(risks, "Do-nothing risk"),
            _conf(risks, 0.8),
        ),
    ]

    answers = [
        ExecutiveAnswerResult(
            question_key=key,
            question_label=EXECUTIVE_QUESTION_LABELS[key],
            answer=answer,
            evidence_note=evidence,
            confidence=conf,
            rank_order=i,
        )
        for i, (key, answer, evidence, conf) in enumerate(answers_spec)
    ]

    overall = round(sum(a.confidence for a in answers) / len(answers), 3)
    generated_at = spec.generated_at or datetime.now(tz=UTC)

    ceo = RoleSummaryResult(
        role="ceo",
        title="CEO brief",
        body=(
            f"{brand} is not losing the whole board — search and content opportunity still hold — "
            f"but generative visibility is the strategic risk. {competitor} jumped citation share "
            f"18% → 31% on research queries after three new pages. A focused {horizon}-day push "
            f"(~{budget}) to publish proprietary proof and harden commercial hubs is the "
            f"executive decision. Doing nothing likely widens the gap. Treat returns as ranges."
        ),
        call_to_action=(
            f"Approve the {horizon}-day generative-visibility programme and name an owner "
            "for citation + AI Share-of-Answer outcomes."
        ),
    )
    cmo = RoleSummaryResult(
        role="cmo",
        title="CMO brief",
        body=(
            f"Marketing priority: stop bleeding AI answer presence. Win zones remain branded "
            f"search and high-opportunity pages; loss zones are citations and multi-engine SoA. "
            f"Why: evidence density. Change this week: competitor research pages + our soft AI "
            f"scores. Worth doing: benchmark study + /compare + /pricing refresh. Cost envelope "
            f"{budget}; expected return is directional SoA recovery, not a point forecast. "
            f"If we wait, the narrative compounds against {brand}."
        ),
        call_to_action=(
            "Greenlight the benchmark + hub refresh sprint; hold low-ROI volume until "
            "citability work lands."
        ),
    )

    headline = f"{brand} · Executive Brain · {horizon}-day generative visibility brief"
    summary = (
        f"Executive Brain for {brand}: {len(answers)} executive answers and "
        f"CEO/CMO summaries (confidence {overall:.2f})."
    )

    return ExecutiveBrainResult(
        client_brand=brand,
        generated_at=generated_at,
        horizon_days=horizon,
        budget_label=budget,
        overall_confidence=overall,
        headline=headline,
        answers=answers,
        role_summaries=[ceo, cmo],
        methodology_note=METHODOLOGY_NOTE,
        summary=summary,
    )
