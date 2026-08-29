"""Temporal Intelligence engine — timeline, queries, change-point detection."""

from __future__ import annotations

import math
import statistics
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from db_models.temporal_intelligence import (
    EVENT_KINDS,
    EVENT_LABELS,
    METHODOLOGY_NOTE,
    NOISE_GUARDRAIL,
    QUERY_INTENTS,
)


# Statistical thresholds — tune to suppress noise
MIN_BASELINE_POINTS = 5
MIN_POST_POINTS = 2
Z_SCORE_ALERT = 2.5
MIN_EFFECT_SIZE_RATIO = 0.15  # relative to |baseline mean| or absolute floor
MIN_ABSOLUTE_EFFECT = 1.0
CUSUM_THRESHOLD_MULT = 4.0


def _clamp100(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


@dataclass
class TimelineEventInput:
    event_kind: str
    occurred_at: datetime
    title: str
    detail: str
    magnitude: float = 0.0
    direction: str = "neutral"  # up|down|neutral
    metric_key: str | None = None
    metric_value: float | None = None
    source_ref: str | None = None

    def validate(self) -> None:
        if self.event_kind not in EVENT_KINDS:
            raise ValueError(f"Unsupported event_kind: {self.event_kind}")
        if self.direction not in ("up", "down", "neutral"):
            raise ValueError("direction must be up|down|neutral")
        if not self.title.strip():
            raise ValueError("title is required")


@dataclass
class MetricSeriesPoint:
    occurred_at: datetime
    value: float


@dataclass
class MetricSeries:
    metric_key: str
    points: list[MetricSeriesPoint] = field(default_factory=list)


@dataclass
class TimelineSpec:
    client_brand: str
    window_start: datetime
    window_end: datetime
    events: list[TimelineEventInput] = field(default_factory=list)
    series: list[MetricSeries] = field(default_factory=list)
    questions: list[str] = field(default_factory=list)


@dataclass(slots=True)
class EventResult:
    event_kind: str
    event_label: str
    occurred_at: datetime
    title: str
    detail: str
    magnitude: float
    direction: str
    metric_key: str | None
    metric_value: float | None
    source_ref: str | None
    event_id: str | None = None  # filled after persist

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["occurred_at"] = self.occurred_at.isoformat()
        return d


@dataclass(slots=True)
class ChangePointResult:
    metric_key: str
    detected_at: datetime
    score: float
    effect_size: float
    baseline_mean: float
    baseline_std: float
    post_mean: float
    is_alert: bool
    suppressed_as_noise: bool
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["detected_at"] = self.detected_at.isoformat()
        return d


@dataclass(slots=True)
class QueryAnswerResult:
    intent: str
    question: str
    answer: str
    supporting_event_indexes: list[int]
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TimelineAnalysisResult:
    window_start: datetime
    window_end: datetime
    events: list[EventResult]
    change_points: list[ChangePointResult]
    query_answers: list[QueryAnswerResult]
    events_count: int
    change_points_count: int
    alerts_suppressed: int
    noise_guardrail: str
    methodology_note: str
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
            "events": [e.to_dict() for e in self.events],
            "change_points": [c.to_dict() for c in self.change_points],
            "query_answers": [q.to_dict() for q in self.query_answers],
            "events_count": self.events_count,
            "change_points_count": self.change_points_count,
            "alerts_suppressed": self.alerts_suppressed,
            "noise_guardrail": self.noise_guardrail,
            "methodology_note": self.methodology_note,
            "summary": self.summary,
        }


def detect_intent(question: str) -> str:
    q = question.lower().strip()
    if "what changed" in q or q.startswith("what changed"):
        return "what_changed"
    if "visibility drop" in q or "why did visibility" in q or "visibility fell" in q:
        return "why_visibility_drop"
    if "before citation" in q or "citations increased" in q or "before citations" in q:
        return "before_citations_increased"
    if "preceded" in q and ("ranking" in q or "rank" in q):
        return "action_preceded_ranking_increase"
    if "peacock action" in q and ("rank" in q or "ranking" in q):
        return "action_preceded_ranking_increase"
    return "custom"


def _std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    return statistics.pstdev(values)


