"""Retrieval Pathway Intelligence — inferred why a page was/wasn't cited.

Peacock does **not** claim access to proprietary internal ranking algorithms
of third-party AI companies. All outputs are framed as:

- inferred retrieval pathway
- observed evidence
- estimated likelihood
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


# Possible forensic causes (classifications)
FORENSIC_CAUSES: tuple[str, ...] = (
    "page_unavailable",
    "crawl_restricted",
    "weak_topical_relevance",
    "insufficient_entity_relationship",
    "competitor_page_stronger",
    "source_freshness",
    "poor_extractability",
    "insufficient_supporting_evidence",
    "lack_of_third_party_corroboration",
    "content_not_retrieved",
    "content_retrieved_but_not_selected",
    "brand_mentioned_but_not_cited",
)

# Likelihood ordinals used in reports
LIKELIHOOD_BANDS: tuple[str, ...] = ("VERY_LOW", "LOW", "MEDIUM", "HIGH", "VERY_HIGH")

# Bottleneck stage labels
BOTTLENECK_STAGES: tuple[str, ...] = (
    "availability",
    "retrieval",
    "selection",
    "citation",
    "mixed",
    "unclear",
)

UNCERTAINTY_BANDS: tuple[str, ...] = ("low", "moderate", "high", "very_high")

METHODOLOGY_DISCLAIMER = (
    "Peacock does not have access to proprietary internal ranking algorithms "
    "of third-party AI companies. Classifications describe an inferred retrieval "
    "pathway from observed evidence and estimated likelihoods only."
)


class RetrievalPathwayAnalysis(Base, WorkspaceTenantMixin):
    """Forensic analysis of why a client page may not be cited."""

    __tablename__ = "retrieval_pathway_analyses"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    query_cluster: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    client_brand: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    target_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    target_domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    analysis_status: Mapped[str] = mapped_column(
        String(32), default="draft", nullable=False, index=True
    )
    methodology: Mapped[str] = mapped_column(
        String(64), default="inferred_retrieval_pathway", nullable=False
    )
    proprietary_ranking_access_claimed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    methodology_disclaimer: Mapped[str] = mapped_column(Text, nullable=False)
    primary_bottleneck_stage: Mapped[str | None] = mapped_column(String(32), index=True)
    primary_bottleneck_label: Mapped[str | None] = mapped_column(String(128))
    estimated_retrieval_likelihood: Mapped[float | None] = mapped_column(Float)
    estimated_selection_likelihood: Mapped[float | None] = mapped_column(Float)
    retrieval_likelihood_band: Mapped[str | None] = mapped_column(String(16))
    selection_likelihood_band: Mapped[str | None] = mapped_column(String(16))
    overall_uncertainty: Mapped[str | None] = mapped_column(String(16))
    interpretation: Mapped[str | None] = mapped_column(Text)
    recommended_investigation: Mapped[str | None] = mapped_column(String(255))
    observation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    evidence_rows: Mapped[list[RpiEvidence]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True
    )
    cause_classifications: Mapped[list[RpiCauseClassification]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True
    )
    bottleneck: Mapped[RpiBottleneckDiagnosis | None] = relationship(
        back_populates="analysis",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )


class RpiEvidence(Base, WorkspaceTenantMixin):
    """Observed evidence feeding an inferred retrieval pathway."""

    __tablename__ = "rpi_evidence"

    analysis_id: Mapped[str] = mapped_column(
        ForeignKey("retrieval_pathway_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    evidence_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    observed_value: Mapped[float | None] = mapped_column(Float)
    observed_text: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(64), default="observed", nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    analysis: Mapped[RetrievalPathwayAnalysis] = relationship(back_populates="evidence_rows")


class RpiCauseClassification(Base, WorkspaceTenantMixin):
    """A possible cause with estimated likelihood and uncertainty."""

    __tablename__ = "rpi_cause_classifications"
    __table_args__ = (UniqueConstraint("analysis_id", "cause_code"),)

    analysis_id: Mapped[str] = mapped_column(
        ForeignKey("retrieval_pathway_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cause_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    estimated_likelihood: Mapped[float] = mapped_column(Float, nullable=False)
    likelihood_band: Mapped[str] = mapped_column(String(16), nullable=False)
    uncertainty: Mapped[str] = mapped_column(String(16), nullable=False)
    supporting_evidence: Mapped[str | None] = mapped_column(Text)
    contrary_evidence: Mapped[str | None] = mapped_column(Text)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    analysis: Mapped[RetrievalPathwayAnalysis] = relationship(
        back_populates="cause_classifications"
    )


class RpiBottleneckDiagnosis(Base, WorkspaceTenantMixin):
    """Headline visibility bottleneck diagnosis (with uncertainty)."""

    __tablename__ = "rpi_bottleneck_diagnoses"
    __table_args__ = (UniqueConstraint("analysis_id"),)

    analysis_id: Mapped[str] = mapped_column(
        ForeignKey("retrieval_pathway_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    bottleneck_stage: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    headline: Mapped[str] = mapped_column(String(255), nullable=False)
    retrieval_probability_band: Mapped[str] = mapped_column(String(16), nullable=False)
    citation_selection_band: Mapped[str] = mapped_column(String(16), nullable=False)
    estimated_retrieval_likelihood: Mapped[float] = mapped_column(Float, nullable=False)
    estimated_selection_likelihood: Mapped[float] = mapped_column(Float, nullable=False)
    interpretation: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_investigation: Mapped[str] = mapped_column(String(255), nullable=False)
    uncertainty: Mapped[str] = mapped_column(String(16), nullable=False)
    disclaimer: Mapped[str] = mapped_column(Text, nullable=False)

    analysis: Mapped[RetrievalPathwayAnalysis] = relationship(back_populates="bottleneck")


# Silence unused import for type checkers that scan Mapped forward refs
_ = datetime
