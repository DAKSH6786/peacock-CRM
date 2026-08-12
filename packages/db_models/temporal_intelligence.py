"""Peacock Temporal Intelligence — Visibility Timeline + change-point detection.

Understands change across search, AI answers, citations, competitors, entities,
sentiment, content, algorithm events, and Peacock actions. Supports “What changed?”
queries and statistical change-point detection that ignores meaningless noise.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db_models.base import Base, WorkspaceTenantMixin


EVENT_KINDS: tuple[str, ...] = (
    "search_change",
    "ai_answer_change",
    "citation_change",
    "competitor_change",
    "entity_change",
    "sentiment_change",
    "content_update",
    "algorithm_event",
    "peacock_action",
)

EVENT_LABELS: dict[str, str] = {
    "search_change": "Search changes",
    "ai_answer_change": "AI answer changes",
    "citation_change": "Citation changes",
    "competitor_change": "Competitor changes",
    "entity_change": "Entity changes",
    "sentiment_change": "Sentiment changes",
    "content_update": "Content updates",
    "algorithm_event": "Algorithm events",
    "peacock_action": "Peacock actions",
}

QUERY_INTENTS: tuple[str, ...] = (
    "what_changed",
    "why_visibility_drop",
    "before_citations_increased",
    "action_preceded_ranking_increase",
    "custom",
)

NOISE_GUARDRAIL = (
    "Change-point detection suppresses meaningless noise: only statistically "
    "unusual shifts (relative to recent baseline variance and minimum effect size) "
    "are promoted to alerts."
)

METHODOLOGY = "peacock_temporal_intelligence_visibility_timeline"
METHODOLOGY_NOTE = (
    "Peacock Temporal Intelligence builds a Visibility Timeline across search, AI "
    "answers, citations, competitors, entities, sentiment, content updates, "
    "algorithm events, and Peacock actions. It answers change questions and runs "
    "statistical change-point detection where data volume allows, without alerting "
    "on meaningless noise. "
    + NOISE_GUARDRAIL
)


class TemporalTimeline(Base, WorkspaceTenantMixin):
    """A Visibility Timeline analysis window."""

    __tablename__ = "temporal_timelines"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_brand: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    analysis_status: Mapped[str] = mapped_column(
        String(32), default="completed", nullable=False, index=True
    )
    methodology: Mapped[str] = mapped_column(String(64), default=METHODOLOGY, nullable=False)
    noise_guardrail: Mapped[str] = mapped_column(Text, nullable=False)
    events_count: Mapped[int] = mapped_column(Integer, nullable=False)
    change_points_count: Mapped[int] = mapped_column(Integer, nullable=False)
    alerts_suppressed: Mapped[int] = mapped_column(Integer, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)

    events: Mapped[list[TiTimelineEvent]] = relationship(
        back_populates="timeline", cascade="all, delete-orphan", passive_deletes=True
    )
    change_points: Mapped[list[TiChangePoint]] = relationship(
        back_populates="timeline", cascade="all, delete-orphan", passive_deletes=True
    )
    query_answers: Mapped[list[TiQueryAnswer]] = relationship(
        back_populates="timeline", cascade="all, delete-orphan", passive_deletes=True
    )


class TiTimelineEvent(Base, WorkspaceTenantMixin):
    """One event on the Visibility Timeline."""

    __tablename__ = "ti_timeline_events"

    timeline_id: Mapped[str] = mapped_column(
        ForeignKey("temporal_timelines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_kind: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    event_label: Mapped[str] = mapped_column(String(255), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False)
    magnitude: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    direction: Mapped[str] = mapped_column(String(16), default="neutral", nullable=False)
    metric_key: Mapped[str | None] = mapped_column(String(128), index=True)
    metric_value: Mapped[float | None] = mapped_column(Float)
    source_ref: Mapped[str | None] = mapped_column(String(255))

    timeline: Mapped[TemporalTimeline] = relationship(back_populates="events")


class TiChangePoint(Base, WorkspaceTenantMixin):
    """Statistically unusual shift — noise filtered."""

    __tablename__ = "ti_change_points"
    __table_args__ = (UniqueConstraint("timeline_id", "metric_key", "detected_at"),)

    timeline_id: Mapped[str] = mapped_column(
        ForeignKey("temporal_timelines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    metric_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    effect_size: Mapped[float] = mapped_column(Float, nullable=False)
    baseline_mean: Mapped[float] = mapped_column(Float, nullable=False)
    baseline_std: Mapped[float] = mapped_column(Float, nullable=False)
    post_mean: Mapped[float] = mapped_column(Float, nullable=False)
    is_alert: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    suppressed_as_noise: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )
    rationale: Mapped[str] = mapped_column(Text, nullable=False)

    timeline: Mapped[TemporalTimeline] = relationship(back_populates="change_points")


class TiQueryAnswer(Base, WorkspaceTenantMixin):
    """Answer to a temporal intelligence query against the timeline."""

    __tablename__ = "ti_query_answers"

    timeline_id: Mapped[str] = mapped_column(
        ForeignKey("temporal_timelines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    intent: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    supporting_event_ids: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    timeline: Mapped[TemporalTimeline] = relationship(back_populates="query_answers")
