"""Peacock Opportunity Engine — always-on intelligence layer for ranked opportunities."""

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


OPPORTUNITY_TYPES: tuple[str, ...] = (
    "competitor_gained_ai_visibility",
    "new_citation_source_emerged",
    "high_value_topic_available",
    "existing_article_decaying",
    "entity_relationship_weakened",
    "new_prompt_cluster_appeared",
    "competitor_content_outdated",
    "ai_sentiment_changed",
    "backlink_source_gained_influence",
    "search_demand_shifted",
    "ai_answer_changed_materially",
)

# Explainable ranking features (not a forever-fixed black box)
RANKING_FEATURES: tuple[str, ...] = (
    "impact",
    "urgency",
    "confidence",
    "expected_value",
    "difficulty",  # inverted in score (higher difficulty lowers rank)
)

# Seed explainable weights — adjustable via historical outcomes
DEFAULT_RANKING_WEIGHTS: dict[str, float] = {
    "impact": 0.25,
    "urgency": 0.20,
    "confidence": 0.15,
    "expected_value": 0.30,
    "difficulty": 0.10,  # applied as (100 - difficulty)
}

METHODOLOGY = "peacock_opportunity_engine_explainable_adaptive"

METHODOLOGY_NOTE = (
    "Peacock Opportunities is an always-running intelligence layer. Ranking starts "
    "explainable (transparent feature contributions for impact, urgency, confidence, "
    "expected value, difficulty). It does not use one manually weighted formula forever — "
    "historical opportunity outcomes adjust feature weights over time while remaining "
    "inspectable."
)

ALWAYS_ON_NOTE = (
    "Peacock Opportunities is designed as a continuous intelligence layer: scans detect "
    "emerging signals (competitor AI visibility, citation sources, decaying pages, prompt "
    "clusters, sentiment/answer shifts, etc.) and refresh ranked opportunities."
)


class OpportunityScan(Base, WorkspaceTenantMixin):
    """One pass of the always-on Opportunity Engine over a workspace/website."""

    __tablename__ = "opportunity_scans"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_brand: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    scan_status: Mapped[str] = mapped_column(
        String(32), default="completed", nullable=False, index=True
    )
    methodology: Mapped[str] = mapped_column(
        String(64), default=METHODOLOGY, nullable=False
    )
    always_on_layer: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ranking_model_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    ranking_is_adaptive: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    fixed_formula_rejected: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    opportunity_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)

    opportunities: Mapped[list[PeacockOpportunity]] = relationship(
        back_populates="scan", cascade="all, delete-orphan", passive_deletes=True
    )
    ranking_weights: Mapped[list[PoRankingWeight]] = relationship(
        back_populates="scan", cascade="all, delete-orphan", passive_deletes=True
    )


class PeacockOpportunity(Base, WorkspaceTenantMixin):
    """A single ranked Peacock Opportunity with evidence and recommended action."""

    __tablename__ = "peacock_opportunities"
    __table_args__ = (UniqueConstraint("scan_id", "opportunity_key"),)

    scan_id: Mapped[str] = mapped_column(
        ForeignKey("opportunity_scans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    opportunity_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    opportunity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    # Core fields required by product
    impact: Mapped[float] = mapped_column(Float, nullable=False)  # 0–100
    urgency: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    difficulty: Mapped[float] = mapped_column(Float, nullable=False)
    expected_value: Mapped[float] = mapped_column(Float, nullable=False)
    recommended_action: Mapped[str] = mapped_column(Text, nullable=False)
    # Ranking
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    opportunity_score: Mapped[float] = mapped_column(Float, nullable=False)
    ranking_explanation: Mapped[str] = mapped_column(Text, nullable=False)
    related_entity: Mapped[str | None] = mapped_column(String(512))
    related_url: Mapped[str | None] = mapped_column(String(2048))
    status_label: Mapped[str] = mapped_column(
        String(32), default="open", nullable=False, index=True
    )

    scan: Mapped[OpportunityScan] = relationship(back_populates="opportunities")
    evidence_items: Mapped[list[PoEvidence]] = relationship(
        back_populates="opportunity", cascade="all, delete-orphan", passive_deletes=True
    )
    ranking_factors: Mapped[list[PoRankingFactor]] = relationship(
        back_populates="opportunity", cascade="all, delete-orphan", passive_deletes=True
    )


class PoEvidence(Base, WorkspaceTenantMixin):
    """Evidence supporting an opportunity."""

    __tablename__ = "po_evidence"

    opportunity_id: Mapped[str] = mapped_column(
        ForeignKey("peacock_opportunities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    evidence_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    source_ref: Mapped[str | None] = mapped_column(String(512))
    strength: Mapped[float] = mapped_column(Float, default=50.0, nullable=False)

    opportunity: Mapped[PeacockOpportunity] = relationship(back_populates="evidence_items")


class PoRankingFactor(Base, WorkspaceTenantMixin):
    """Explainable contribution of one ranking feature to opportunity_score."""

    __tablename__ = "po_ranking_factors"
    __table_args__ = (UniqueConstraint("opportunity_id", "feature_code"),)

    opportunity_id: Mapped[str] = mapped_column(
        ForeignKey("peacock_opportunities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    feature_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    feature_value: Mapped[float] = mapped_column(Float, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    contribution: Mapped[float] = mapped_column(Float, nullable=False)
    weight_source: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # base|learned|blended
    explanation: Mapped[str] = mapped_column(Text, nullable=False)

    opportunity: Mapped[PeacockOpportunity] = relationship(back_populates="ranking_factors")


class PoRankingWeight(Base, WorkspaceTenantMixin):
    """Ranking feature weight snapshot for a scan (base + learned blend)."""

    __tablename__ = "po_ranking_weights"
    __table_args__ = (UniqueConstraint("scan_id", "feature_code"),)

    scan_id: Mapped[str] = mapped_column(
        ForeignKey("opportunity_scans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    feature_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    base_weight: Mapped[float] = mapped_column(Float, nullable=False)
    learned_weight: Mapped[float] = mapped_column(Float, nullable=False)
    effective_weight: Mapped[float] = mapped_column(Float, nullable=False)
    learning_sample_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)

    scan: Mapped[OpportunityScan] = relationship(back_populates="ranking_weights")


class PoOutcomeFeedback(Base, WorkspaceTenantMixin):
    """Historical outcome used to improve ranking weights over time."""

    __tablename__ = "po_outcome_feedback"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    opportunity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    opportunity_key: Mapped[str | None] = mapped_column(String(128), index=True)
    # Snapshot of scores at decision time
    impact: Mapped[float] = mapped_column(Float, nullable=False)
    urgency: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    difficulty: Mapped[float] = mapped_column(Float, nullable=False)
    expected_value: Mapped[float] = mapped_column(Float, nullable=False)
    predicted_score: Mapped[float] = mapped_column(Float, nullable=False)
    # Observed outcome 0–100 (realized value / success)
    realized_outcome: Mapped[float] = mapped_column(Float, nullable=False)
    outcome_label: Mapped[str] = mapped_column(
        String(64), default="observed", nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text)
