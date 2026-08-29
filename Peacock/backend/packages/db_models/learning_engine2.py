"""Peacock Learning Engine 2.0 — long-term moat via recommendation→outcome learning.

For every recommendation store: Context, Recommendation, Expected Impact, Confidence,
Execution, Actual Outcome. Learn which topics/formats/sources/writers/interventions
work, how industries and engines differ. Industry-specific policies — never one
universal GEO strategy.
"""

from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db_models.base import Base, WorkspaceTenantMixin


INDUSTRIES: tuple[str, ...] = (
    "finance",
    "healthcare",
    "saas",
    "ecommerce",
    "education",
    "travel",
    "legal",
    "consumer_goods",
    "technology",
)

INDUSTRY_LABELS: dict[str, str] = {
    "finance": "Finance",
    "healthcare": "Healthcare",
    "saas": "SaaS",
    "ecommerce": "E-commerce",
    "education": "Education",
    "travel": "Travel",
    "legal": "Legal",
    "consumer_goods": "Consumer goods",
    "technology": "Technology",
}

LEARNING_DIMENSIONS: tuple[str, ...] = (
    "topic",
    "format",
    "source",
    "writer",
    "citation_intervention",
    "industry",
    "engine",
)

RECORD_STATUSES: tuple[str, ...] = (
    "draft",
    "recommended",
    "executing",
    "executed",
    "outcome_recorded",
    "learned",
)

NOT_UNIVERSAL_GEO = (
    "Do not apply one universal GEO strategy. Peacock Learning Engine 2.0 maintains "
    "industry-specific policies (Finance, Healthcare, SaaS, E-commerce, Education, "
    "Travel, Legal, Consumer goods, Technology) and learns per-industry behaviour."
)

METHODOLOGY = "peacock_learning_engine_2_closed_loop"
METHODOLOGY_NOTE = (
    "Peacock Learning Engine 2.0 is the long-term moat: every recommendation stores "
    "Context, Recommendation, Expected Impact, Confidence, Execution, and Actual "
    "Outcome, then learns which topics, formats, sources, writers, citation "
    "interventions, industries, and engines succeed. "
    + NOT_UNIVERSAL_GEO
)


class Learning2Record(Base, WorkspaceTenantMixin):
    """Closed-loop learning record for one recommendation lifecycle."""

    __tablename__ = "learning2_records"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    central_recommendation_id: Mapped[str | None] = mapped_column(
        ForeignKey("recommendations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    record_status: Mapped[str] = mapped_column(
        String(32), default="recommended", nullable=False, index=True
    )
    context_summary: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation_text: Mapped[str] = mapped_column(Text, nullable=False)
    expected_impact: Mapped[str] = mapped_column(Text, nullable=False)
    expected_impact_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    execution_summary: Mapped[str | None] = mapped_column(Text)
    execution_status: Mapped[str | None] = mapped_column(String(32), index=True)
    actual_outcome: Mapped[str | None] = mapped_column(Text)
    actual_outcome_score: Mapped[float | None] = mapped_column(Float)
    outcome_delta: Mapped[float | None] = mapped_column(Float)
    topic_key: Mapped[str | None] = mapped_column(String(128), index=True)
    format_key: Mapped[str | None] = mapped_column(String(128), index=True)
    source_key: Mapped[str | None] = mapped_column(String(128), index=True)
    writer_key: Mapped[str | None] = mapped_column(String(128), index=True)
    intervention_key: Mapped[str | None] = mapped_column(String(128), index=True)
    engine_key: Mapped[str | None] = mapped_column(String(128), index=True)
    methodology: Mapped[str] = mapped_column(String(64), default=METHODOLOGY, nullable=False)
    not_universal_geo_strategy: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    not_universal_geo_note: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    context_factors: Mapped[list[Le2ContextFactor]] = relationship(
        back_populates="record", cascade="all, delete-orphan", passive_deletes=True
    )


class Le2ContextFactor(Base, WorkspaceTenantMixin):
    """Structured context signal attached to a learning record."""

    __tablename__ = "le2_context_factors"
    __table_args__ = (UniqueConstraint("record_id", "factor_key"),)

    record_id: Mapped[str] = mapped_column(
        ForeignKey("learning2_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    factor_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    factor_value: Mapped[str] = mapped_column(Text, nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    record: Mapped[Learning2Record] = relationship(back_populates="context_factors")


class Le2IndustryPolicy(Base, WorkspaceTenantMixin):
    """Industry-specific learning policy — not a universal GEO strategy."""

    __tablename__ = "le2_industry_policies"
    __table_args__ = (UniqueConstraint("organisation_id", "industry", "policy_code"),)

    industry: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    policy_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    guidance: Mapped[str] = mapped_column(Text, nullable=False)
    preferred_formats: Mapped[str | None] = mapped_column(Text)
    preferred_sources: Mapped[str | None] = mapped_column(Text)
    citation_interventions: Mapped[str | None] = mapped_column(Text)
    forbidden_universal_claims: Mapped[str] = mapped_column(Text, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    sample_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_rate: Mapped[float | None] = mapped_column(Float)


class Le2DimensionInsight(Base, WorkspaceTenantMixin):
    """Aggregated learning insight for a dimension (topic/format/source/…)."""

    __tablename__ = "le2_dimension_insights"
    __table_args__ = (
        UniqueConstraint("organisation_id", "dimension", "dimension_key", "industry"),
    )

    dimension: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    dimension_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    industry: Mapped[str] = mapped_column(
        String(64), default="all", nullable=False, index=True
    )
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_expected_impact: Mapped[float] = mapped_column(Float, nullable=False)
    avg_actual_outcome: Mapped[float] = mapped_column(Float, nullable=False)
    avg_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    success_rate: Mapped[float] = mapped_column(Float, nullable=False)
    insight_summary: Mapped[str] = mapped_column(Text, nullable=False)
    not_universal_geo_strategy: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )


class Le2LearningRun(Base, WorkspaceTenantMixin):
    """One learning refresh across records → insights + policy updates."""

    __tablename__ = "le2_learning_runs"

    website_id: Mapped[str | None] = mapped_column(
        ForeignKey("websites.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    records_considered: Mapped[int] = mapped_column(Integer, nullable=False)
    insights_generated: Mapped[int] = mapped_column(Integer, nullable=False)
    industries_touched: Mapped[str] = mapped_column(Text, nullable=False)
    not_universal_geo_strategy: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    methodology_note: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
