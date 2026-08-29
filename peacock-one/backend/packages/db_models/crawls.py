from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db_models.base import Base, TimestampMixin, WorkspaceTenantMixin, new_uuid


class Crawl(Base, WorkspaceTenantMixin):
    __tablename__ = "crawls"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    trigger: Mapped[str] = mapped_column(String(64), default="manual", nullable=False)
    seed_url: Mapped[str | None] = mapped_column(String(2048))
    job_id: Mapped[str | None] = mapped_column(String(36), index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    page_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pages_discovered: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pages_crawled: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pages_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    issues_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    control_command: Mapped[str] = mapped_column(String(32), default="none", nullable=False)
    error_summary: Mapped[str | None] = mapped_column(Text)
    # Crawl knobs vary by engine version — justified JSONB
    config: Mapped[dict | None] = mapped_column(JSONB)

    pages: Mapped[list[CrawlPage]] = relationship(
        back_populates="crawl", cascade="all, delete-orphan", passive_deletes=True
    )
    issues: Mapped[list[CrawlIssue]] = relationship(
        back_populates="crawl", cascade="all, delete-orphan", passive_deletes=True
    )


class CrawlPage(Base, TimestampMixin):
    __tablename__ = "crawl_pages"
    __table_args__ = (UniqueConstraint("crawl_id", "url"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    organisation_id: Mapped[str] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    crawl_id: Mapped[str] = mapped_column(
        ForeignKey("crawls.id", ondelete="CASCADE"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    canonical_url: Mapped[str | None] = mapped_column(String(2048))
    status_code: Mapped[int | None] = mapped_column(Integer)
    title: Mapped[str | None] = mapped_column(String(1024))
    meta_description: Mapped[str | None] = mapped_column(String(2048))
    h1: Mapped[str | None] = mapped_column(Text)
    h2: Mapped[str | None] = mapped_column(Text)
    h3: Mapped[str | None] = mapped_column(Text)
    body_text: Mapped[str | None] = mapped_column(Text)
    word_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    internal_link_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    external_link_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Structured lists with stable shapes — justified JSONB for variable-length page facts
    internal_links: Mapped[list | None] = mapped_column(JSONB)
    external_links: Mapped[list | None] = mapped_column(JSONB)
    images: Mapped[list | None] = mapped_column(JSONB)
    schema_blocks: Mapped[list | None] = mapped_column(JSONB)
    robots: Mapped[str | None] = mapped_column(String(255))
    indexability: Mapped[str | None] = mapped_column(String(64), index=True)
    crawl_depth: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    content_type: Mapped[str | None] = mapped_column(String(128))
    language: Mapped[str | None] = mapped_column(String(32))
    is_js_heavy: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    redirect_chain: Mapped[list | None] = mapped_column(JSONB)
    fetch_mode: Mapped[str] = mapped_column(String(32), default="httpx", nullable=False)
    is_near_duplicate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    near_duplicate_of: Mapped[str | None] = mapped_column(String(2048))
    is_orphan_candidate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), default="fetched", nullable=False, index=True)
    created_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    crawl: Mapped[Crawl] = relationship(back_populates="pages")
    outbound_links: Mapped[list[CrawlLink]] = relationship(
        back_populates="from_page",
        foreign_keys="CrawlLink.from_page_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class CrawlLink(Base, TimestampMixin):
    __tablename__ = "crawl_links"
    __table_args__ = (UniqueConstraint("crawl_id", "from_page_id", "to_url"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    organisation_id: Mapped[str] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    crawl_id: Mapped[str] = mapped_column(
        ForeignKey("crawls.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_page_id: Mapped[str] = mapped_column(
        ForeignKey("crawl_pages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    to_page_id: Mapped[str | None] = mapped_column(
        ForeignKey("crawl_pages.id", ondelete="SET NULL"), nullable=True, index=True
    )
    to_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    link_type: Mapped[str] = mapped_column(String(32), default="anchor", nullable=False)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    created_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    from_page: Mapped[CrawlPage] = relationship(
        back_populates="outbound_links", foreign_keys=[from_page_id]
    )


class CrawlIssue(Base, TimestampMixin):
    __tablename__ = "crawl_issues"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    organisation_id: Mapped[str] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    crawl_id: Mapped[str] = mapped_column(
        ForeignKey("crawls.id", ondelete="CASCADE"), nullable=False, index=True
    )
    page_id: Mapped[str | None] = mapped_column(
        ForeignKey("crawl_pages.id", ondelete="SET NULL"), nullable=True, index=True
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="open", nullable=False, index=True)
    created_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    crawl: Mapped[Crawl] = relationship(back_populates="issues")
