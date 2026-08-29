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


class GenerativeEngine(Base, TimestampMixin):
    """Catalog of generative / answer engines used for visibility probes."""

    __tablename__ = "generative_engines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    vendor: Mapped[str] = mapped_column(String(128), nullable=False)
    llm_provider_id: Mapped[str | None] = mapped_column(
        ForeignKey("ai_providers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)


class AIQuery(Base, WorkspaceTenantMixin):
    __tablename__ = "ai_queries"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    phrase: Mapped[str] = mapped_column(String(1024), nullable=False)
    locale: Mapped[str] = mapped_column(String(32), default="en-US", nullable=False)
    intent: Mapped[str | None] = mapped_column(String(64))
    priority: Mapped[str] = mapped_column(String(16), default="medium", nullable=False)


class AIQueryRun(Base, WorkspaceTenantMixin):
    __tablename__ = "ai_query_runs"

    ai_query_id: Mapped[str] = mapped_column(
        ForeignKey("ai_queries.id", ondelete="CASCADE"), nullable=False, index=True
    )
    generative_engine_id: Mapped[str] = mapped_column(
        ForeignKey("generative_engines.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_summary: Mapped[str | None] = mapped_column(Text)


class AIResponseObservation(Base, WorkspaceTenantMixin):
    __tablename__ = "ai_response_observations"

    ai_query_run_id: Mapped[str] = mapped_column(
        ForeignKey("ai_query_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    raw_excerpt: Mapped[str | None] = mapped_column(Text)
    # Never store private chain-of-thought — structured summary only
    structured_summary: Mapped[str | None] = mapped_column(Text)
    sentiment: Mapped[float | None] = mapped_column(Float)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class BrandMention(Base, WorkspaceTenantMixin):
    __tablename__ = "brand_mentions"

    observation_id: Mapped[str] = mapped_column(
        ForeignKey("ai_response_observations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    brand_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    mentioned: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    position_hint: Mapped[int | None] = mapped_column(Integer)
    sentiment: Mapped[float | None] = mapped_column(Float)


class CitationObservation(Base, WorkspaceTenantMixin):
    __tablename__ = "citation_observations"

    observation_id: Mapped[str] = mapped_column(
        ForeignKey("ai_response_observations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    cited_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    cited_domain: Mapped[str | None] = mapped_column(String(255), index=True)
    is_owned_property: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class EntityObservation(Base, WorkspaceTenantMixin):
    __tablename__ = "entity_observations"

    observation_id: Mapped[str] = mapped_column(
        ForeignKey("ai_response_observations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entity_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    confidence: Mapped[float | None] = mapped_column(Float)


class AEOObservation(Base, WorkspaceTenantMixin):
    __tablename__ = "aeo_observations"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    observation_id: Mapped[str | None] = mapped_column(
        ForeignKey("ai_response_observations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    answerability_score: Mapped[float] = mapped_column(Float, nullable=False)
    faq_coverage_score: Mapped[float | None] = mapped_column(Float)
    citation_readiness_score: Mapped[float | None] = mapped_column(Float)
    notes: Mapped[str | None] = mapped_column(Text)


class GEOMetric(Base, WorkspaceTenantMixin):
    __tablename__ = "geo_metrics"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    metric_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(32))
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AIVisibilitySnapshot(Base, WorkspaceTenantMixin):
    __tablename__ = "ai_visibility_snapshots"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    generative_engine_id: Mapped[str | None] = mapped_column(
        ForeignKey("generative_engines.id", ondelete="SET NULL"), nullable=True, index=True
    )
    mention_rate: Mapped[float] = mapped_column(Float, nullable=False)
    citation_rate: Mapped[float] = mapped_column(Float, nullable=False)
    query_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
