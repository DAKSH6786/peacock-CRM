"""Content Digital Twin — pre-publish article simulation against multi-channel requirements."""

from __future__ import annotations

from sqlalchemy import (
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db_models.base import Base, WorkspaceTenantMixin


# Surfaces the twin is simulated against
SIMULATION_SURFACES: tuple[str, ...] = (
    "seo_requirements",
    "aeo_requirements",
    "geo_requirements",
    "competitor_pages",
    "target_entities",
    "user_personas",
    "ai_answer_scenarios",
    "citation_requirements",
    "brand_guidelines",
)

# Finding categories produced by an evaluation
FINDING_CATEGORIES: tuple[str, ...] = (
    "predicted_strength",
    "potential_weakness",
    "missing_entity",
    "missing_evidence",
    "missing_question",
    "competitor_advantage",
    "citation_opportunity",
    "differentiation_opportunity",
)

METHODOLOGY = "content_digital_twin_pre_publish_simulation"

METHODOLOGY_NOTE = (
    "Content Digital Twin simulates a proposed article plan against SEO, AEO, GEO, "
    "competitor pages, target entities, user personas, AI answer scenarios, citation "
    "requirements, and brand guidelines before publish. Users can modify the plan and "
    "rerun evaluation. Scores are Peacock estimates, not live SERP/AI guarantees."
)


class ContentDigitalTwin(Base, WorkspaceTenantMixin):
    """A proposed article's digital twin — plan + evaluation history."""

    __tablename__ = "content_digital_twins"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_brand: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    topic_cluster: Mapped[str | None] = mapped_column(String(255), index=True)
    twin_status: Mapped[str] = mapped_column(
        String(32), default="draft", nullable=False, index=True
    )
    # Latest article plan as JSON text (title, outline, entities, questions, …)
    article_plan_json: Mapped[str] = mapped_column(Text, nullable=False)
    # Simulation context as JSON text (requirements, competitors, personas, …)
    simulation_context_json: Mapped[str] = mapped_column(Text, nullable=False)
    plan_revision: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    evaluation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    latest_evaluation_id: Mapped[str | None] = mapped_column(String(36), index=True)
    content_lab_proposal_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True
    )
    methodology: Mapped[str] = mapped_column(
        String(64), default=METHODOLOGY, nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text)

    evaluations: Mapped[list[CdtEvaluation]] = relationship(
        back_populates="twin", cascade="all, delete-orphan", passive_deletes=True
    )


class CdtEvaluation(Base, WorkspaceTenantMixin):
    """One simulation run of a twin (supports modify-plan + rerun)."""

    __tablename__ = "cdt_evaluations"
    __table_args__ = (UniqueConstraint("twin_id", "evaluation_number"),)

    twin_id: Mapped[str] = mapped_column(
        ForeignKey("content_digital_twins.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    evaluation_number: Mapped[int] = mapped_column(Integer, nullable=False)
    plan_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    # Snapshot of plan + context at evaluation time
    article_plan_snapshot_json: Mapped[str] = mapped_column(Text, nullable=False)
    simulation_context_snapshot_json: Mapped[str] = mapped_column(Text, nullable=False)

    predicted_strength_score: Mapped[float] = mapped_column(Float, nullable=False)
    readiness_score: Mapped[float] = mapped_column(Float, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    evaluation_status: Mapped[str] = mapped_column(
        String(32), default="completed", nullable=False, index=True
    )

    twin: Mapped[ContentDigitalTwin] = relationship(back_populates="evaluations")
    requirement_scores: Mapped[list[CdtRequirementScore]] = relationship(
        back_populates="evaluation", cascade="all, delete-orphan", passive_deletes=True
    )
    findings: Mapped[list[CdtFinding]] = relationship(
        back_populates="evaluation", cascade="all, delete-orphan", passive_deletes=True
    )


class CdtRequirementScore(Base, WorkspaceTenantMixin):
    """Coverage score for one simulation surface (SEO, AEO, …)."""

    __tablename__ = "cdt_requirement_scores"
    __table_args__ = (UniqueConstraint("evaluation_id", "surface"),)

    evaluation_id: Mapped[str] = mapped_column(
        ForeignKey("cdt_evaluations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    surface: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    coverage_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0–100
    matched_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    missing_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)

    evaluation: Mapped[CdtEvaluation] = relationship(back_populates="requirement_scores")


class CdtFinding(Base, WorkspaceTenantMixin):
    """Explainable finding in one of the eight output categories."""

    __tablename__ = "cdt_findings"

    evaluation_id: Mapped[str] = mapped_column(
        ForeignKey("cdt_evaluations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(
        String(16), default="info", nullable=False, index=True
    )  # info|low|medium|high
    related_surface: Mapped[str | None] = mapped_column(String(64), index=True)
    related_item: Mapped[str | None] = mapped_column(String(512))
    priority: Mapped[float] = mapped_column(Float, default=50.0, nullable=False)

    evaluation: Mapped[CdtEvaluation] = relationship(back_populates="findings")
