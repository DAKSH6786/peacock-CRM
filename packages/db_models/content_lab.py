"""Peacock Content Lab — multi-opportunity content evaluation beyond keywords.

Scores proposed content on SEO/AEO/GEO/AI citation opportunity, business value,
information gain, content moat, and generative citability (proprietary estimate).
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


OPPORTUNITY_DIMENSIONS: tuple[str, ...] = (
    "seo_opportunity",
    "aeo_opportunity",
    "geo_opportunity",
    "ai_citation_opportunity",
    "business_value",
    "audience_relevance",
    "competitor_gap",
    "information_gain",
    "originality_opportunity",
    "topical_authority_impact",
    "conversion_potential",
    "backlink_potential",
    "entity_impact",
    "effort",  # lower effort = better for priority; stored as opportunity-adjusted
    "time_sensitivity",
)

# Signals that reduce Information Gain
INFO_GAIN_PENALTIES: tuple[str, ...] = (
    "generic_duplication",
    "near_identical_competitor_coverage",
    "common_definitions",
    "repeated_statistics",
    "commodity_advice",
)

# Signals that reward Information Gain
INFO_GAIN_REWARDS: tuple[str, ...] = (
    "original_data",
    "original_experiment",
    "new_comparison",
    "expert_opinion",
    "first_party_insight",
    "unique_framework",
    "new_synthesis",
    "fresh_statistics",
    "novel_example",
)

# Content formats with default moat priors (0–100)
MOAT_FORMAT_PRIORS: dict[str, int] = {
    "generic_listicle": 18,
    "expert_interview": 51,
    "original_dataset": 86,
    "proprietary_benchmark_study": 94,
}

CITABILITY_COMPONENTS: tuple[str, ...] = (
    "specificity",
    "evidence",
    "direct_answers",
    "original_information",
    "entity_clarity",
    "source_attribution",
    "freshness",
    "structured_information",
    "tables",
    "definitions",
    "comparisons",
)

CITABILITY_DISCLAIMER = (
    "Generative Citability Score is Peacock's proprietary estimate of whether a page "
    "is likely to offer useful quotable/retrievable information. It is not a guaranteed "
    "third-party ranking factor and does not claim access to proprietary AI ranking systems."
)


class ContentLabAnalysis(Base, WorkspaceTenantMixin):
    """Batch or single Content Lab evaluation run."""

    __tablename__ = "content_lab_analyses"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_brand: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    topic_cluster: Mapped[str | None] = mapped_column(String(255), index=True)
    analysis_status: Mapped[str] = mapped_column(
        String(32), default="draft", nullable=False, index=True
    )
    methodology: Mapped[str] = mapped_column(
        String(64), default="content_lab_multi_opportunity", nullable=False
    )
    proposal_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    citability_is_proprietary_estimate: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    citability_disclaimer: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    proposals: Mapped[list[ClContentProposal]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True
    )


class ClContentProposal(Base, WorkspaceTenantMixin):
    """One proposed piece of content evaluated by Content Lab."""

    __tablename__ = "cl_content_proposals"
    __table_args__ = (UniqueConstraint("analysis_id", "slug"),)

    analysis_id: Mapped[str] = mapped_column(
        ForeignKey("content_lab_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    content_format: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    angle: Mapped[str | None] = mapped_column(Text)
    target_url: Mapped[str | None] = mapped_column(String(2048))

    # Composite priority 0–100
    lab_priority_score: Mapped[float] = mapped_column(Float, nullable=False)

    # Opportunity dimensions 0–100 (effort inverted for priority use)
    seo_opportunity: Mapped[float] = mapped_column(Float, nullable=False)
    aeo_opportunity: Mapped[float] = mapped_column(Float, nullable=False)
    geo_opportunity: Mapped[float] = mapped_column(Float, nullable=False)
    ai_citation_opportunity: Mapped[float] = mapped_column(Float, nullable=False)
    business_value: Mapped[float] = mapped_column(Float, nullable=False)
    audience_relevance: Mapped[float] = mapped_column(Float, nullable=False)
    competitor_gap: Mapped[float] = mapped_column(Float, nullable=False)
    information_gain: Mapped[float] = mapped_column(Float, nullable=False)
    originality_opportunity: Mapped[float] = mapped_column(Float, nullable=False)
    topical_authority_impact: Mapped[float] = mapped_column(Float, nullable=False)
    conversion_potential: Mapped[float] = mapped_column(Float, nullable=False)
    backlink_potential: Mapped[float] = mapped_column(Float, nullable=False)
    entity_impact: Mapped[float] = mapped_column(Float, nullable=False)
    effort: Mapped[float] = mapped_column(Float, nullable=False)  # 0=easy, 100=hard
    time_sensitivity: Mapped[float] = mapped_column(Float, nullable=False)

    # Signature proprietary scores
    information_gain_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0–100
    content_moat_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0–100
    generative_citability_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0–100

    information_gain_breakdown: Mapped[str | None] = mapped_column(Text)
    moat_rationale: Mapped[str | None] = mapped_column(Text)
    citability_breakdown: Mapped[str | None] = mapped_column(Text)
    recommendation_summary: Mapped[str] = mapped_column(Text, nullable=False)

    analysis: Mapped[ContentLabAnalysis] = relationship(back_populates="proposals")
    info_gain_signals: Mapped[list[ClInfoGainSignal]] = relationship(
        back_populates="proposal", cascade="all, delete-orphan", passive_deletes=True
    )
    citability_components: Mapped[list[ClCitabilityComponent]] = relationship(
        back_populates="proposal", cascade="all, delete-orphan", passive_deletes=True
    )


class ClInfoGainSignal(Base, WorkspaceTenantMixin):
    """Detected penalty or reward contributing to Information Gain Score."""

    __tablename__ = "cl_info_gain_signals"

    proposal_id: Mapped[str] = mapped_column(
        ForeignKey("cl_content_proposals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    signal_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    polarity: Mapped[str] = mapped_column(String(16), nullable=False)  # penalty|reward
    strength: Mapped[float] = mapped_column(Float, nullable=False)
    evidence: Mapped[str] = mapped_column(Text, nullable=False)

    proposal: Mapped[ClContentProposal] = relationship(back_populates="info_gain_signals")


class ClCitabilityComponent(Base, WorkspaceTenantMixin):
    """Explainable Generative Citability component (proprietary estimate)."""

    __tablename__ = "cl_citability_components"
    __table_args__ = (UniqueConstraint("proposal_id", "component_code"),)

    proposal_id: Mapped[str] = mapped_column(
        ForeignKey("cl_content_proposals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    component_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)

    proposal: Mapped[ClContentProposal] = relationship(back_populates="citability_components")