def detect_change_points(series: MetricSeries) -> list[ChangePointResult]:
    """CUSUM / z-score hybrid. Suppresses noise below effect-size and z thresholds."""
    pts = sorted(series.points, key=lambda p: p.occurred_at)
    if len(pts) < MIN_BASELINE_POINTS + MIN_POST_POINTS:
        return []

    results: list[ChangePointResult] = []
    suppressed = 0
    values = [p.value for p in pts]

    # Sliding: for each candidate split after enough baseline
    for i in range(MIN_BASELINE_POINTS, len(pts) - MIN_POST_POINTS + 1):
        baseline = values[:i]
        # Look at a short post window
        post = values[i : i + MIN_POST_POINTS]
        b_mean = statistics.fmean(baseline)
        b_std = _std(baseline) or 1e-6
        p_mean = statistics.fmean(post)
        effect = p_mean - b_mean
        z = abs(effect) / b_std
        min_effect = max(MIN_ABSOLUTE_EFFECT, abs(b_mean) * MIN_EFFECT_SIZE_RATIO)

        # CUSUM-like cumulative deviation ending at i
        cusum = 0.0
        for v in baseline[-MIN_BASELINE_POINTS:]:
            cusum += v - b_mean
        cusum_score = abs(cusum) / b_std

        score = max(z, cusum_score / CUSUM_THRESHOLD_MULT * Z_SCORE_ALERT)
        detected_at = pts[i].occurred_at

        if abs(effect) < min_effect or z < Z_SCORE_ALERT:
            suppressed += 1
            results.append(
                ChangePointResult(
                    metric_key=series.metric_key,
                    detected_at=detected_at,
                    score=round(score, 3),
                    effect_size=round(effect, 3),
                    baseline_mean=round(b_mean, 3),
                    baseline_std=round(b_std, 3),
                    post_mean=round(p_mean, 3),
                    is_alert=False,
                    suppressed_as_noise=True,
                    rationale=(
                        f"Noise suppressed for {series.metric_key} at {detected_at.isoformat()}: "
                        f"|effect|={abs(effect):.2f} < min {min_effect:.2f} or z={z:.2f} < {Z_SCORE_ALERT}."
                    ),
                )
            )
            continue

        results.append(
            ChangePointResult(
                metric_key=series.metric_key,
                detected_at=detected_at,
                score=round(score, 3),
                effect_size=round(effect, 3),
                baseline_mean=round(b_mean, 3),
                baseline_std=round(b_std, 3),
                post_mean=round(p_mean, 3),
                is_alert=True,
                suppressed_as_noise=False,
                rationale=(
                    f"Unusual shift in {series.metric_key}: baseline {b_mean:.2f}±{b_std:.2f} → "
                    f"post {p_mean:.2f} (effect {effect:+.2f}, z={z:.2f})."
                ),
            )
        )

    # Keep strongest alert per day + all suppressions counted; collapse alerts
    alerts = [r for r in results if r.is_alert]
    noise = [r for r in results if r.suppressed_as_noise]
    # Deduplicate alerts: keep max score per (metric, date)
    best: dict[str, ChangePointResult] = {}
    for a in alerts:
        key = a.detected_at.date().isoformat()
        if key not in best or a.score > best[key].score:
            best[key] = a
    # Return alerts + a sample of noise (for transparency count we keep all noise
    # but API may filter). Store all for suppressed count.
    return list(best.values()) + noise


def _answer_what_changed(events: list[EventResult]) -> QueryAnswerResult:
    if not events:
        return QueryAnswerResult(
            intent="what_changed",
            question="What changed?",
            answer="No timeline events in the selected window.",
            supporting_event_indexes=[],
            confidence=40.0,
        )
    # Rank by magnitude
    ranked = sorted(
        enumerate(events),
        key=lambda iv: abs(iv[1].magnitude),
        reverse=True,
    )[:5]
    lines = [
        f"- {e.occurred_at.date()}: [{e.event_label}] {e.title} ({e.direction}, mag={e.magnitude:.1f})"
        for _, e in ranked
    ]
    return QueryAnswerResult(
        intent="what_changed",
        question="What changed?",
        answer="Top changes in the Visibility Timeline:\n" + "\n".join(lines),
        supporting_event_indexes=[i for i, _ in ranked],
        confidence=_clamp100(55 + 5 * len(ranked)),
    )


