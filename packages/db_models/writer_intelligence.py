"""Writer Intelligence 2.0 — proprietary writer decision system (not sample similarity)."""

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


# Writer DNA traits — proprietary multi-signal profile
WRITER_DNA_TRAITS: tuple[str, ...] = (
    "subject_expertise",
    "research_depth",
    "technical_accuracy",
    "style",
    "tone",
    "sentence_structure",
    "readability",
    "storytelling",
    "citations",
    "fact_density",
    "original_thinking",
    "seo_execution",
    "aeo_execution",
    "geo_execution",
    "editing_effort",  # historical rewrite burden (higher = more effort needed)
    "deadline_reliability",
    "client_acceptance",
)

# Outcome graph node kinds: Writer → Article → Client → Industry → Topic → Performance
OUTCOME_NODE_KINDS: tuple[str, ...] = (
    "writer",
    "article",
    "client",
    "industry",
    "topic",
    "performance",
)

OUTCOME_EDGE_TYPES: tuple[str, ...] = (
    "wrote",           # writer → article
    "for_client",      # article → client
    "in_industry",     # client/article → industry
    "on_topic",        # article → topic
    "achieved",        # article → performance
)

# Performance signals on the outcome graph
PERFORMANCE_METRICS: tuple[str, ...] = (
    "approval",
    "revision_rounds",  # lower is better when inverted for score
    "ranking",
    "impressions",
    "ai_citations",
    "engagement",
    "links_earned",
    "conversion",
)

METHODOLOGY = "writer_intelligence_2_outcome_decision"

METHODOLOGY_NOTE = (
    "Writer Intelligence 2.0 is a proprietary decision system. It does NOT merely "
    "embed writing samples and calculate similarity. Recommendations answer: which "
    "writer is most likely to produce the best outcome for THIS topic, THIS client, "
    "and THIS audience — using Writer DNA, Writer×Topic×Client scoring, and the "
    "Writer Outcome Graph."
)

SIMILARITY_ONLY_REJECTED = (
    "Similarity-only matching (embed samples → nearest neighbor) is rejected as the "
    "primary decision method. Sample likeness is not a substitute for predicted "
    "outcome on this topic × client × audience."
)


class WriterIntelligenceAnalysis(Base, WorkspaceTenantMixin):
    """A Writer Intelligence 2.0 recommendation / analysis run."""

    __tablename__ = "writer_intelligence_analyses"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_brand: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    industry: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    topic: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    audience: Mapped[str] = mapped_column(String(512), nullable=False)
    analysis_status: Mapped[str] = mapped_column(
        String(32), default="draft", nullable=False, index=True
    )
    methodology: Mapped[str] = mapped_column(
        String(64), default=METHODOLOGY, nullable=False
    )
    similarity_only_rejected: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    similarity_rejection_note: Mapped[str] = mapped_column(Text, nullable=False)
    decision_question: Mapped[str] = mapped_column(Text, nullable=False)
    top_writer_key: Mapped[str | None] = mapped_column(String(128), index=True)
    top_outcome_score: Mapped[float | None] = mapped_column(Float)
    summary: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)

    dna_profiles: Mapped[list[WiWriterDna]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True
    )
    recommendations: Mapped[list[WiRecommendation]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True
    )
    outcome_nodes: Mapped[list[WiOutcomeNode]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True
    )
    outcome_edges: Mapped[list[WiOutcomeEdge]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True
    )
    performance_records: Mapped[list[WiPerformanceRecord]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True
    )


