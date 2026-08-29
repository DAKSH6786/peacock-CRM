"""Share of Answer — multi-indicator generative answer influence.

Traditional SEO uses Share of Voice. Peacock measures Share of Answer:
how much of a generative answer is controlled by or favourable to each
brand/entity.

Token span alone is recorded as a weak signal — it is never treated as
influence by itself. Influence combines mention, position, recommendation
strength, answer space, citation ownership, semantic prominence, claim
polarity, and comparison outcome.
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

from db_models.base import Base, WorkspaceTenantMixin, new_uuid


# Comparison outcome codes (stored lowercase)
COMPARISON_OUTCOMES: tuple[str, ...] = (
    "win",
    "lose",
    "tie",
    "absent",
    "mixed",
)

SOA_INDICATORS: tuple[str, ...] = (
    "mention",
    "position",
    "recommendation_strength",
    "answer_space",
    "citation_ownership",
    "semantic_prominence",
    "positive_claims",
    "negative_claims",
    "neutral_claims",
    "comparison_outcome",
)


class ShareOfAnswerAnalysis(Base, WorkspaceTenantMixin):
    """Share of Answer analysis for a query cluster (e.g. Enterprise CRM)."""

    __tablename__ = "share_of_answer_analyses"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    query_cluster: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    client_brand: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    analysis_status: Mapped[str] = mapped_column(
        String(32), default="draft", nullable=False, index=True
    )
    observation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    entity_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Explicit methodology flag — never token-only
    methodology: Mapped[str] = mapped_column(
        String(64), default="multi_indicator", nullable=False
    )
    token_count_alone_rejected: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text)

    observations: Mapped[list[SoaAnswerObservation]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True
    )
    brand_scores: Mapped[list[SoaBrandScore]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True
    )


class SoaAnswerObservation(Base, WorkspaceTenantMixin):
    """One generative answer observed for Share of Answer scoring."""

    __tablename__ = "soa_answer_observations"

    analysis_id: Mapped[str] = mapped_column(
        ForeignKey("share_of_answer_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    engine_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    model_code: Mapped[str | None] = mapped_column(String(128))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    raw_excerpt: Mapped[str | None] = mapped_column(Text)
    structured_summary: Mapped[str | None] = mapped_column(Text)
    # Total tokens in answer — diagnostic only, never sole influence input
    answer_token_count: Mapped[int | None] = mapped_column(Integer)
    visibility_probe_observation_id: Mapped[str | None] = mapped_column(
        ForeignKey("visibility_probe_observations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    ai_query_run_id: Mapped[str | None] = mapped_column(
        ForeignKey("ai_query_runs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    probe_source: Mapped[str] = mapped_column(String(32), default="mock", nullable=False)

    analysis: Mapped[ShareOfAnswerAnalysis] = relationship(back_populates="observations")
    entity_indicators: Mapped[list[SoaEntityIndicator]] = relationship(
        back_populates="observation", cascade="all, delete-orphan", passive_deletes=True
    )


class SoaEntityIndicator(Base, WorkspaceTenantMixin):
    """Per-entity multi-indicator reading inside one generative answer."""

    __tablename__ = "soa_entity_indicators"
    __table_args__ = (UniqueConstraint("observation_id", "entity_name"),)

    observation_id: Mapped[str] = mapped_column(
        ForeignKey("soa_answer_observations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    entity_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    is_client: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    # --- Tracked indicators ---
    mention: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mention_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    position: Mapped[int | None] = mapped_column(Integer)  # 1 = top recommendation
    recommendation_strength: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    # Structural presence in the answer (section / slot share) — not raw tokens-as-influence
    answer_space: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    citation_ownership: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    semantic_prominence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    positive_claims: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    negative_claims: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    neutral_claims: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    comparison_outcome: Mapped[str] = mapped_column(
        String(16), default="absent", nullable=False, index=True
    )
    # Diagnostic: token span ratio — capped contribution in scorer, never alone
    token_span_ratio: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    # Composite influence for this entity in this answer (pre-normalisation)
    influence_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    observation: Mapped[SoaAnswerObservation] = relationship(back_populates="entity_indicators")


class SoaBrandScore(Base, WorkspaceTenantMixin):
    """Aggregated Share of Answer for a brand within a query cluster analysis."""

    __tablename__ = "soa_brand_scores"
    __table_args__ = (UniqueConstraint("analysis_id", "entity_name"),)

    analysis_id: Mapped[str] = mapped_column(
        ForeignKey("share_of_answer_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    entity_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    is_client: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    # Primary headline metric (0–100 percentage points of answer influence)
    share_of_answer: Mapped[float] = mapped_column(Float, nullable=False)

    # Indicator averages (0–1 unless noted)
    mention_rate: Mapped[float] = mapped_column(Float, nullable=False)
    avg_position_score: Mapped[float] = mapped_column(Float, nullable=False)
    avg_recommendation_strength: Mapped[float] = mapped_column(Float, nullable=False)
    avg_answer_space: Mapped[float] = mapped_column(Float, nullable=False)
    avg_citation_ownership: Mapped[float] = mapped_column(Float, nullable=False)
    avg_semantic_prominence: Mapped[float] = mapped_column(Float, nullable=False)
    avg_claim_balance: Mapped[float] = mapped_column(Float, nullable=False)
    avg_comparison_score: Mapped[float] = mapped_column(Float, nullable=False)
    # Diagnostic only
    avg_token_span_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    token_only_share: Mapped[float] = mapped_column(Float, nullable=False)
    # How much token-only share diverges from multi-indicator SOA
    token_vs_influence_gap: Mapped[float] = mapped_column(Float, nullable=False)

    positive_claims_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    negative_claims_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    neutral_claims_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    observation_sample_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mean_influence: Mapped[float] = mapped_column(Float, nullable=False)

    analysis: Mapped[ShareOfAnswerAnalysis] = relationship(back_populates="brand_scores")