def _answer_visibility_drop(events: list[EventResult]) -> QueryAnswerResult:
    drops = [
        (i, e)
        for i, e in enumerate(events)
        if e.direction == "down"
        and (
            e.event_kind in ("search_change", "ai_answer_change", "citation_change")
            or (e.metric_key and "visibility" in (e.metric_key or ""))
        )
    ]
    preceding = []
    if drops:
        first_drop_at = min(e.occurred_at for _, e in drops)
        preceding = [
            (i, e)
            for i, e in enumerate(events)
            if e.occurred_at <= first_drop_at
            and e.event_kind
            in ("competitor_change", "algorithm_event", "content_update", "peacock_action")
        ]
    if not drops:
        return QueryAnswerResult(
            intent="why_visibility_drop",
            question="Why did visibility drop?",
            answer=(
                "No clear visibility-down events in this window. "
                "Check Search Console / AI citation series for subtler declines."
            ),
            supporting_event_indexes=[],
            confidence=35.0,
        )
    drop_lines = [f"- {e.title} ({e.occurred_at.date()})" for _, e in drops[:3]]
    prec_lines = [
        f"- {e.event_label}: {e.title} ({e.occurred_at.date()})" for _, e in preceding[:4]
    ] or ["- No strong preceding competitor/algorithm/content/action events recorded."]
    return QueryAnswerResult(
        intent="why_visibility_drop",
        question="Why did visibility drop?",
        answer=(
            "Visibility-down signals:\n"
            + "\n".join(drop_lines)
            + "\nPossible preceding factors:\n"
            + "\n".join(prec_lines)
            + "\n(Correlation on the timeline — not proven causality.)"
        ),
        supporting_event_indexes=[i for i, _ in drops[:3]] + [i for i, _ in preceding[:4]],
        confidence=60.0 if preceding else 45.0,
    )


def _answer_before_citations(events: list[EventResult]) -> QueryAnswerResult:
    cites_up = [
        (i, e)
        for i, e in enumerate(events)
        if e.event_kind == "citation_change" and e.direction == "up"
    ]
    if not cites_up:
        return QueryAnswerResult(
            intent="before_citations_increased",
            question="What happened before citations increased?",
            answer="No citation-increase events found in this window.",
            supporting_event_indexes=[],
            confidence=35.0,
        )
    first = min(cites_up, key=lambda iv: iv[1].occurred_at)
    before = [
        (i, e)
        for i, e in enumerate(events)
        if e.occurred_at < first[1].occurred_at
        and e.event_kind
        in ("content_update", "peacock_action", "entity_change", "algorithm_event")
    ]
    before = sorted(before, key=lambda iv: iv[1].occurred_at, reverse=True)[:5]
    lines = [
        f"- {e.occurred_at.date()}: [{e.event_label}] {e.title}" for _, e in before
    ] or ["- No content/action/entity/algorithm events recorded before the lift."]
    return QueryAnswerResult(
        intent="before_citations_increased",
        question="What happened before citations increased?",
        answer=(
            f"Citation increase at {first[1].occurred_at.date()} ({first[1].title}). "
            f"Preceding timeline events:\n" + "\n".join(lines)
        ),
        supporting_event_indexes=[first[0]] + [i for i, _ in before],
        confidence=58.0 if before else 42.0,
    )


def _answer_action_preceded_rank(events: list[EventResult]) -> QueryAnswerResult:
    rank_up = [
        (i, e)
        for i, e in enumerate(events)
        if e.direction == "up"
        and (
            e.event_kind == "search_change"
            or (e.metric_key and "rank" in (e.metric_key or "").lower())
            or "rank" in e.title.lower()
        )
    ]
    actions = [(i, e) for i, e in enumerate(events) if e.event_kind == "peacock_action"]
    pairs = []
    for ri, re in rank_up:
        prior_actions = [
            (ai, ae) for ai, ae in actions if ae.occurred_at <= re.occurred_at
        ]
        if prior_actions:
            last = max(prior_actions, key=lambda iv: iv[1].occurred_at)
            pairs.append((last, (ri, re)))
    if not pairs:
        return QueryAnswerResult(
            intent="action_preceded_ranking_increase",
            question="Which action preceded our ranking increase?",
            answer=(
                "No Peacock action clearly preceding a ranking-up event in this window."
            ),
            supporting_event_indexes=[],
            confidence=35.0,
        )
    lines = [
        f"- Action '{ae.title}' ({ae.occurred_at.date()}) → ranking signal "
        f"'{re.title}' ({re.occurred_at.date()})"
        for (ai, ae), (ri, re) in pairs[:5]
    ]
    return QueryAnswerResult(
        intent="action_preceded_ranking_increase",
        question="Which action preceded our ranking increase?",
        answer="Actions preceding ranking increases:\n" + "\n".join(lines)
        + "\n(Temporal precedence only — not causal proof.)",
        supporting_event_indexes=[ai for (ai, _), (ri, _) in pairs[:5] for ai in (ai,)]
        + [ri for _, (ri, _) in pairs[:5]],
        confidence=62.0,
    )