class WiWriterDna(Base, WorkspaceTenantMixin):
    """Writer DNA composite profile for one writer in an analysis."""

    __tablename__ = "wi_writer_dna"
    __table_args__ = (UniqueConstraint("analysis_id", "writer_key"),)

    analysis_id: Mapped[str] = mapped_column(
        ForeignKey("writer_intelligence_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    writer_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    dna_composite_score: Mapped[float] = mapped_column(Float, nullable=False)
    dna_summary: Mapped[str] = mapped_column(Text, nullable=False)

    analysis: Mapped[WriterIntelligenceAnalysis] = relationship(
        back_populates="dna_profiles"
    )
    traits: Mapped[list[WiDnaTrait]] = relationship(
        back_populates="dna", cascade="all, delete-orphan", passive_deletes=True
    )


class WiDnaTrait(Base, WorkspaceTenantMixin):
    """Single Writer DNA trait score (0–100)."""

    __tablename__ = "wi_dna_traits"
    __table_args__ = (UniqueConstraint("dna_id", "trait_code"),)

    dna_id: Mapped[str] = mapped_column(
        ForeignKey("wi_writer_dna.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    trait_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    evidence: Mapped[str] = mapped_column(Text, nullable=False)

    dna: Mapped[WiWriterDna] = relationship(back_populates="traits")


class WiOutcomeNode(Base, WorkspaceTenantMixin):
    """Node on the Writer Outcome Graph."""

    __tablename__ = "wi_outcome_nodes"
    __table_args__ = (UniqueConstraint("analysis_id", "node_kind", "node_key"),)

    analysis_id: Mapped[str] = mapped_column(
        ForeignKey("writer_intelligence_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    node_kind: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    node_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(512), nullable=False)
    attributes_json: Mapped[str | None] = mapped_column(Text)

    analysis: Mapped[WriterIntelligenceAnalysis] = relationship(
        back_populates="outcome_nodes"
    )


class WiOutcomeEdge(Base, WorkspaceTenantMixin):
    """Directed edge on the Writer Outcome Graph."""

    __tablename__ = "wi_outcome_edges"

    analysis_id: Mapped[str] = mapped_column(
        ForeignKey("writer_intelligence_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    edge_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    from_node_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    from_node_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    to_node_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    to_node_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    analysis: Mapped[WriterIntelligenceAnalysis] = relationship(
        back_populates="outcome_edges"
    )


class WiPerformanceRecord(Base, WorkspaceTenantMixin):
    """Article performance signals feeding the Outcome Graph."""

    __tablename__ = "wi_performance_records"
    __table_args__ = (UniqueConstraint("analysis_id", "article_key"),)

    analysis_id: Mapped[str] = mapped_column(
        ForeignKey("writer_intelligence_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    article_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    writer_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    client_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    industry: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    topic: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    approval: Mapped[float | None] = mapped_column(Float)  # 0–1
    revision_rounds: Mapped[float | None] = mapped_column(Float)
    ranking: Mapped[float | None] = mapped_column(Float)  # normalized 0–1 higher better
    impressions: Mapped[float | None] = mapped_column(Float)
    ai_citations: Mapped[float | None] = mapped_column(Float)
    engagement: Mapped[float | None] = mapped_column(Float)
    links_earned: Mapped[float | None] = mapped_column(Float)
    conversion: Mapped[float | None] = mapped_column(Float)
    composite_outcome: Mapped[float] = mapped_column(Float, nullable=False)

    analysis: Mapped[WriterIntelligenceAnalysis] = relationship(
        back_populates="performance_records"
    )


class WiRecommendation(Base, WorkspaceTenantMixin):
    """Ranked writer recommendation from the Writer×Topic×Client model."""

    __tablename__ = "wi_recommendations"
    __table_args__ = (UniqueConstraint("analysis_id", "writer_key"),)

    analysis_id: Mapped[str] = mapped_column(
        ForeignKey("writer_intelligence_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    writer_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    predicted_outcome_score: Mapped[float] = mapped_column(Float, nullable=False)
    dna_fit_score: Mapped[float] = mapped_column(Float, nullable=False)
    topic_fit_score: Mapped[float] = mapped_column(Float, nullable=False)
    client_fit_score: Mapped[float] = mapped_column(Float, nullable=False)
    audience_fit_score: Mapped[float] = mapped_column(Float, nullable=False)
    historical_outcome_score: Mapped[float] = mapped_column(Float, nullable=False)
    similarity_score_unused: Mapped[float | None] = mapped_column(Float)
    similarity_not_used_as_primary: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    decision_answer: Mapped[str] = mapped_column(Text, nullable=False)

    analysis: Mapped[WriterIntelligenceAnalysis] = relationship(
        back_populates="recommendations"
    )
