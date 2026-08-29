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


class Recommendation(Base, WorkspaceTenantMixin):
    """Central explainable recommendation record for the learning loop."""

    __tablename__ = "recommendations"

    website_id: Mapped[str | None] = mapped_column(
        ForeignKey("websites.id", ondelete="SET NULL"), nullable=True, index=True
    )
    decision_id: Mapped[str | None] = mapped_column(
        ForeignKey("decisions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    kind: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text)
    impact_score: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    effort_score: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    priority: Mapped[str] = mapped_column(String(16), default="medium", nullable=False, index=True)


class RecommendationExecution(Base, WorkspaceTenantMixin):
    __tablename__ = "recommendation_executions"

    recommendation_id: Mapped[str] = mapped_column(
        ForeignKey("recommendations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    executor_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    notes: Mapped[str | None] = mapped_column(Text)


class RecommendationMetric(Base, WorkspaceTenantMixin):
    __tablename__ = "recommendation_metrics"
    __table_args__ = (UniqueConstraint("recommendation_id", "metric_key"),)

    recommendation_id: Mapped[str] = mapped_column(
        ForeignKey("recommendations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    metric_key: Mapped[str] = mapped_column(String(128), nullable=False)
    baseline_value: Mapped[float | None] = mapped_column(Float)
    target_value: Mapped[float | None] = mapped_column(Float)
    current_value: Mapped[float | None] = mapped_column(Float)


class RecommendationOutcome(Base, WorkspaceTenantMixin):
    __tablename__ = "recommendation_outcomes"

    recommendation_id: Mapped[str] = mapped_column(
        ForeignKey("recommendations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    execution_id: Mapped[str | None] = mapped_column(
        ForeignKey("recommendation_executions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    metric_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)


class FeatureWeight(Base, WorkspaceTenantMixin):
    __tablename__ = "feature_weights"
    __table_args__ = (UniqueConstraint("workspace_id", "kind", "feature_key"),)

    kind: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    feature_key: Mapped[str] = mapped_column(String(128), nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    sample_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class ModelEvaluation(Base, WorkspaceTenantMixin):
    __tablename__ = "model_evaluations"

    model_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    evaluation_type: Mapped[str] = mapped_column(String(64), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    sample_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
