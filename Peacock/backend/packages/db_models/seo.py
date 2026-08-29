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


class SEOScore(Base, WorkspaceTenantMixin):
    __tablename__ = "seo_scores"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    audit_id: Mapped[str | None] = mapped_column(
        ForeignKey("audits.id", ondelete="SET NULL"), nullable=True, index=True
    )
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    technical_score: Mapped[float | None] = mapped_column(Float)
    onpage_score: Mapped[float | None] = mapped_column(Float)
    content_score: Mapped[float | None] = mapped_column(Float)
    authority_score: Mapped[float | None] = mapped_column(Float)
    scored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class TechnicalSEOResult(Base, WorkspaceTenantMixin):
    __tablename__ = "technical_seo_results"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    audit_id: Mapped[str | None] = mapped_column(
        ForeignKey("audits.id", ondelete="SET NULL"), nullable=True, index=True
    )
    crawl_id: Mapped[str | None] = mapped_column(
        ForeignKey("crawls.id", ondelete="SET NULL"), nullable=True, index=True
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    indexability_score: Mapped[float | None] = mapped_column(Float)
    https_ok: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    robots_ok: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sitemap_ok: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    canonical_issues: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)


class OnPageSEOResult(Base, WorkspaceTenantMixin):
    __tablename__ = "onpage_seo_results"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    audit_id: Mapped[str | None] = mapped_column(
        ForeignKey("audits.id", ondelete="SET NULL"), nullable=True, index=True
    )
    page_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    title_ok: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    meta_ok: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    heading_ok: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    thin_content: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class InternalLinkResult(Base, WorkspaceTenantMixin):
    __tablename__ = "internal_link_results"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    audit_id: Mapped[str | None] = mapped_column(
        ForeignKey("audits.id", ondelete="SET NULL"), nullable=True, index=True
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    orphan_pages: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    deep_pages: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    broken_internal_links: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_click_depth: Mapped[float | None] = mapped_column(Float)


class SchemaResult(Base, WorkspaceTenantMixin):
    __tablename__ = "schema_results"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    audit_id: Mapped[str | None] = mapped_column(
        ForeignKey("audits.id", ondelete="SET NULL"), nullable=True, index=True
    )
    page_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    schema_types: Mapped[str | None] = mapped_column(Text)  # comma-separated known types
    has_organization: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_faq: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_howto: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    validation_errors: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class PerformanceResult(Base, WorkspaceTenantMixin):
    __tablename__ = "performance_results"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    audit_id: Mapped[str | None] = mapped_column(
        ForeignKey("audits.id", ondelete="SET NULL"), nullable=True, index=True
    )
    page_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    lcp_ms: Mapped[float | None] = mapped_column(Float)
    cls: Mapped[float | None] = mapped_column(Float)
    inp_ms: Mapped[float | None] = mapped_column(Float)
    ttfb_ms: Mapped[float | None] = mapped_column(Float)
