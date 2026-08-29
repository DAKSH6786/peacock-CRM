"""Peacock One Quality Bar — module completeness gates before shipping.

Before considering any module complete, ask:

1. Does this merely match a conventional SEO tool? → Improve it.
2. Does this merely track AI mentions? → Improve it.
3. Does this only give an LLM recommendation? → Add evidence.
4. Does it have evidence but no uncertainty? → Add confidence.
5. Does it recommend something but never measure the result? → Add outcome tracking.
6. Does it track results but never learn from them? → Connect to Peacock Learning.
7. Does an expensive LLM call perform something deterministic code could calculate?
   → Move it out of the LLM.
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


QUALITY_GATES: tuple[str, ...] = (
    "beyond_conventional_seo",
    "beyond_ai_mention_tracking",
    "evidence_backed_recommendations",
    "uncertainty_with_evidence",
    "outcome_tracking",
    "learning_loop",
    "deterministic_over_llm",
)

GATE_QUESTIONS: dict[str, str] = {
    "beyond_conventional_seo": "Does this merely match a conventional SEO tool?",
    "beyond_ai_mention_tracking": "Does this merely track AI mentions?",
    "evidence_backed_recommendations": "Does this only give an LLM recommendation?",
    "uncertainty_with_evidence": "Does it have evidence but no uncertainty?",
    "outcome_tracking": "Does it recommend something but never measure the result?",
    "learning_loop": "Does it track results but never learn from them?",
    "deterministic_over_llm": (
        "Does an expensive LLM call perform something deterministic code could calculate?"
    ),
}

GATE_IMPROVEMENTS: dict[str, str] = {
    "beyond_conventional_seo": "Improve it.",
    "beyond_ai_mention_tracking": "Improve it.",
    "evidence_backed_recommendations": "Add evidence.",
    "uncertainty_with_evidence": "Add confidence.",
    "outcome_tracking": "Add outcome tracking.",
    "learning_loop": "Connect it to Peacock Learning.",
    "deterministic_over_llm": "Move it out of the LLM.",
}

GATE_LABELS: dict[str, str] = {
    "beyond_conventional_seo": "Beyond conventional SEO",
    "beyond_ai_mention_tracking": "Beyond AI mention tracking",
    "evidence_backed_recommendations": "Evidence-backed recommendations",
    "uncertainty_with_evidence": "Uncertainty / confidence",
    "outcome_tracking": "Outcome tracking",
    "learning_loop": "Peacock Learning loop",
    "deterministic_over_llm": "Deterministic over expensive LLM",
}

# Passing = answering the "does it merely/only…?" question with NO (or remediated)
GATE_PASS_MEANS: dict[str, str] = {
    "beyond_conventional_seo": "Delivers generative visibility / GEO-AEO value beyond classic SEO.",
    "beyond_ai_mention_tracking": "Measures influence, citations, pathways — not mention counts alone.",
    "evidence_backed_recommendations": "Recommendations cite ledger / observations / graph evidence.",
    "uncertainty_with_evidence": "Evidence is paired with confidence or uncertainty bands.",
    "outcome_tracking": "Recommendations are linked to measured outcomes.",
    "learning_loop": "Outcomes feed Peacock Learning Engine industry memory.",
    "deterministic_over_llm": "Deterministic calculations stay in code; LLMs reserved for judgment.",
}

COMPLETENESS_VERDICTS: tuple[str, ...] = (
    "complete",
    "incomplete",
    "blocked",
)

METHODOLOGY = "peacock_one_quality_bar_v1"
METHODOLOGY_NOTE = (
    "Peacock One Quality Bar is the shipping checklist for every module. "
    "A module is not complete if it merely matches a conventional SEO tool, "
    "only tracks AI mentions, only emits LLM advice without evidence/confidence/"
    "outcomes/learning, or spends LLM calls on deterministic work."
)
QUALITY_POSITIONING = (
    "Peacock One Quality Bar raises the product above conventional SEO and "
    "naive AI-mention dashboards — evidence, uncertainty, outcomes, learning, "
    "and deterministic-first intelligence."
)


class QualityBarAssessment(Base, WorkspaceTenantMixin):
    """One Quality Bar assessment of a Peacock module."""

    __tablename__ = "quality_bar_assessments"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_brand: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    module_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    module_label: Mapped[str] = mapped_column(String(255), nullable=False)
    completeness_verdict: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    gates_total: Mapped[int] = mapped_column(Integer, nullable=False)
    gates_passed: Mapped[int] = mapped_column(Integer, nullable=False)
    gates_failed: Mapped[int] = mapped_column(Integer, nullable=False)
    completeness_score: Mapped[float] = mapped_column(Float, nullable=False)
    blocked_by: Mapped[str | None] = mapped_column(Text)
    improvement_summary: Mapped[str] = mapped_column(Text, nullable=False)
    methodology: Mapped[str] = mapped_column(String(64), default=METHODOLOGY, nullable=False)
    quality_positioning: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    analysed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    notes: Mapped[str | None] = mapped_column(Text)

    gate_results: Mapped[list[QbGateResult]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan", passive_deletes=True
    )
    remediation_actions: Mapped[list[QbRemediationAction]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan", passive_deletes=True
    )


class QbGateResult(Base, WorkspaceTenantMixin):
    """Pass/fail for one Quality Bar gate on an assessment."""

    __tablename__ = "qb_gate_results"
    __table_args__ = (UniqueConstraint("assessment_id", "gate_key"),)

    assessment_id: Mapped[str] = mapped_column(
        ForeignKey("quality_bar_assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    gate_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    gate_label: Mapped[str] = mapped_column(String(255), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    improvement_if_fail: Mapped[str] = mapped_column(Text, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    answer_yes_problem: Mapped[bool] = mapped_column(Boolean, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_note: Mapped[str | None] = mapped_column(Text)
    rank_order: Mapped[int] = mapped_column(Integer, nullable=False)

    assessment: Mapped[QualityBarAssessment] = relationship(back_populates="gate_results")


class QbRemediationAction(Base, WorkspaceTenantMixin):
    """Concrete improvement required when a gate fails."""

    __tablename__ = "qb_remediation_actions"
    __table_args__ = (UniqueConstraint("assessment_id", "gate_key", "action_key"),)

    assessment_id: Mapped[str] = mapped_column(
        ForeignKey("quality_bar_assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    gate_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    action_key: Mapped[str] = mapped_column(String(64), nullable=False)
    action_label: Mapped[str] = mapped_column(String(255), nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False)
    links_to_learning: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rank_order: Mapped[int] = mapped_column(Integer, nullable=False)

    assessment: Mapped[QualityBarAssessment] = relationship(
        back_populates="remediation_actions"
    )
