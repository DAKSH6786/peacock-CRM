"""Peacock Citation Graph — generative citation pathways and influence.

Chain:
  AI Engine → Prompt → Answer → Citation → Domain → Page → Entity → Topic

Aggregated across observations to discover hubs, pathways, source classes,
Citation Influence Score, and ethical Source Opportunities.
"""

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

from db_models.base import Base, WorkspaceTenantMixin


# Pathway node kinds (ordered)
PATHWAY_NODE_KINDS: tuple[str, ...] = (
    "engine",
    "prompt",
    "answer",
    "citation",
    "domain",
    "page",
    "entity",
    "topic",
)

SOURCE_CLASSES: tuple[str, ...] = (
    "competitor_owned",
    "independent",
    "news",
    "forum",
    "review",
    "government",
    "academic",
    "industry_publication",
    "unknown",
)

CIS_COMPONENTS: tuple[str, ...] = (
    "citation_frequency",
    "cross_engine_citation",
    "topic_coverage",
    "prominence",
    "freshness",
    "authority_proxy",
    "brand_association",
    "citation_diversity",
)

OPPORTUNITY_TYPES: tuple[str, ...] = (
    "pr_opportunity",
    "expert_contribution",
    "original_research",
    "source_partnership",
    "listing_correction",
    "review_improvement",
    "content_relationship",
)

# Never recommend manipulative spam / deceptive tactics
FORBIDDEN_TACTICS: tuple[str, ...] = (
    "spam",
    "link_farm",
    "doorway_pages",
    "fake_reviews",
    "paid_undisclosed_placement",
    "content_scraping",
    "astroturfing",
    "cloaking",
)


class CitationGraphAnalysis(Base, WorkspaceTenantMixin):
    """Analysis run that builds a Citation Graph for a topic cluster."""

    __tablename__ = "citation_graph_analyses"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    topic_cluster: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    client_brand: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    analysis_status: Mapped[str] = mapped_column(
        String(32), default="draft", nullable=False, index=True
    )
    observation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    citation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    domain_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pathway_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    opportunity_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    methodology: Mapped[str] = mapped_column(
        String(64), default="citation_influence_multi_component", nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text)

    observations: Mapped[list[CgObservation]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True
    )
    pathways: Mapped[list[CgPathway]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True
    )
    domain_scores: Mapped[list[CgDomainScore]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True
    )
    opportunities: Mapped[list[CgSourceOpportunity]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True
    )


