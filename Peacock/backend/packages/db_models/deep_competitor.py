"""Deep Competitor Intelligence — multi-category discovery, deltas, reverse content.

A site may be a strong SEO / AI visibility competitor without being a direct
business competitor. Peacock discovers competitors dynamically and recommends
**differentiated** strategies — never copying competitor content.
"""

from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db_models.base import Base, WorkspaceTenantMixin


COMPETITOR_CATEGORIES: tuple[str, ...] = (
    "business_competitor",
    "search_competitor",
    "content_competitor",
    "ai_visibility_competitor",
    "citation_competitor",
    "entity_competitor",
    "serp_competitor",
)

DISCOVERY_SIGNALS: tuple[str, ...] = (
    "serp_overlap",
    "keyword_overlap",
    "topic_overlap",
    "ai_mention_overlap",
    "citation_overlap",
    "entity_similarity",
    "product_similarity",
)

CONTENT_COMPARE_DIMENSIONS: tuple[str, ...] = (
    "topical_completeness",
    "entities",
    "structure",
    "freshness",
    "original_data",
    "references",
    "schema",
    "internal_linking",
    "backlinks",
    "citations",
    "author_signals",
    "content_type",
    "intent_satisfaction",
    "page_ux",
)

# Explicitly forbidden recommendation modes
FORBIDDEN_RECOMMENDATION_MODES: tuple[str, ...] = (
    "copy_competitor_content",
    "paraphrase_competitor_page",
    "scrape_and_republish",
    "thin_rewrite_of_competitor",
)


class DeepCompetitorAnalysis(Base, WorkspaceTenantMixin):
    """Deep competitor intelligence analysis for a client website."""

    __tablename__ = "deep_competitor_analyses"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_brand: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    client_domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    topic_cluster: Mapped[str | None] = mapped_column(String(255), index=True)
    analysis_status: Mapped[str] = mapped_column(
        String(32), default="draft", nullable=False, index=True
    )
    methodology: Mapped[str] = mapped_column(
        String(64), default="deep_competitor_multi_category", nullable=False
    )
    copy_competitor_content_rejected: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    discovered_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    delta_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    content_diff_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    strategy_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    competitors: Mapped[list[DcCompetitorProfile]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True
    )
    deltas: Mapped[list[DcCompetitiveDelta]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True
    )
    content_diffs: Mapped[list[DcContentDiff]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True
    )
    strategies: Mapped[list[DcDifferentiatedStrategy]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True
    )


class DcCompetitorProfile(Base, WorkspaceTenantMixin):
    """Discovered or seeded competitor with multi-category membership."""

    __tablename__ = "dc_competitor_profiles"
    __table_args__ = (UniqueConstraint("analysis_id", "domain"),)

    analysis_id: Mapped[str] = mapped_column(
        ForeignKey("deep_competitor_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    # Comma-separated category codes
    categories: Mapped[str] = mapped_column(String(512), nullable=False)
    discovery_method: Mapped[str] = mapped_column(
        String(64), default="automatic", nullable=False, index=True
    )
    # Discovery signal strengths 0–1
    serp_overlap: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    keyword_overlap: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    topic_overlap: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    ai_mention_overlap: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    citation_overlap: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    entity_similarity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    product_similarity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    overall_rivalry_score: Mapped[float] = mapped_column(Float, nullable=False)
    is_direct_business_competitor: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    discovery_rationale: Mapped[str] = mapped_column(Text, nullable=False)
    # Optional link to legacy competitors table
    legacy_competitor_id: Mapped[str | None] = mapped_column(
        ForeignKey("competitors.id", ondelete="SET NULL"), nullable=True, index=True
    )

    analysis: Mapped[DeepCompetitorAnalysis] = relationship(back_populates="competitors")


class DcCompetitiveDelta(Base, WorkspaceTenantMixin):
    """Competitive Delta Engine output for one rival."""

    __tablename__ = "dc_competitive_deltas"
    __table_args__ = (UniqueConstraint("analysis_id", "competitor_domain", "dimension"),)

    analysis_id: Mapped[str] = mapped_column(
        ForeignKey("deep_competitor_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    competitor_domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    competitor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    dimension: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    where_stronger: Mapped[str] = mapped_column(Text, nullable=False)
    why_stronger: Mapped[str] = mapped_column(Text, nullable=False)
    gap_difficulty: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    gap_difficulty_score: Mapped[float] = mapped_column(Float, nullable=False)
    how_to_close: Mapped[str] = mapped_column(Text, nullable=False)
    how_to_leapfrog: Mapped[str] = mapped_column(Text, nullable=False)
    client_score: Mapped[float] = mapped_column(Float, nullable=False)
    competitor_score: Mapped[float] = mapped_column(Float, nullable=False)
    delta: Mapped[float] = mapped_column(Float, nullable=False)
    evidence: Mapped[str | None] = mapped_column(Text)

    analysis: Mapped[DeepCompetitorAnalysis] = relationship(back_populates="deltas")


class DcContentDiff(Base, WorkspaceTenantMixin):
    """Evidence-backed reverse engineering of winning competitor content."""

    __tablename__ = "dc_content_diffs"

    analysis_id: Mapped[str] = mapped_column(
        ForeignKey("deep_competitor_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    competitor_domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    competitor_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    client_url: Mapped[str | None] = mapped_column(String(2048))
    dimension: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    competitor_advantage: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    client_score: Mapped[float] = mapped_column(Float, nullable=False)
    competitor_score: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_summary: Mapped[str] = mapped_column(Text, nullable=False)
    differentiated_recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    copy_rejected: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    analysis: Mapped[DeepCompetitorAnalysis] = relationship(back_populates="content_diffs")


class DcDifferentiatedStrategy(Base, WorkspaceTenantMixin):
    """Strategy that leapfrogs rivals without copying their content."""

    __tablename__ = "dc_differentiated_strategies"

    analysis_id: Mapped[str] = mapped_column(
        ForeignKey("deep_competitor_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    competitor_domain: Mapped[str | None] = mapped_column(String(255), index=True)
    priority: Mapped[str] = mapped_column(String(16), default="medium", nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    differentiated_moves: Mapped[str] = mapped_column(Text, nullable=False)
    leapfrog_angle: Mapped[str] = mapped_column(Text, nullable=False)
    copy_competitor_content_rejected: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    forbidden_modes_note: Mapped[str] = mapped_column(Text, nullable=False)

    analysis: Mapped[DeepCompetitorAnalysis] = relationship(back_populates="strategies")
