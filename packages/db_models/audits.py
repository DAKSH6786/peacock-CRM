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


class Audit(Base, WorkspaceTenantMixin):
    __tablename__ = "audits"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    crawl_id: Mapped[str | None] = mapped_column(
        ForeignKey("crawls.id", ondelete="SET NULL"), nullable=True, index=True
    )
    audit_type: Mapped[str] = mapped_column(String(64), default="full", nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    overall_score: Mapped[float | None] = mapped_column(Float)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    sections: Mapped[list[AuditSection]] = relationship(
        back_populates="audit", cascade="all, delete-orphan", passive_deletes=True
    )
    issues: Mapped[list[AuditIssue]] = relationship(
        back_populates="audit", cascade="all, delete-orphan", passive_deletes=True
    )
    recommendations: Mapped[list[AuditRecommendation]] = relationship(
        back_populates="audit", cascade="all, delete-orphan", passive_deletes=True
    )


class AuditSection(Base, TimestampMixin):
    __tablename__ = "audit_sections"
    __table_args__ = (UniqueConstraint("audit_id", "code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    organisation_id: Mapped[str] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    audit_id: Mapped[str] = mapped_column(
        ForeignKey("audits.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    score: Mapped[float | None] = mapped_column(Float)
    summary: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="complete", nullable=False, index=True)
    created_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    audit: Mapped[Audit] = relationship(back_populates="sections")
    metrics: Mapped[list[AuditMetric]] = relationship(
        back_populates="section", cascade="all, delete-orphan", passive_deletes=True
    )


class AuditMetric(Base, TimestampMixin):
    __tablename__ = "audit_metrics"
    __table_args__ = (UniqueConstraint("section_id", "metric_key"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    organisation_id: Mapped[str] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    section_id: Mapped[str] = mapped_column(
        ForeignKey("audit_sections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    metric_key: Mapped[str] = mapped_column(String(128), nullable=False)
    metric_value: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(32))
    label: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    created_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    section: Mapped[AuditSection] = relationship(back_populates="metrics")


class AuditIssue(Base, TimestampMixin):
    __tablename__ = "audit_issues"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    organisation_id: Mapped[str] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    audit_id: Mapped[str] = mapped_column(
        ForeignKey("audits.id", ondelete="CASCADE"), nullable=False, index=True
    )
    section_id: Mapped[str | None] = mapped_column(
        ForeignKey("audit_sections.id", ondelete="SET NULL"), nullable=True, index=True
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    evidence_url: Mapped[str | None] = mapped_column(String(2048))
    status: Mapped[str] = mapped_column(String(32), default="open", nullable=False, index=True)
    created_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    audit: Mapped[Audit] = relationship(back_populates="issues")


class AuditRecommendation(Base, TimestampMixin):
    __tablename__ = "audit_recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    organisation_id: Mapped[str] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    audit_id: Mapped[str] = mapped_column(
        ForeignKey("audits.id", ondelete="CASCADE"), nullable=False, index=True
    )
    issue_id: Mapped[str | None] = mapped_column(
        ForeignKey("audit_issues.id", ondelete="SET NULL"), nullable=True, index=True
    )
    recommendation_id: Mapped[str | None] = mapped_column(
        ForeignKey("recommendations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(16), default="medium", nullable=False)
    impact_score: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    effort_score: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="proposed", nullable=False, index=True)
    created_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    audit: Mapped[Audit] = relationship(back_populates="recommendations")
