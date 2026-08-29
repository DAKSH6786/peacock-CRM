"""Peacock Executive Brain — CEO/CMO-ready executive view.

Answers the executive questions without SEO complexity:
Where are we winning? Losing? Why? What changed? What is worth doing?
What will it cost? What could it return? What happens if we do nothing?
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


EXECUTIVE_QUESTIONS: tuple[str, ...] = (
    "where_winning",
    "where_losing",
    "why",
    "what_changed",
    "worth_doing",
    "what_cost",
    "what_return",
    "if_do_nothing",
)

EXECUTIVE_QUESTION_LABELS: dict[str, str] = {
    "where_winning": "Where are we winning?",
    "where_losing": "Where are we losing?",
    "why": "Why?",
    "what_changed": "What changed?",
    "worth_doing": "What is worth doing?",
    "what_cost": "What will it cost?",
    "what_return": "What could it return?",
    "if_do_nothing": "What happens if we do nothing?",
}

SUMMARY_ROLES: tuple[str, ...] = ("ceo", "cmo")

METHODOLOGY = "peacock_executive_brain_v1"
METHODOLOGY_NOTE = (
    "Peacock Executive Brain is a special executive view. It strips SEO "
    "complexity into winning/losing, why, change, action, cost, return, and "
    "do-nothing risk — with CEO- and CMO-ready summaries. Ranges and "
    "confidence are directional, not guaranteed P&L."
)


class ExecutiveBrainBrief(Base, WorkspaceTenantMixin):
    """One Executive Brain briefing for a brand/website."""

    __tablename__ = "executive_brain_briefs"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_brand: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    brief_status: Mapped[str] = mapped_column(
        String(32), default="completed", nullable=False, index=True
    )
    methodology: Mapped[str] = mapped_column(String(64), default=METHODOLOGY, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    horizon_days: Mapped[int] = mapped_column(Integer, default=90, nullable=False)
    budget_label: Mapped[str | None] = mapped_column(String(64))
    overall_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    headline: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)

    answers: Mapped[list[EbAnswer]] = relationship(
        back_populates="brief", cascade="all, delete-orphan", passive_deletes=True
    )
    role_summaries: Mapped[list[EbRoleSummary]] = relationship(
        back_populates="brief", cascade="all, delete-orphan", passive_deletes=True
    )


class EbAnswer(Base, WorkspaceTenantMixin):
    """Answer to one executive question."""

    __tablename__ = "eb_answers"
    __table_args__ = (UniqueConstraint("brief_id", "question_key"),)

    brief_id: Mapped[str] = mapped_column(
        ForeignKey("executive_brain_briefs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    question_label: Mapped[str] = mapped_column(String(255), nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_note: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    rank_order: Mapped[int] = mapped_column(Integer, nullable=False)

    brief: Mapped[ExecutiveBrainBrief] = relationship(back_populates="answers")


class EbRoleSummary(Base, WorkspaceTenantMixin):
    """CEO- or CMO-ready executive summary."""

    __tablename__ = "eb_role_summaries"
    __table_args__ = (UniqueConstraint("brief_id", "role"),)

    brief_id: Mapped[str] = mapped_column(
        ForeignKey("executive_brain_briefs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    call_to_action: Mapped[str] = mapped_column(Text, nullable=False)

    brief: Mapped[ExecutiveBrainBrief] = relationship(back_populates="role_summaries")
