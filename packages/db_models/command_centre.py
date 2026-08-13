"""Peacock Command Centre — flagship visibility command snapshot.

Surfaces Peacock Visibility Index dimensions, situation briefing, and an
intelligence feed of PEACOCK DETECTED events — not a generic SEO dashboard.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
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


VISIBILITY_DIMENSIONS: tuple[str, ...] = (
    "search_visibility",
    "ai_visibility",
    "share_of_answer",
    "entity_authority",
    "citation_authority",
    "content_opportunity",
    "agent_readiness",
)

VISIBILITY_LABELS: dict[str, str] = {
    "search_visibility": "Search Visibility",
    "ai_visibility": "AI Visibility",
    "share_of_answer": "Share of Answer",
    "entity_authority": "Entity Authority",
    "citation_authority": "Citation Authority",
    "content_opportunity": "Content Opportunity",
    "agent_readiness": "Agent Readiness",
}

SITUATION_KINDS: tuple[str, ...] = (
    "biggest_opportunity",
    "biggest_threat",
    "fastest_win",
    "competitor_movement",
    "ai_visibility_change",
    "critical_technical_issue",
)

SITUATION_LABELS: dict[str, str] = {
    "biggest_opportunity": "Biggest Opportunity",
    "biggest_threat": "Biggest Threat",
    "fastest_win": "Fastest Win",
    "competitor_movement": "Competitor Movement",
    "ai_visibility_change": "AI Visibility Change",
    "critical_technical_issue": "Critical Technical Issue",
}

METHODOLOGY = "peacock_command_centre_v1"
METHODOLOGY_NOTE = (
    "Peacock Command Centre is the flagship command surface for generative "
    "visibility intelligence. It centres the Peacock Visibility Index, a "
    "situation briefing, and a PEACOCK DETECTED intelligence feed — not a "
    "generic SEO metric dashboard."
)


class CommandCentreSnapshot(Base, WorkspaceTenantMixin):
    """One Command Centre snapshot for a brand/website."""

    __tablename__ = "command_centre_snapshots"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_brand: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    snapshot_status: Mapped[str] = mapped_column(
        String(32), default="completed", nullable=False, index=True
    )
    methodology: Mapped[str] = mapped_column(String(64), default=METHODOLOGY, nullable=False)
    visibility_index: Mapped[float] = mapped_column(Float, nullable=False)
    visibility_delta: Mapped[float] = mapped_column(Float, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    headline: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)

    signals: Mapped[list[CcVisibilitySignal]] = relationship(
        back_populates="snapshot", cascade="all, delete-orphan", passive_deletes=True
    )
    situations: Mapped[list[CcSituationItem]] = relationship(
        back_populates="snapshot", cascade="all, delete-orphan", passive_deletes=True
    )
    feed_items: Mapped[list[CcFeedItem]] = relationship(
        back_populates="snapshot", cascade="all, delete-orphan", passive_deletes=True
    )


class CcVisibilitySignal(Base, WorkspaceTenantMixin):
    """One Peacock Visibility Index dimension."""

    __tablename__ = "cc_visibility_signals"
    __table_args__ = (UniqueConstraint("snapshot_id", "dimension"),)

    snapshot_id: Mapped[str] = mapped_column(
        ForeignKey("command_centre_snapshots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dimension: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    delta: Mapped[float] = mapped_column(Float, nullable=False)
    rank_order: Mapped[int] = mapped_column(Integer, nullable=False)

    snapshot: Mapped[CommandCentreSnapshot] = relationship(back_populates="signals")


class CcSituationItem(Base, WorkspaceTenantMixin):
    """Second-layer situation briefing item."""

    __tablename__ = "cc_situation_items"
    __table_args__ = (UniqueConstraint("snapshot_id", "kind"),)

    snapshot_id: Mapped[str] = mapped_column(
        ForeignKey("command_centre_snapshots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    kind: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    rank_order: Mapped[int] = mapped_column(Integer, nullable=False)

    snapshot: Mapped[CommandCentreSnapshot] = relationship(back_populates="situations")


class CcFeedItem(Base, WorkspaceTenantMixin):
    """Intelligence feed detection (PEACOCK DETECTED)."""

    __tablename__ = "cc_feed_items"
    __table_args__ = (UniqueConstraint("snapshot_id", "feed_index"),)

    snapshot_id: Mapped[str] = mapped_column(
        ForeignKey("command_centre_snapshots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    feed_index: Mapped[int] = mapped_column(Integer, nullable=False)
    detection_label: Mapped[str] = mapped_column(
        String(64), default="PEACOCK DETECTED", nullable=False
    )
    headline: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    primary_driver: Mapped[str] = mapped_column(Text, nullable=False)
    potential_response: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    graph_surface: Mapped[str | None] = mapped_column(String(64), index=True)

    snapshot: Mapped[CommandCentreSnapshot] = relationship(back_populates="feed_items")
