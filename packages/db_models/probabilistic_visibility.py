"""Probabilistic AI Visibility — controlled multi-run measurement.

Never treat a single generative response as truth. Visibility is estimated
from configurable, rate-limited repetitions across engines / contexts.
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

from db_models.base import Base, TimestampMixin, WorkspaceTenantMixin, new_uuid


class VisibilityCampaign(Base, WorkspaceTenantMixin):
    """A controlled probabilistic visibility measurement campaign."""

    __tablename__ = "visibility_campaigns"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    brand_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    # Rate-limit / anti-abuse envelope (never uncontrolled traffic)
    target_repetitions: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    max_repetitions: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    max_calls_per_minute: Mapped[int] = mapped_column(Integer, default=6, nullable=False)
    max_concurrent: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_total_calls: Mapped[int] = mapped_column(Integer, default=500, nullable=False)
    min_interval_ms: Mapped[int] = mapped_column(Integer, default=1500, nullable=False)
    campaign_status: Mapped[str] = mapped_column(
        String(32), default="draft", nullable=False, index=True
    )
    notes: Mapped[str | None] = mapped_column(Text)

    cells: Mapped[list[VisibilityProbeCell]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan", passive_deletes=True
    )
    observations: Mapped[list[VisibilityProbeObservation]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan", passive_deletes=True
    )
    distributions: Mapped[list[VisibilityDistribution]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan", passive_deletes=True
    )
    score_cards: Mapped[list[VisibilityScoreCard]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan", passive_deletes=True
    )


class VisibilityProbeCell(Base, WorkspaceTenantMixin):
    """Controlled cell: Prompt × Model × Location × Persona × Config × Time bucket."""

    __tablename__ = "visibility_probe_cells"
    __table_args__ = (
        UniqueConstraint(
            "campaign_id",
            "prompt_hash",
            "engine_code",
            "location_code",
            "persona_code",
            "config_code",
            "time_bucket",
        ),
    )

    campaign_id: Mapped[str] = mapped_column(
        ForeignKey("visibility_campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    engine_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    model_code: Mapped[str | None] = mapped_column(String(128))
    location_code: Mapped[str] = mapped_column(String(64), default="global", nullable=False, index=True)
    persona_code: Mapped[str] = mapped_column(String(64), default="default", nullable=False, index=True)
    config_code: Mapped[str] = mapped_column(String(64), default="temp_0.2", nullable=False, index=True)
    temperature: Mapped[float] = mapped_column(Float, default=0.2, nullable=False)
    time_bucket: Mapped[str] = mapped_column(String(32), default="current", nullable=False, index=True)
    target_repetitions: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    completed_repetitions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    generative_engine_id: Mapped[str | None] = mapped_column(
        ForeignKey("generative_engines.id", ondelete="SET NULL"), nullable=True, index=True
    )
    ai_query_id: Mapped[str | None] = mapped_column(
        ForeignKey("ai_queries.id", ondelete="SET NULL"), nullable=True, index=True
    )

    campaign: Mapped[VisibilityCampaign] = relationship(back_populates="cells")
    observations: Mapped[list[VisibilityProbeObservation]] = relationship(
        back_populates="cell", cascade="all, delete-orphan", passive_deletes=True
    )


class VisibilityProbeObservation(Base, WorkspaceTenantMixin):
    """One controlled repetition outcome — never the sole source of truth."""

    __tablename__ = "visibility_probe_observations"
    __table_args__ = (UniqueConstraint("cell_id", "run_index"),)

    campaign_id: Mapped[str] = mapped_column(
        ForeignKey("visibility_campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    cell_id: Mapped[str] = mapped_column(
        ForeignKey("visibility_probe_cells.id", ondelete="CASCADE"), nullable=False, index=True
    )
    run_index: Mapped[int] = mapped_column(Integer, nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    brand_mentioned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    brand_cited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    brand_top3: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    brand_position: Mapped[int | None] = mapped_column(Integer)
    # Competitor hits stored as comma-separated codes for relational simplicity
    competitor_mentions: Mapped[str | None] = mapped_column(Text)
    raw_excerpt: Mapped[str | None] = mapped_column(Text)
    structured_summary: Mapped[str | None] = mapped_column(Text)
    ai_query_run_id: Mapped[str | None] = mapped_column(
        ForeignKey("ai_query_runs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    probe_source: Mapped[str] = mapped_column(String(32), default="mock", nullable=False)

    campaign: Mapped[VisibilityCampaign] = relationship(back_populates="observations")
    cell: Mapped[VisibilityProbeCell] = relationship(back_populates="observations")


class VisibilityDistribution(Base, WorkspaceTenantMixin):
    """Distributional metric derived from controlled repetitions — not a single shot."""

    __tablename__ = "visibility_distributions"
    __table_args__ = (
        UniqueConstraint("campaign_id", "metric_key", "subject_key", "scope_key"),
    )

    campaign_id: Mapped[str] = mapped_column(
        ForeignKey("visibility_campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    metric_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    # e.g. brand | competitor:acme | engine:chatgpt
    subject_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    scope_key: Mapped[str] = mapped_column(String(128), default="campaign", nullable=False)
    probability: Mapped[float] = mapped_column(Float, nullable=False)
    variance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    ci_low: Mapped[float] = mapped_column(Float, nullable=False)
    ci_high: Mapped[float] = mapped_column(Float, nullable=False)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False)
    engine_disagreement: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    temporal_volatility: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    success_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    campaign: Mapped[VisibilityCampaign] = relationship(back_populates="distributions")


class VisibilityScoreCard(Base, WorkspaceTenantMixin):
    """Defensible score card: score + measurement confidence + observation basis."""

    __tablename__ = "visibility_score_cards"

    campaign_id: Mapped[str] = mapped_column(
        ForeignKey("visibility_campaigns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ai_visibility_score: Mapped[float] = mapped_column(Float, nullable=False)
    measurement_confidence: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    peacock_visibility_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    observation_count: Mapped[int] = mapped_column(Integer, nullable=False)
    engine_count: Mapped[int] = mapped_column(Integer, nullable=False)
    prompt_count: Mapped[int] = mapped_column(Integer, nullable=False)
    period_count: Mapped[int] = mapped_column(Integer, nullable=False)
    brand_mention_probability: Mapped[float] = mapped_column(Float, nullable=False)
    citation_probability: Mapped[float] = mapped_column(Float, nullable=False)
    top3_probability: Mapped[float] = mapped_column(Float, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    campaign: Mapped[VisibilityCampaign] = relationship(back_populates="score_cards")
