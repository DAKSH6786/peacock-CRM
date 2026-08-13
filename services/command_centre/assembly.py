"""Command Centre assembly — Visibility Index, situation layer, intelligence feed."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from db_models.command_centre import (
    METHODOLOGY_NOTE,
    SITUATION_KINDS,
    SITUATION_LABELS,
    VISIBILITY_DIMENSIONS,
    VISIBILITY_LABELS,
)


@dataclass
class VisibilitySignalSpec:
    dimension: str
    score: float
    delta: float = 0.0

    def validate(self) -> None:
        if self.dimension not in VISIBILITY_DIMENSIONS:
            raise ValueError(f"Unsupported dimension: {self.dimension}")
        if not 0.0 <= self.score <= 100.0:
            raise ValueError("score must be 0–100")


@dataclass
class SituationSpec:
    kind: str
    title: str
    detail: str
    severity: str = "medium"

    def validate(self) -> None:
        if self.kind not in SITUATION_KINDS:
            raise ValueError(f"Unsupported situation kind: {self.kind}")
        if self.severity not in ("low", "medium", "high", "critical"):
            raise ValueError("severity must be low|medium|high|critical")


@dataclass
class FeedItemSpec:
    headline: str
    body: str
    primary_driver: str
    potential_response: str
    confidence: float
    detected_at: datetime | None = None
    graph_surface: str | None = None
    detection_label: str = "PEACOCK DETECTED"

    def validate(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be 0–1")


@dataclass
class CommandCentreSpec:
    client_brand: str
    signals: list[VisibilitySignalSpec] = field(default_factory=list)
    situations: list[SituationSpec] = field(default_factory=list)
    feed_items: list[FeedItemSpec] = field(default_factory=list)
    captured_at: datetime | None = None


@dataclass(slots=True)
class VisibilitySignalResult:
    dimension: str
    label: str
    score: float
    delta: float
    rank_order: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SituationResult:
    kind: str
    label: str
    title: str
    detail: str
    severity: str
    rank_order: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class FeedItemResult:
    feed_index: int
    detection_label: str
    headline: str
    body: str
    primary_driver: str
    potential_response: str
    confidence: float
    detected_at: datetime
    graph_surface: str | None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["detected_at"] = self.detected_at.isoformat()
        d["confidence_pct"] = int(round(self.confidence * 100))
        return d


@dataclass
class CommandCentreResult:
    client_brand: str
    visibility_index: float
    visibility_delta: float
    captured_at: datetime
    headline: str
    signals: list[VisibilitySignalResult]
    situations: list[SituationResult]
    feed_items: list[FeedItemResult]
    methodology_note: str
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "client_brand": self.client_brand,
            "visibility_index": self.visibility_index,
            "visibility_delta": self.visibility_delta,
            "captured_at": self.captured_at.isoformat(),
            "headline": self.headline,
            "signals": [s.to_dict() for s in self.signals],
            "situations": [s.to_dict() for s in self.situations],
            "feed_items": [f.to_dict() for f in self.feed_items],
            "methodology_note": self.methodology_note,
            "summary": self.summary,
        }


def catalog() -> dict[str, Any]:
    return {
        "visibility_dimensions": list(VISIBILITY_DIMENSIONS),
        "visibility_labels": dict(VISIBILITY_LABELS),
        "situation_kinds": list(SITUATION_KINDS),
        "situation_labels": dict(SITUATION_LABELS),
        "methodology_note": METHODOLOGY_NOTE,
        "product_note": (
            "Peacock Command Centre is the flagship UI — Visibility Index, "
            "situation briefing, and PEACOCK DETECTED intelligence feed. "
            "It is not a generic SEO dashboard."
        ),
    }


def demo_signals() -> list[VisibilitySignalSpec]:
    return [
        VisibilitySignalSpec("search_visibility", 72.0, +1.4),
        VisibilitySignalSpec("ai_visibility", 58.0, -3.8),
        VisibilitySignalSpec("share_of_answer", 41.0, -2.1),
        VisibilitySignalSpec("entity_authority", 63.0, +0.6),
        VisibilitySignalSpec("citation_authority", 47.0, -5.2),
        VisibilitySignalSpec("content_opportunity", 81.0, +4.0),
        VisibilitySignalSpec("agent_readiness", 54.0, +1.1),
    ]


def demo_situations(brand: str, competitor: str = "Competitor A") -> list[SituationSpec]:
    return [
        SituationSpec(
            "biggest_opportunity",
            "Proprietary benchmark study",
            f"Publishing an owned benchmark can reclaim citation share {brand} lost on commercial prompts.",
            "high",
        ),
        SituationSpec(
            "biggest_threat",
            f"{competitor} citation surge",
            f"{competitor} citation share jumped 18% → 31% on category research queries.",
            "critical",
        ),
        SituationSpec(
            "fastest_win",
            "Refresh /compare + /pricing hubs",
            "Entity-dense comparison tables are the shortest path to SoA recovery this sprint.",
            "high",
        ),
        SituationSpec(
            "competitor_movement",
            f"{competitor} shipped 3 research pages",
            "Those pages are the primary driver behind the citation-share acceleration.",
            "high",
        ),
        SituationSpec(
            "ai_visibility_change",
            "AI Visibility −3.8 this week",
            "Claude and Perplexity presence softened; ChatGPT held flatter.",
            "medium",
        ),
        SituationSpec(
            "critical_technical_issue",
            "Indexation gap on /guides/*",
            "Agent and crawler readiness checks flag thin schema + blocked snippets on guide templates.",
            "critical",
        ),
    ]


def demo_feed(competitor: str = "Competitor A") -> list[FeedItemSpec]:
    now = datetime.now(tz=UTC)
    return [
        FeedItemSpec(
            headline=f"{competitor} increased citation share",
            body=f"{competitor} increased citation share from 18% → 31%.",
            primary_driver="3 recently published research pages.",
            potential_response="Publish proprietary benchmark study.",
            confidence=0.87,
            detected_at=now - timedelta(hours=2),
            graph_surface="citation_graph",
        ),
        FeedItemSpec(
            headline="AI Visibility dipped across two engines",
            body="Share of Answer softened on Claude (−4pp) and Perplexity (−2pp) week-over-week.",
            primary_driver="Citation disappearance on commercial prompt cluster.",
            potential_response="Reinforce comparison hubs with quotable specs and sources.",
            confidence=0.81,
            detected_at=now - timedelta(hours=5),
            graph_surface="anomaly_engine",
        ),
        FeedItemSpec(
            headline="Content opportunity cluster opened on /security",
            body="Opportunity Engine ranks /security in the top GEO improvement set.",
            primary_driver="Entity Authority gap on ‘enterprise reliability’ facet.",
            potential_response="Assign evidence-dense writer; ship FAQ + source block variant.",
            confidence=0.76,
            detected_at=now - timedelta(hours=9),
            graph_surface="opportunity_engine",
        ),
    ]


def _weighted_index(signals: list[VisibilitySignalResult]) -> float:
    # Equal weight across dimensions for the flagship index
    if not signals:
        return 0.0
    return round(sum(s.score for s in signals) / len(signals), 1)


def assemble_command_centre(spec: CommandCentreSpec) -> CommandCentreResult:
    brand = (spec.client_brand or "").strip()
    if not brand:
        raise ValueError("client_brand is required")

    for s in spec.signals:
        s.validate()
    for s in spec.situations:
        s.validate()
    for f in spec.feed_items:
        f.validate()

    signal_specs = list(spec.signals) or demo_signals()
    situation_specs = list(spec.situations) or demo_situations(brand)
    feed_specs = list(spec.feed_items) or demo_feed()

    # Ensure all dimensions present (fill demo for missing)
    have = {s.dimension for s in signal_specs}
    for d in VISIBILITY_DIMENSIONS:
        if d not in have:
            demo = next(x for x in demo_signals() if x.dimension == d)
            signal_specs.append(demo)

    signals = [
        VisibilitySignalResult(
            dimension=s.dimension,
            label=VISIBILITY_LABELS[s.dimension],
            score=round(s.score, 1),
            delta=round(s.delta, 1),
            rank_order=i,
        )
        for i, s in enumerate(
            sorted(
                signal_specs,
                key=lambda x: VISIBILITY_DIMENSIONS.index(x.dimension),
            )
        )
    ]

    # Situations in canonical order
    by_kind = {s.kind: s for s in situation_specs}
    situations: list[SituationResult] = []
    for i, kind in enumerate(SITUATION_KINDS):
        s = by_kind.get(kind) or next(x for x in demo_situations(brand) if x.kind == kind)
        situations.append(
            SituationResult(
                kind=kind,
                label=SITUATION_LABELS[kind],
                title=s.title,
                detail=s.detail,
                severity=s.severity,
                rank_order=i,
            )
        )

    captured = spec.captured_at or datetime.now(tz=UTC)
    feed_items = [
        FeedItemResult(
            feed_index=i,
            detection_label=f.detection_label,
            headline=f.headline,
            body=f.body,
            primary_driver=f.primary_driver,
            potential_response=f.potential_response,
            confidence=round(f.confidence, 3),
            detected_at=f.detected_at or (captured - timedelta(hours=i + 1)),
            graph_surface=f.graph_surface,
        )
        for i, f in enumerate(feed_specs)
    ]

    index = _weighted_index(signals)
    delta = round(sum(s.delta for s in signals) / max(len(signals), 1), 1)
    headline = f"{brand} · Peacock Visibility Index {index:.0f}"
    summary = (
        f"Command Centre for {brand}: Visibility Index {index:.1f} "
        f"({delta:+.1f}), {len(situations)} situation signals, "
        f"{len(feed_items)} intelligence detections."
    )

    return CommandCentreResult(
        client_brand=brand,
        visibility_index=index,
        visibility_delta=delta,
        captured_at=captured,
        headline=headline,
        signals=signals,
        situations=situations,
        feed_items=feed_items,
        methodology_note=METHODOLOGY_NOTE,
        summary=summary,
    )
