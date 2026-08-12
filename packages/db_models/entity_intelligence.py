"""Peacock Entity Intelligence — graph of brand/entity relationships.

Tracks associations among brands, people, products, concepts, competitors,
pages, sources, and more. Powers Entity Association Strength and Entity Gap.
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


ENTITY_TYPES: tuple[str, ...] = (
    "brand",
    "founder",
    "executive",
    "product",
    "service",
    "person",
    "industry",
    "problem",
    "location",
    "competitor",
    "feature",
    "publication",
    "concept",
    "customer",
    "topic",
    "page",
    "source",
)

ASSOCIATION_COMPONENTS: tuple[str, ...] = (
    "co_occurrence",
    "semantic_proximity",
    "ownership_signal",
    "citation_linkage",
    "topical_centrality",
    "recency",
    "cross_source_consistency",
)

STRATEGY_ACTIONS: tuple[str, ...] = (
    "strengthen_entity_ownership",
    "publish_pillar_content",
    "earn_third_party_association",
    "clarify_product_positioning",
    "executive_thought_leadership",
    "close_feature_narrative_gap",
    "localise_entity_presence",
    "competitor_differentiation",
)


class EntityIntelligenceAnalysis(Base, WorkspaceTenantMixin):
    """Analysis run that builds / scores an Entity Intelligence graph."""

    __tablename__ = "entity_intelligence_analyses"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_brand: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    industry: Mapped[str | None] = mapped_column(String(255), index=True)
    analysis_status: Mapped[str] = mapped_column(
        String(32), default="draft", nullable=False, index=True
    )
    methodology: Mapped[str] = mapped_column(
        String(64), default="entity_association_multi_signal", nullable=False
    )
    entity_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    association_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    gap_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    strategy_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    entities: Mapped[list[EiEntity]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True
    )
    associations: Mapped[list[EiAssociation]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True
    )
    gaps: Mapped[list[EiEntityGap]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True
    )
    strategies: Mapped[list[EiStrategy]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True
    )


class EiEntity(Base, WorkspaceTenantMixin):
    """Node in the Entity Intelligence graph."""

    __tablename__ = "ei_entities"
    __table_args__ = (UniqueConstraint("analysis_id", "canonical_name", "entity_type"),)

    analysis_id: Mapped[str] = mapped_column(
        ForeignKey("entity_intelligence_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    canonical_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    is_client: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_competitor: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    aliases: Mapped[str | None] = mapped_column(Text)  # comma-separated
    description: Mapped[str | None] = mapped_column(Text)
    ownership_brand: Mapped[str | None] = mapped_column(String(255), index=True)

    analysis: Mapped[EntityIntelligenceAnalysis] = relationship(back_populates="entities")


class EiAssociation(Base, WorkspaceTenantMixin):
    """Directed/undirected association with Entity Association Strength."""

    __tablename__ = "ei_associations"
    __table_args__ = (
        UniqueConstraint("analysis_id", "source_entity_name", "target_entity_name"),
    )

    analysis_id: Mapped[str] = mapped_column(
        ForeignKey("entity_intelligence_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_entity_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    target_entity_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    target_entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    is_client_owned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_competitor_owned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Primary metric 0–1
    association_strength: Mapped[float] = mapped_column(Float, nullable=False)

    # Explainable components 0–1
    co_occurrence: Mapped[float] = mapped_column(Float, nullable=False)
    semantic_proximity: Mapped[float] = mapped_column(Float, nullable=False)
    ownership_signal: Mapped[float] = mapped_column(Float, nullable=False)
    citation_linkage: Mapped[float] = mapped_column(Float, nullable=False)
    topical_centrality: Mapped[float] = mapped_column(Float, nullable=False)
    recency: Mapped[float] = mapped_column(Float, nullable=False)
    cross_source_consistency: Mapped[float] = mapped_column(Float, nullable=False)

    observation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    component_explanations: Mapped[str | None] = mapped_column(Text)

    analysis: Mapped[EntityIntelligenceAnalysis] = relationship(back_populates="associations")


class EiEntityGap(Base, WorkspaceTenantMixin):
    """Entity Gap: client vs competitor association to a target concept."""

    __tablename__ = "ei_entity_gaps"
    __table_args__ = (UniqueConstraint("analysis_id", "target_concept"),)

    analysis_id: Mapped[str] = mapped_column(
        ForeignKey("entity_intelligence_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_concept: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    target_entity_type: Mapped[str] = mapped_column(
        String(64), default="concept", nullable=False
    )
    client_brand: Mapped[str] = mapped_column(String(255), nullable=False)
    client_association: Mapped[float] = mapped_column(Float, nullable=False)
    leading_competitor_name: Mapped[str | None] = mapped_column(String(255))
    leading_competitor_association: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    competitor_associations_json: Mapped[str | None] = mapped_column(Text)
    gap_size: Mapped[float] = mapped_column(Float, nullable=False)
    severity: Mapped[str] = mapped_column(String(16), default="medium", nullable=False, index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)

    analysis: Mapped[EntityIntelligenceAnalysis] = relationship(back_populates="gaps")


class EiStrategy(Base, WorkspaceTenantMixin):
    """Strategy generated from Entity Gaps / weak associations."""

    __tablename__ = "ei_strategies"

    analysis_id: Mapped[str] = mapped_column(
        ForeignKey("entity_intelligence_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    gap_id: Mapped[str | None] = mapped_column(
        ForeignKey("ei_entity_gaps.id", ondelete="SET NULL"), nullable=True, index=True
    )
    target_concept: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(16), default="medium", nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_moves: Mapped[str] = mapped_column(Text, nullable=False)
    expected_association_lift: Mapped[float | None] = mapped_column(Float)

    analysis: Mapped[EntityIntelligenceAnalysis] = relationship(back_populates="strategies")
