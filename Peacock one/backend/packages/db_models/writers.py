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


class Writer(Base, WorkspaceTenantMixin):
    __tablename__ = "writers"

    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320), index=True)
    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    bio: Mapped[str | None] = mapped_column(Text)
    seniority: Mapped[str | None] = mapped_column(String(64))
    availability: Mapped[str] = mapped_column(String(32), default="available", nullable=False)


class WriterSample(Base, TimestampMixin):
    __tablename__ = "writer_samples"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    organisation_id: Mapped[str] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    writer_id: Mapped[str] = mapped_column(
        ForeignKey("writers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str | None] = mapped_column(String(2048))
    excerpt: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    created_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class WriterProfile(Base, TimestampMixin):
    __tablename__ = "writer_profiles"
    __table_args__ = (UniqueConstraint("writer_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    organisation_id: Mapped[str] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    writer_id: Mapped[str] = mapped_column(
        ForeignKey("writers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tone: Mapped[str | None] = mapped_column(String(128))
    strengths: Mapped[str | None] = mapped_column(Text)
    languages: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    created_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class WriterSkill(Base, TimestampMixin):
    __tablename__ = "writer_skills"
    __table_args__ = (UniqueConstraint("writer_id", "skill_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    organisation_id: Mapped[str] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    writer_id: Mapped[str] = mapped_column(
        ForeignKey("writers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_code: Mapped[str] = mapped_column(String(64), nullable=False)
    proficiency: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    created_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class WriterIndustryExpertise(Base, TimestampMixin):
    __tablename__ = "writer_industry_expertise"
    __table_args__ = (UniqueConstraint("writer_id", "industry_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    organisation_id: Mapped[str] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    writer_id: Mapped[str] = mapped_column(
        ForeignKey("writers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    industry_code: Mapped[str] = mapped_column(String(64), nullable=False)
    years_experience: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    created_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class WriterPerformance(Base, WorkspaceTenantMixin):
    __tablename__ = "writer_performances"

    writer_id: Mapped[str] = mapped_column(
        ForeignKey("writers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    pieces_delivered: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_quality_score: Mapped[float | None] = mapped_column(Float)
    on_time_rate: Mapped[float | None] = mapped_column(Float)


class WriterRecommendation(Base, WorkspaceTenantMixin):
    __tablename__ = "writer_recommendations"

    writer_id: Mapped[str] = mapped_column(
        ForeignKey("writers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content_brief_id: Mapped[str | None] = mapped_column(
        ForeignKey("content_briefs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    recommendation_id: Mapped[str | None] = mapped_column(
        ForeignKey("recommendations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    fit_score: Mapped[float] = mapped_column(Float, nullable=False)


class WriterAssignment(Base, WorkspaceTenantMixin):
    __tablename__ = "writer_assignments"

    writer_id: Mapped[str] = mapped_column(
        ForeignKey("writers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content_brief_id: Mapped[str] = mapped_column(
        ForeignKey("content_briefs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
