"""Peacock Proprietary Metrics — documented scoring framework.

IMPORTANT: Every metric here is a **Peacock proprietary indicator**.
Never represent these as Google, OpenAI, Anthropic, Perplexity, or other
official ranking factors / platform algorithms.
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


METRIC_KEYS: tuple[str, ...] = (
    "peacock_visibility_index",
    "peacock_ai_visibility_score",
    "share_of_answer",
    "citation_influence_score",
    "entity_authority_score",
    "answer_readiness_score",
    "generative_citability_score",
    "content_moat_score",
    "topic_opportunity_score",
    "writer_match_score",
    "agent_readiness_score",
    "competitive_threat_score",
    "opportunity_confidence",
)

METRIC_LABELS: dict[str, str] = {
    "peacock_visibility_index": "Peacock Visibility Index",
    "peacock_ai_visibility_score": "Peacock AI Visibility Score",
    "share_of_answer": "Share of Answer",
    "citation_influence_score": "Citation Influence Score",
    "entity_authority_score": "Entity Authority Score",
    "answer_readiness_score": "Answer Readiness Score",
    "generative_citability_score": "Generative Citability Score",
    "content_moat_score": "Content Moat Score",
    "topic_opportunity_score": "Topic Opportunity Score",
    "writer_match_score": "Writer Match Score",
    "agent_readiness_score": "Agent Readiness Score",
    "competitive_threat_score": "Competitive Threat Score",
    "opportunity_confidence": "Opportunity Confidence",
}

PROPRIETARY_DISCLAIMER = (
    "All Peacock Proprietary Metrics are Peacock One indicators for internal "
    "decision support. They are NOT Google ranking factors, NOT OpenAI / ChatGPT "
    "ranking factors, NOT Anthropic / Claude ranking factors, NOT Perplexity "
    "ranking factors, and NOT any other platform's official algorithms. Peacock "
    "does not claim access to proprietary third-party ranking systems."
)

NOT_OFFICIAL_PLATFORMS: tuple[str, ...] = (
    "Google",
    "OpenAI",
    "ChatGPT",
    "Anthropic",
    "Claude",
    "Perplexity",
    "Bing",
    "Gemini",
)

METHODOLOGY = "peacock_proprietary_metrics_v1"
METHODOLOGY_NOTE = (
    "Peacock Proprietary Metrics define a documented scoring framework for "
    "generative visibility intelligence. Every formula is published in-product. "
    + PROPRIETARY_DISCLAIMER
)


class ProprietaryMetricScorecard(Base, WorkspaceTenantMixin):
    """One proprietary metrics scorecard for a brand/website."""

    __tablename__ = "proprietary_metric_scorecards"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_brand: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    scorecard_status: Mapped[str] = mapped_column(
        String(32), default="completed", nullable=False, index=True
    )
    methodology: Mapped[str] = mapped_column(String(64), default=METHODOLOGY, nullable=False)
    scored_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    metrics_scored: Mapped[int] = mapped_column(Integer, nullable=False)
    proprietary_disclaimer: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)

    scores: Mapped[list[PmMetricScore]] = relationship(
        back_populates="scorecard", cascade="all, delete-orphan", passive_deletes=True
    )


class PmMetricScore(Base, WorkspaceTenantMixin):
    """One proprietary metric score with formula reference."""

    __tablename__ = "pm_metric_scores"
    __table_args__ = (UniqueConstraint("scorecard_id", "metric_key"),)

    scorecard_id: Mapped[str] = mapped_column(
        ForeignKey("proprietary_metric_scorecards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    metric_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    metric_label: Mapped[str] = mapped_column(String(128), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    formula_id: Mapped[str] = mapped_column(String(64), nullable=False)
    formula_text: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    proprietary_note: Mapped[str] = mapped_column(Text, nullable=False)
    rank_order: Mapped[int] = mapped_column(Integer, nullable=False)

    scorecard: Mapped[ProprietaryMetricScorecard] = relationship(back_populates="scores")
    components: Mapped[list[PmMetricComponent]] = relationship(
        back_populates="metric_score", cascade="all, delete-orphan", passive_deletes=True
    )


class PmMetricComponent(Base, WorkspaceTenantMixin):
    """Component contribution for a proprietary metric score."""

    __tablename__ = "pm_metric_components"
    __table_args__ = (UniqueConstraint("metric_score_id", "component_key"),)

    metric_score_id: Mapped[str] = mapped_column(
        ForeignKey("pm_metric_scores.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    component_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    component_label: Mapped[str] = mapped_column(String(128), nullable=False)
    raw_value: Mapped[float] = mapped_column(Float, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    contribution: Mapped[float] = mapped_column(Float, nullable=False)
    rank_order: Mapped[int] = mapped_column(Integer, nullable=False)

    metric_score: Mapped[PmMetricScore] = relationship(back_populates="components")