def answer_queries(
    questions: list[str], events: list[EventResult]
) -> list[QueryAnswerResult]:
    defaults = [
        "What changed?",
        "Why did visibility drop?",
        "What happened before citations increased?",
        "Which action preceded our ranking increase?",
    ]
    qs = questions or defaults
    answers: list[QueryAnswerResult] = []
    for q in qs:
        intent = detect_intent(q)
        if intent == "what_changed":
            a = _answer_what_changed(events)
            a = QueryAnswerResult(a.intent, q, a.answer, a.supporting_event_indexes, a.confidence)
        elif intent == "why_visibility_drop":
            a = _answer_visibility_drop(events)
            a = QueryAnswerResult(a.intent, q, a.answer, a.supporting_event_indexes, a.confidence)
        elif intent == "before_citations_increased":
            a = _answer_before_citations(events)
            a = QueryAnswerResult(a.intent, q, a.answer, a.supporting_event_indexes, a.confidence)
        elif intent == "action_preceded_ranking_increase":
            a = _answer_action_preceded_rank(events)
            a = QueryAnswerResult(a.intent, q, a.answer, a.supporting_event_indexes, a.confidence)
        else:
            # Custom: fall back to what changed with question echoed
            base = _answer_what_changed(events)
            a = QueryAnswerResult(
                "custom",
                q,
                f"Interpreted as a general change query.\n{base.answer}",
                base.supporting_event_indexes,
                max(30.0, base.confidence - 10),
            )
        answers.append(a)
    return answers


def demo_events(window_end: datetime | None = None) -> list[TimelineEventInput]:
    """Deterministic demo timeline for tests / empty inputs."""
    end = window_end or datetime.now(UTC)
    base = end - timedelta(days=30)
    return [
        TimelineEventInput(
            "content_update",
            base + timedelta(days=3),
            "Refreshed canonical product page",
            "Content update shipped on /pricing",
            magnitude=2.0,
            direction="neutral",
            source_ref="cms:pricing",
        ),
        TimelineEventInput(
            "peacock_action",
            base + timedelta(days=4),
            "Executed schema suggestion action",
            "Peacock Action Engine executed generate_schema_suggestion",
            magnitude=2.5,
            direction="up",
            source_ref="action:schema",
        ),
        TimelineEventInput(
            "search_change",
            base + timedelta(days=10),
            "Organic ranking increase for core query",
            "Avg rank improved for brand+category queries",
            magnitude=5.0,
            direction="up",
            metric_key="organic_rank_score",
            metric_value=72.0,
        ),
        TimelineEventInput(
            "citation_change",
            base + timedelta(days=14),
            "AI citations increased",
            "Citation share up on comparison prompts",
            magnitude=4.5,
            direction="up",
            metric_key="ai_citation_share",
            metric_value=18.0,
        ),
        TimelineEventInput(
            "competitor_change",
            base + timedelta(days=18),
            "Competitor launched comparison hub",
            "Competitor X published aggressive comparison content",
            magnitude=3.0,
            direction="down",
        ),
        TimelineEventInput(
            "search_change",
            base + timedelta(days=20),
            "Visibility dip on category terms",
            "Organic visibility down after competitor hub",
            magnitude=4.0,
            direction="down",
            metric_key="visibility_index",
            metric_value=48.0,
        ),
        TimelineEventInput(
            "algorithm_event",
            base + timedelta(days=21),
            "Engine retrieval refresh noted",
            "Industry chatter of generative retrieval refresh",
            magnitude=2.0,
            direction="neutral",
        ),
        TimelineEventInput(
            "entity_change",
            base + timedelta(days=22),
            "Brand entity association shifted",
            "Entity graph shows weaker product-category link",
            magnitude=2.5,
            direction="down",
            metric_key="entity_association",
            metric_value=40.0,
        ),
        TimelineEventInput(
            "sentiment_change",
            base + timedelta(days=24),
            "Answer sentiment softened",
            "Model answers less positive on brand mentions",
            magnitude=1.5,
            direction="down",
        ),
        TimelineEventInput(
            "ai_answer_change",
            base + timedelta(days=25),
            "AI answer presence reduced",
            "Fewer featured answer slots for brand",
            magnitude=3.5,
            direction="down",
            metric_key="ai_answer_presence",
            metric_value=22.0,
        ),
    ]


