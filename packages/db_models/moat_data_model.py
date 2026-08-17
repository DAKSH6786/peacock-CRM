"""Peacock Moat Data Model — accumulates proprietary intelligence pathways.

This dataset is Peacock One's long-term competitive advantage: closed-loop
pathways such as recommendation→outcome, writer→topic→outcome,
citation_source→AI visibility, content_structure→citation result,
industry→GEO strategy→result, entity_gap→intervention→result, and
competitor_movement→response→outcome.

Domain engines remain systems of record; moat tables unify pathway memory.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
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


PATHWAY_KINDS: tuple[str, ...] = (
    "recommendation_outcome",
    "writer_topic_outcome",
    "citation_source_visibility",
    "content_structure_citation",
    "industry_geo_strategy_result",
    "entity_gap_intervention_result",
    "competitor_movement_response_outcome",
)

PATHWAY_LABELS: dict[str, str] = {
    "recommendation_outcome": "recommendation → outcome",
    "writer_topic_outcome": "writer → topic → outcome",
    "citation_source_visibility": "citation source → AI visibility",
    "content_structure_citation": "content structure → citation result",
    "industry_geo_strategy_result": "industry → GEO strategy → result",
    "entity_gap_intervention_result": "entity gap → intervention → result",
    "competitor_movement_response_outcome": "competitor movement → response → outcome",
}

NODE_ROLES: tuple[str, ...] = (
    "stimulus",
    "intervention",
    "mediator",
    "result",
)

NODE_KINDS: tuple[str, ...] = (
    "recommendation",
    "outcome",
    "writer",
    "topic",
    "citation_source",
    "ai_visibility",
    "content_structure",
    "citation_result",
    "industry",
    "geo_strategy",
    "strategy_result",
    "entity_gap",
    "intervention",
    "competitor_movement",
    "response",
)

EDGE_TYPES: tuple[str, ...] = (
    "leads_to",
    "wrote",
    "targets",
    "cites",
    "influences",
    "structures",
    "achieves",
    "applies_in",
    "closes",
    "responds_to",
    "realized",
)

MOAT_POSITIONING = (
    "The Peacock Moat Data Model accumulates proprietary intelligence pathways "
    "across Peacock One. Over time this dataset becomes Peacock's long-term "
    "competitive advantage — closed-loop memory that competitors cannot easily "
    "replicate from public SEO tools alone."
)

NOT_UNIVERSAL_GEO = (
    "Industry → GEO strategy → result pathways are industry-scoped. "
    "Peacock does not claim a universal GEO strategy."
)

METHODOLOGY = "peacock_moat_data_model_v1"
METHODOLOGY_NOTE = (
    "Peacock Moat Data Model stores typed proprietary pathways "
    "(stimulus → intervention/mediator → result) with outcomes and confidence. "
    + MOAT_POSITIONING + " " + NOT_UNIVERSAL_GEO
)


class MoatIntelligenceRun(Base, WorkspaceTenantMixin):
    """One moat accumulation / snapshot run for a brand."""

    __tablename__ = "moat_intelligence_runs"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_brand: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    industry: Mapped[str | None] = mapped_column(String(64), index=True)
    run_status: Mapped[str] = mapped_column(
        String(32), default="completed", nullable=False, index=True
    )
    methodology: Mapped[str] = mapped_column(String(64), default=METHODOLOGY, nullable=False)
    moat_positioning: Mapped[str] = mapped_column(Text, nullable=False)
    pathways_count: Mapped[int] = mapped_column(Integer, nullable=False)
    nodes_count: Mapped[int] = mapped_column(Integer, nullable=False)
    edges_count: Mapped[int] = mapped_column(Integer, nullable=False)
    outcomes_count: Mapped[int] = mapped_column(Integer, nullable=False)
    moat_strength_score: Mapped[float] = mapped_column(Float, nullable=False)
    mean_outcome_delta: Mapped[float | None] = mapped_column(Float)
    mean_confidence: Mapped[float | None] = mapped_column(Float)
    summary: Mapped[str | None] = mapped_column(Text)
    analysed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    notes: Mapped[str | None] = mapped_column(Text)

    pathways: Mapped[list[MoatPathway]] = relationship(
        back_populates="run", cascade="all, delete-orphan", passive_deletes=True
    )


class MoatPathway(Base, WorkspaceTenantMixin):
    """One proprietary intelligence pathway instance."""

    __tablename__ = "moat_pathways"
    __table_args__ = (UniqueConstraint("run_id", "pathway_key"),)

    run_id: Mapped[str] = mapped_column(
        ForeignKey("moat_intelligence_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pathway_kind: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    pathway_label: Mapped[str] = mapped_column(String(255), nullable=False)
    pathway_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    industry: Mapped[str | None] = mapped_column(String(64), index=True)
    topic_key: Mapped[str | None] = mapped_column(String(128), index=True)
    expected_score: Mapped[float | None] = mapped_column(Float)
    actual_score: Mapped[float | None] = mapped_column(Float)
    outcome_delta: Mapped[float | None] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    sample_weight: Mapped[float] = mapped_column(Float, nullable=False)
    source_system: Mapped[str | None] = mapped_column(String(64), index=True)
    source_ref: Mapped[str | None] = mapped_column(String(128))
    narrative: Mapped[str] = mapped_column(Text, nullable=False)
    rank_order: Mapped[int] = mapped_column(Integer, nullable=False)

    run: Mapped[MoatIntelligenceRun] = relationship(back_populates="pathways")
    nodes: Mapped[list[MoatPathwayNode]] = relationship(
        back_populates="pathway", cascade="all, delete-orphan", passive_deletes=True
    )
    edges: Mapped[list[MoatPathwayEdge]] = relationship(
        back_populates="pathway", cascade="all, delete-orphan", passive_deletes=True
    )
    outcomes: Mapped[list[MoatPathwayOutcome]] = relationship(
        back_populates="pathway", cascade="all, delete-orphan", passive_deletes=True
    )


class MoatPathwayNode(Base, WorkspaceTenantMixin):
    """Ordered hop in a proprietary pathway."""

    __tablename__ = "moat_pathway_nodes"
    __table_args__ = (UniqueConstraint("pathway_id", "node_ordinal"),)

    pathway_id: Mapped[str] = mapped_column(
        ForeignKey("moat_pathways.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    node_ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    node_role: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    node_kind: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    node_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(255), nullable=False)

    pathway: Mapped[MoatPathway] = relationship(back_populates="nodes")


class MoatPathwayEdge(Base, WorkspaceTenantMixin):
    """Directed relationship between pathway nodes."""

    __tablename__ = "moat_pathway_edges"
    __table_args__ = (
        UniqueConstraint("pathway_id", "from_ordinal", "to_ordinal", "edge_type"),
    )

    pathway_id: Mapped[str] = mapped_column(
        ForeignKey("moat_pathways.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    to_ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    edge_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    weight: Mapped[float] = mapped_column(Float, nullable=False)

    pathway: Mapped[MoatPathway] = relationship(back_populates="edges")


class MoatPathwayOutcome(Base, WorkspaceTenantMixin):
    """Measured outcome attached to a proprietary pathway."""

    __tablename__ = "moat_pathway_outcomes"
    __table_args__ = (UniqueConstraint("pathway_id", "metric_key", "observed_at"),)

    pathway_id: Mapped[str] = mapped_column(
        ForeignKey("moat_pathways.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    metric_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    baseline_value: Mapped[float | None] = mapped_column(Float)
    delta: Mapped[float | None] = mapped_column(Float)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    provenance: Mapped[str | None] = mapped_column(String(255))

    pathway: Mapped[MoatPathway] = relationship(back_populates="outcomes")
