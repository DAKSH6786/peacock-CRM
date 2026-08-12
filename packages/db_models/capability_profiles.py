"""Dynamic model capability profiles for PINE routing.

Profiles are **observed** performance — soft catalog priors exist separately
and must never be treated as permanent role locks
(e.g. Claude≠forever-critic, Perplexity≠forever-research).
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

# Canonical task-type codes tracked per model
CAPABILITY_TASK_TYPES = (
    "RESEARCH",
    "SEO_REASONING",
    "GEO_REASONING",
    "ENTITY_EXTRACTION",
    "CITATION_EXTRACTION",
    "STRUCTURED_OUTPUT",
    "CRITICAL_ANALYSIS",
    "SUMMARISATION",
    "STRATEGY",
    "CONTENT_ANALYSIS",
    "COMPETITOR_ANALYSIS",
    "FACT_VERIFICATION",
    "LONG_CONTEXT_ANALYSIS",
)


class ModelCapabilityPrior(Base, TimestampMixin):
    """Soft default prior for a provider/model on a task type.

    Priors initialise routing when little/no observed data exists.
    They are **not** permanent assumptions and are overridden by
    ``ModelCapabilityProfile`` once sample_size is sufficient.
    """

    __tablename__ = "model_capability_priors"
    __table_args__ = (UniqueConstraint("provider_code", "model_code", "task_type"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    provider_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    model_code: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    task_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    # Expected starting metrics (0–1 rates / scores unless noted)
    quality_score: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    latency_ms: Mapped[float] = mapped_column(Float, default=2000.0, nullable=False)
    cost_usd_micros: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    failure_rate: Mapped[float] = mapped_column(Float, default=0.1, nullable=False)
    json_compliance_rate: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    citation_accuracy: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    historical_agreement: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    # Relative hint only — never a hard lock
    prior_weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)


class ModelCapabilityProfile(Base, WorkspaceTenantMixin):
    """Rolling observed capability of a model for a task type in a workspace."""

    __tablename__ = "model_capability_profiles"
    __table_args__ = (
        UniqueConstraint("workspace_id", "provider_code", "model_code", "task_type"),
    )

    provider_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    model_code: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    task_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    provider_id: Mapped[str | None] = mapped_column(
        ForeignKey("ai_providers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    model_id: Mapped[str | None] = mapped_column(
        ForeignKey("ai_provider_models.id", ondelete="SET NULL"), nullable=True, index=True
    )

    quality_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    latency_ms_avg: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    cost_usd_micros_avg: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    failure_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    json_compliance_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    citation_accuracy: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    historical_agreement: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    sample_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failure_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    observations: Mapped[list[ModelCapabilityObservation]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", passive_deletes=True
    )


class ModelCapabilityObservation(Base, WorkspaceTenantMixin):
    """Single scored model invocation that updates a capability profile."""

    __tablename__ = "model_capability_observations"

    profile_id: Mapped[str] = mapped_column(
        ForeignKey("model_capability_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    model_code: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    task_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    quality_score: Mapped[float | None] = mapped_column(Float)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    cost_usd_micros: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    succeeded: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    json_compliant: Mapped[bool | None] = mapped_column(Boolean)
    citation_accuracy: Mapped[float | None] = mapped_column(Float)
    historical_agreement: Mapped[float | None] = mapped_column(Float)

    gateway_role: Mapped[str | None] = mapped_column(String(64), index=True)
    template_id: Mapped[str | None] = mapped_column(String(128))
    llm_request_id: Mapped[str | None] = mapped_column(
        ForeignKey("llm_requests.id", ondelete="SET NULL"), nullable=True, index=True
    )
    notes: Mapped[str | None] = mapped_column(Text)

    profile: Mapped[ModelCapabilityProfile] = relationship(back_populates="observations")
