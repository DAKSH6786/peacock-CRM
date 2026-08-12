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


class Topic(Base, WorkspaceTenantMixin):
    __tablename__ = "topics"
    __table_args__ = (UniqueConstraint("workspace_id", "slug"),)

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)


class TopicCluster(Base, WorkspaceTenantMixin):
    __tablename__ = "topic_clusters"
    __table_args__ = (UniqueConstraint("workspace_id", "name"),)

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    hub_topic_id: Mapped[str | None] = mapped_column(
        ForeignKey("topics.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)


class TopicRecommendation(Base, WorkspaceTenantMixin):
    __tablename__ = "topic_recommendations"

    topic_id: Mapped[str] = mapped_column(
        ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recommendation_id: Mapped[str | None] = mapped_column(
        ForeignKey("recommendations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(16), default="medium", nullable=False)


class Keyword(Base, WorkspaceTenantMixin):
    __tablename__ = "keywords"
    __table_args__ = (UniqueConstraint("workspace_id", "phrase", "locale"),)

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    phrase: Mapped[str] = mapped_column(String(512), nullable=False)
    locale: Mapped[str] = mapped_column(String(32), default="en-US", nullable=False)
    intent: Mapped[str | None] = mapped_column(String(64))
    volume: Mapped[int | None] = mapped_column(Integer)
    difficulty: Mapped[float | None] = mapped_column(Float)
    priority: Mapped[str] = mapped_column(String(16), default="medium", nullable=False)


class KeywordCluster(Base, WorkspaceTenantMixin):
    __tablename__ = "keyword_clusters"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    topic_cluster_id: Mapped[str | None] = mapped_column(
        ForeignKey("topic_clusters.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    seed_keyword_id: Mapped[str | None] = mapped_column(
        ForeignKey("keywords.id", ondelete="SET NULL"), nullable=True, index=True
    )


class ContentBrief(Base, WorkspaceTenantMixin):
    __tablename__ = "content_briefs"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    topic_id: Mapped[str | None] = mapped_column(
        ForeignKey("topics.id", ondelete="SET NULL"), nullable=True, index=True
    )
    primary_keyword_id: Mapped[str | None] = mapped_column(
        ForeignKey("keywords.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    audience: Mapped[str | None] = mapped_column(String(255))
    outline: Mapped[str | None] = mapped_column(Text)
    target_word_count: Mapped[int | None] = mapped_column(Integer)


class ContentRecommendation(Base, WorkspaceTenantMixin):
    __tablename__ = "content_recommendations"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content_brief_id: Mapped[str | None] = mapped_column(
        ForeignKey("content_briefs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    recommendation_id: Mapped[str | None] = mapped_column(
        ForeignKey("recommendations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(16), default="medium", nullable=False)


class BacklinkOpportunity(Base, WorkspaceTenantMixin):
    __tablename__ = "backlink_opportunities"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    target_url: Mapped[str | None] = mapped_column(String(2048))
    opportunity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    authority_score: Mapped[float | None] = mapped_column(Float)
    notes: Mapped[str | None] = mapped_column(Text)


class CitationSource(Base, WorkspaceTenantMixin):
    __tablename__ = "citation_sources"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    source_domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    trust_score: Mapped[float | None] = mapped_column(Float)
    notes: Mapped[str | None] = mapped_column(Text)
