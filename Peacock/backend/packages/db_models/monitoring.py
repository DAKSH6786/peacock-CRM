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


class MonitoringProject(Base, WorkspaceTenantMixin):
    __tablename__ = "monitoring_projects"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    cadence: Mapped[str] = mapped_column(String(32), default="weekly", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class MetricSnapshot(Base, WorkspaceTenantMixin):
    __tablename__ = "metric_snapshots"

    monitoring_project_id: Mapped[str] = mapped_column(
        ForeignKey("monitoring_projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    metric_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class SearchPerformanceSnapshot(Base, WorkspaceTenantMixin):
    __tablename__ = "search_performance_snapshots"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    monitoring_project_id: Mapped[str | None] = mapped_column(
        ForeignKey("monitoring_projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    clicks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    impressions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ctr: Mapped[float | None] = mapped_column(Float)
    avg_position: Mapped[float | None] = mapped_column(Float)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