def demo_series(window_end: datetime | None = None) -> list[MetricSeries]:
    end = window_end or datetime.now(UTC)
    start = end - timedelta(days=30)
    # Stable then sharp drop — should alert
    visibility = []
    for d in range(30):
        ts = start + timedelta(days=d)
        val = 60.0 + (1.0 if d < 18 else -12.0) + (0.2 * math.sin(d))
        visibility.append(MetricSeriesPoint(ts, val))
    # Noisy flat series — should suppress
    noise = []
    for d in range(30):
        ts = start + timedelta(days=d)
        noise.append(MetricSeriesPoint(ts, 50.0 + (0.3 * math.sin(d * 3))))
    return [
        MetricSeries("visibility_index", visibility),
        MetricSeries("noise_metric", noise),
    ]


def analyse_timeline(spec: TimelineSpec) -> TimelineAnalysisResult:
    if not spec.client_brand.strip():
        raise ValueError("client_brand is required")
    if spec.window_end <= spec.window_start:
        raise ValueError("window_end must be after window_start")

    events_in = list(spec.events) if spec.events else demo_events(spec.window_end)
    for e in events_in:
        e.validate()

    # Filter to window
    events_in = [
        e
        for e in events_in
        if spec.window_start <= e.occurred_at <= spec.window_end
    ]
    events_in.sort(key=lambda e: e.occurred_at)

    event_results = [
        EventResult(
            event_kind=e.event_kind,
            event_label=EVENT_LABELS[e.event_kind],
            occurred_at=e.occurred_at,
            title=e.title,
            detail=e.detail,
            magnitude=e.magnitude,
            direction=e.direction,
            metric_key=e.metric_key,
            metric_value=e.metric_value,
            source_ref=e.source_ref,
        )
        for e in events_in
    ]

    series_list = list(spec.series) if spec.series else demo_series(spec.window_end)
    change_points: list[ChangePointResult] = []
    for series in series_list:
        # Clip series to window
        clipped = MetricSeries(
            series.metric_key,
            [
                p
                for p in series.points
                if spec.window_start <= p.occurred_at <= spec.window_end
            ],
        )
        change_points.extend(detect_change_points(clipped))

    alerts = [c for c in change_points if c.is_alert]
    suppressed = [c for c in change_points if c.suppressed_as_noise]

    answers = answer_queries(spec.questions, event_results)

    summary = (
        f"Visibility Timeline for {spec.client_brand}: {len(event_results)} events, "
        f"{len(alerts)} change-point alerts, {len(suppressed)} noise suppressions. "
        f"{NOISE_GUARDRAIL}"
    )

    return TimelineAnalysisResult(
        window_start=spec.window_start,
        window_end=spec.window_end,
        events=event_results,
        change_points=change_points,
        query_answers=answers,
        events_count=len(event_results),
        change_points_count=len(alerts),
        alerts_suppressed=len(suppressed),
        noise_guardrail=NOISE_GUARDRAIL,
        methodology_note=METHODOLOGY_NOTE,
        summary=summary,
    )


def catalog() -> dict[str, Any]:
    return {
        "event_kinds": dict(EVENT_LABELS),
        "event_codes": list(EVENT_KINDS),
        "query_intents": list(QUERY_INTENTS),
        "example_queries": [
            "What changed?",
            "Why did visibility drop?",
            "What happened before citations increased?",
            "Which action preceded our ranking increase?",
        ],
        "noise_guardrail": NOISE_GUARDRAIL,
        "methodology_note": METHODOLOGY_NOTE,
        "change_detection": {
            "min_baseline_points": MIN_BASELINE_POINTS,
            "z_score_alert": Z_SCORE_ALERT,
            "min_effect_size_ratio": MIN_EFFECT_SIZE_RATIO,
        },
    }
