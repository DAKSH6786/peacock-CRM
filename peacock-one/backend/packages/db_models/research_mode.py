"""Peacock Research Mode — controlled analyses for a search intelligence laboratory.

Enterprise users define hypothesis, metric, pages, and prompts; collect baseline;
measure treatment; repeat observations; calculate uncertainty; generate findings.

This moves Peacock from SEO software toward a search intelligence laboratory.
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


STUDY_PHASES: tuple[str, ...] = (
    "hypothesis",
    "metric",
    "pages",
    "prompts",
    "baseline",
    "treatment",
    "repeat_observations",
    "uncertainty",
    "findings",
)

OBSERVATION_ARMS: tuple[str, ...] = (
    "baseline",
    "treatment",
)

PAGE_ROLES: tuple[str, ...] = (
    "control",
    "treatment",
)

# Research metrics (Peacock proprietary indicators — not platform ranking factors)
RESEARCH_METRICS: tuple[str, ...] = (
    "ai_citation_probability",
    "share_of_answer",
    "citation_influence_score",
    "generative_citability_score",
    "answer_readiness_score",
    "peacock_ai_visibility_score",
)

RESEARCH_METRIC_LABELS: dict[str, str] = {
    "ai_citation_probability": "AI citation probability",
    "share_of_answer": "Share of Answer",
    "citation_influence_score": "Citation Influence Score",
    "generative_citability_score": "Generative Citability Score",
    "answer_readiness_score": "Answer Readiness Score",
    "peacock_ai_visibility_score": "Peacock AI Visibility Score",
}

FINDING_VERDICTS: tuple[str, ...] = (
    "supports_hypothesis",
    "does_not_support_hypothesis",
    "inconclusive",
    "needs_more_data",
)

UNCERTAINTY_BANDS: tuple[str, ...] = (
    "low",
    "moderate",
    "high",
    "very_high",
)

LABORATORY_POSITIONING = (
    "Peacock Research Mode is how Peacock moves from SEO software toward a "
    "search intelligence laboratory: controlled analyses with hypothesis, "
    "metrics, pages, prompts, baseline, treatment, repeated observations, "
    "uncertainty, and findings."
)

CAUSALITY_WARNING = (
    "CAUTION: Research Mode does not automatically conclude that a treatment "
    "caused a metric change. Findings report observed deltas with uncertainty. "
    "Confounds, engine drift, seasonality, and small samples can explain lifts. "
    "Prefer controls, repeated observations, and honest uncertainty bands."
)

METHODOLOGY = "peacock_research_mode_controlled_analysis"
METHODOLOGY_NOTE = (
    "Peacock Research Mode enables serious enterprise users to run controlled "
    "analyses: define hypothesis and metric, select pages and prompts, collect "
    "baseline, measure treatment, repeat observations, calculate uncertainty, "
    "and generate findings. " + LABORATORY_POSITIONING + " " + CAUSALITY_WARNING
)


class ResearchStudy(Base, WorkspaceTenantMixin):
    """One controlled Research Mode study."""

    __tablename__ = "research_studies"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_brand: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    research_question: Mapped[str] = mapped_column(Text, nullable=False)
    hypothesis: Mapped[str] = mapped_column(Text, nullable=False)
    metric_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    metric_label: Mapped[str] = mapped_column(String(128), nullable=False)
    treatment_description: Mapped[str] = mapped_column(Text, nullable=False)
    study_status: Mapped[str] = mapped_column(
        String(32), default="completed", nullable=False, index=True
    )
    methodology: Mapped[str] = mapped_column(String(64), default=METHODOLOGY, nullable=False)
    laboratory_positioning: Mapped[str] = mapped_column(Text, nullable=False)
    causality_warning: Mapped[str] = mapped_column(Text, nullable=False)
    completed_phases: Mapped[str] = mapped_column(Text, nullable=False)
    baseline_mean: Mapped[float | None] = mapped_column(Float)
    treatment_mean: Mapped[float | None] = mapped_column(Float)
    absolute_delta: Mapped[float | None] = mapped_column(Float)
    relative_delta_pct: Mapped[float | None] = mapped_column(Float)
    control_adjusted_delta: Mapped[float | None] = mapped_column(Float)
    uncertainty_band: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    uncertainty_score: Mapped[float] = mapped_column(Float, nullable=False)
    finding_verdict: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    finding_summary: Mapped[str] = mapped_column(Text, nullable=False)
    observation_rounds: Mapped[int] = mapped_column(Integer, nullable=False)
    pages_count: Mapped[int] = mapped_column(Integer, nullable=False)
    prompts_count: Mapped[int] = mapped_column(Integer, nullable=False)
    analysed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    notes: Mapped[str | None] = mapped_column(Text)

    pages: Mapped[list[RmPage]] = relationship(
        back_populates="study", cascade="all, delete-orphan", passive_deletes=True
    )
    prompts: Mapped[list[RmPrompt]] = relationship(
        back_populates="study", cascade="all, delete-orphan", passive_deletes=True
    )
    observations: Mapped[list[RmObservation]] = relationship(
        back_populates="study", cascade="all, delete-orphan", passive_deletes=True
    )
    findings: Mapped[list[RmFinding]] = relationship(
        back_populates="study", cascade="all, delete-orphan", passive_deletes=True
    )


class RmPage(Base, WorkspaceTenantMixin):
    """Page selected into a Research Mode study."""

    __tablename__ = "rm_pages"
    __table_args__ = (UniqueConstraint("study_id", "url"),)

    study_id: Mapped[str] = mapped_column(
        ForeignKey("research_studies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    page_role: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    label: Mapped[str | None] = mapped_column(String(255))
    rank_order: Mapped[int] = mapped_column(Integer, nullable=False)

    study: Mapped[ResearchStudy] = relationship(back_populates="pages")


class RmPrompt(Base, WorkspaceTenantMixin):
    """Prompt selected into a Research Mode study."""

    __tablename__ = "rm_prompts"
    __table_args__ = (UniqueConstraint("study_id", "prompt_text"),)

    study_id: Mapped[str] = mapped_column(
        ForeignKey("research_studies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_cluster: Mapped[str | None] = mapped_column(String(128), index=True)
    rank_order: Mapped[int] = mapped_column(Integer, nullable=False)

    study: Mapped[ResearchStudy] = relationship(back_populates="prompts")


class RmObservation(Base, WorkspaceTenantMixin):
    """Repeated metric observation (baseline or treatment arm)."""

    __tablename__ = "rm_observations"
    __table_args__ = (
        UniqueConstraint(
            "study_id",
            "arm",
            "round_index",
            "page_url",
            "prompt_text",
            name="uq_rm_observations_point",
        ),
    )

    study_id: Mapped[str] = mapped_column(
        ForeignKey("research_studies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    arm: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    round_index: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    page_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    page_role: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    metric_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    study: Mapped[ResearchStudy] = relationship(back_populates="observations")


class RmFinding(Base, WorkspaceTenantMixin):
    """Structured research finding with uncertainty."""

    __tablename__ = "rm_findings"
    __table_args__ = (UniqueConstraint("study_id", "finding_index"),)

    study_id: Mapped[str] = mapped_column(
        ForeignKey("research_studies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    finding_index: Mapped[int] = mapped_column(Integer, nullable=False)
    verdict: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    claim: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[str] = mapped_column(Text, nullable=False)
    uncertainty_band: Mapped[str] = mapped_column(String(32), nullable=False)
    uncertainty_rationale: Mapped[str] = mapped_column(Text, nullable=False)
    auto_causal_conclusion_rejected: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    next_step: Mapped[str] = mapped_column(Text, nullable=False)

    study: Mapped[ResearchStudy] = relationship(back_populates="findings")