class CgObservation(Base, WorkspaceTenantMixin):
    """One generative answer observation feeding the citation graph.

    Anchors: AI Engine → Prompt → Answer.
    """

    __tablename__ = "cg_observations"

    analysis_id: Mapped[str] = mapped_column(
        ForeignKey("citation_graph_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    engine_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    answer_excerpt: Mapped[str | None] = mapped_column(Text)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    model_code: Mapped[str | None] = mapped_column(String(128))
    topic_label: Mapped[str | None] = mapped_column(String(255), index=True)
    # Optional links into existing observation systems
    visibility_probe_observation_id: Mapped[str | None] = mapped_column(
        ForeignKey("visibility_probe_observations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    ai_query_run_id: Mapped[str | None] = mapped_column(
        ForeignKey("ai_query_runs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    citation_observation_id: Mapped[str | None] = mapped_column(
        ForeignKey("citation_observations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    analysis: Mapped[CitationGraphAnalysis] = relationship(back_populates="observations")
    citations: Mapped[list[CgCitation]] = relationship(
        back_populates="observation", cascade="all, delete-orphan", passive_deletes=True
    )
    entities: Mapped[list[CgEntityMention]] = relationship(
        back_populates="observation", cascade="all, delete-orphan", passive_deletes=True
    )


class CgCitation(Base, WorkspaceTenantMixin):
    """Citation → Domain → Page node for one observation."""

    __tablename__ = "cg_citations"

    observation_id: Mapped[str] = mapped_column(
        ForeignKey("cg_observations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    cited_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    cited_domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    page_path: Mapped[str | None] = mapped_column(String(2048))
    source_class: Mapped[str] = mapped_column(
        String(64), default="unknown", nullable=False, index=True
    )
    is_competitor_owned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_client_owned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    prominence: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    # Days since content/publish signal when known; null = unknown
    freshness_days: Mapped[int | None] = mapped_column(Integer)
    authority_proxy: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    position_in_answer: Mapped[int | None] = mapped_column(Integer)

    observation: Mapped[CgObservation] = relationship(back_populates="citations")


class CgEntityMention(Base, WorkspaceTenantMixin):
    """Entity mentioned in an answer (client, competitor, or other)."""

    __tablename__ = "cg_entity_mentions"

    observation_id: Mapped[str] = mapped_column(
        ForeignKey("cg_observations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entity_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    is_client: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_competitor: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mentioned: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    position_hint: Mapped[int | None] = mapped_column(Integer)

    observation: Mapped[CgObservation] = relationship(back_populates="entities")


class CgPathway(Base, WorkspaceTenantMixin):
    """Materialised pathway:
    Engine → Prompt → Answer → Citation → Domain → Page → Entity → Topic
    """

    __tablename__ = "cg_pathways"

    analysis_id: Mapped[str] = mapped_column(
        ForeignKey("citation_graph_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    observation_id: Mapped[str] = mapped_column(
        ForeignKey("cg_observations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    citation_id: Mapped[str] = mapped_column(
        ForeignKey("cg_citations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    engine_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    prompt_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    answer_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    cited_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    cited_domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    page_path: Mapped[str | None] = mapped_column(String(2048))
    entity_name: Mapped[str | None] = mapped_column(String(255), index=True)
    topic_label: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_class: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    pathway_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    analysis: Mapped[CitationGraphAnalysis] = relationship(back_populates="pathways")


class CgDomainScore(Base, WorkspaceTenantMixin):
    """Aggregated Citation Influence Score for a domain within a topic cluster."""

    __tablename__ = "cg_domain_scores"
    __table_args__ = (UniqueConstraint("analysis_id", "cited_domain"),)

    analysis_id: Mapped[str] = mapped_column(
        ForeignKey("citation_graph_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cited_domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_class: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    is_citation_hub: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_competitor_owned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_client_owned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Primary proprietary metric (0–100)
    citation_influence_score: Mapped[float] = mapped_column(Float, nullable=False)

    # Explainable components (0–1)
    citation_frequency: Mapped[float] = mapped_column(Float, nullable=False)
    cross_engine_citation: Mapped[float] = mapped_column(Float, nullable=False)
    topic_coverage: Mapped[float] = mapped_column(Float, nullable=False)
    prominence: Mapped[float] = mapped_column(Float, nullable=False)
    freshness: Mapped[float] = mapped_column(Float, nullable=False)
    authority_proxy: Mapped[float] = mapped_column(Float, nullable=False)
    brand_association: Mapped[float] = mapped_column(Float, nullable=False)
    citation_diversity: Mapped[float] = mapped_column(Float, nullable=False)

    citation_count: Mapped[int] = mapped_column(Integer, nullable=False)
    engine_count: Mapped[int] = mapped_column(Integer, nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False)
    observation_share: Mapped[float] = mapped_column(Float, nullable=False)
    client_mention_rate: Mapped[float] = mapped_column(Float, nullable=False)
    competitor_mention_rate: Mapped[float] = mapped_column(Float, nullable=False)
    component_explanations: Mapped[str | None] = mapped_column(Text)

    analysis: Mapped[CitationGraphAnalysis] = relationship(back_populates="domain_scores")


class CgSourceOpportunity(Base, WorkspaceTenantMixin):
    """Source Opportunity Engine finding — ethical recommendations only."""

    __tablename__ = "cg_source_opportunities"

    analysis_id: Mapped[str] = mapped_column(
        ForeignKey("citation_graph_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cited_domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_class: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    opportunity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(16), default="medium", nullable=False, index=True)

    # Narrative stats for the topic cluster
    domain_answer_influence_pct: Mapped[float] = mapped_column(Float, nullable=False)
    client_mention_pct: Mapped[float] = mapped_column(Float, nullable=False)
    top_competitor_name: Mapped[str | None] = mapped_column(String(255))
    top_competitor_mention_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_actions: Mapped[str] = mapped_column(Text, nullable=False)
    manipulative_spam_rejected: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    forbidden_tactics_note: Mapped[str | None] = mapped_column(Text)

    analysis: Mapped[CitationGraphAnalysis] = relationship(back_populates="opportunities")
