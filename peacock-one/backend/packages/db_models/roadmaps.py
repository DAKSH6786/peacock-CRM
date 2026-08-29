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


class Roadmap(Base, WorkspaceTenantMixin):
    __tablename__ = "roadmaps"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    horizon_days: Mapped[int] = mapped_column(Integer, default=90, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    starts_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ends_on: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    months: Mapped[list[RoadmapMonth]] = relationship(
        back_populates="roadmap", cascade="all, delete-orphan", passive_deletes=True
    )


class RoadmapMonth(Base, TimestampMixin):
    __tablename__ = "roadmap_months"
    __table_args__ = (UniqueConstraint("roadmap_id", "month_index"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    organisation_id: Mapped[str] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    roadmap_id: Mapped[str] = mapped_column(
        ForeignKey("roadmaps.id", ondelete="CASCADE"), nullable=False, index=True
    )
    month_index: Mapped[int] = mapped_column(Integer, nullable=False)
    theme: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="planned", nullable=False, index=True)
    created_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    roadmap: Mapped[Roadmap] = relationship(back_populates="months")
    weeks: Mapped[list[RoadmapWeek]] = relationship(
        back_populates="month", cascade="all, delete-orphan", passive_deletes=True
    )


class RoadmapWeek(Base, TimestampMixin):
    __tablename__ = "roadmap_weeks"
    __table_args__ = (UniqueConstraint("month_id", "week_index"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    organisation_id: Mapped[str] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    month_id: Mapped[str] = mapped_column(
        ForeignKey("roadmap_months.id", ondelete="CASCADE"), nullable=False, index=True
    )
    week_index: Mapped[int] = mapped_column(Integer, nullable=False)
    theme: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="planned", nullable=False, index=True)
    created_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    month: Mapped[RoadmapMonth] = relationship(back_populates="weeks")
    tasks: Mapped[list[RoadmapTask]] = relationship(
        back_populates="week", cascade="all, delete-orphan", passive_deletes=True
    )


class RoadmapTask(Base, TimestampMixin):
    __tablename__ = "roadmap_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    organisation_id: Mapped[str] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    week_id: Mapped[str] = mapped_column(
        ForeignKey("roadmap_weeks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    owner_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    priority: Mapped[str] = mapped_column(String(16), default="medium", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="todo", nullable=False, index=True)
    created_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    week: Mapped[RoadmapWeek] = relationship(back_populates="tasks")


class RoadmapRecommendation(Base, WorkspaceTenantMixin):
    __tablename__ = "roadmap_recommendations"

    roadmap_id: Mapped[str] = mapped_column(
        ForeignKey("roadmaps.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recommendation_id: Mapped[str | None] = mapped_column(
        ForeignKey("recommendations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(16), default="medium", nullable=False)
