"""Peacock Judge 2.0 — deterministic multi-signal judgment for major recommendations.

Combines deterministic data, statistical evidence, historical outcomes, multi-model
findings, source reliability, business goals, cost, risk, and confidence.
Scoring runs outside the LLM where possible. Always returns reversal conditions
(«What Would Change Our Decision»).
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


# Input signal families combined by the Judge
JUDGE_SIGNAL_FAMILIES: tuple[str, ...] = (
    "deterministic_data",
    "statistical_evidence",
    "historical_outcomes",
    "multi_model_findings",
    "source_reliability",
    "business_goals",
    "cost",
    "risk",
    "confidence",
)

# Explainable default weights for deterministic blend (cost/risk inverted)
DEFAULT_JUDGE_WEIGHTS: dict[str, float] = {
    "deterministic_data": 0.12,
    "statistical_evidence": 0.12,
    "historical_outcomes": 0.12,
    "multi_model_findings": 0.12,
    "source_reliability": 0.10,
    "business_goals": 0.14,
    "cost": 0.08,  # inverted: higher cost lowers score
    "risk": 0.10,  # inverted
    "confidence": 0.10,
}

METHODOLOGY = "peacock_judge_2_deterministic_multi_signal"

METHODOLOGY_NOTE = (
    "Peacock Judge 2.0 combines deterministic data, statistical evidence, historical "
    "outcomes, multi-model findings, source reliability, business goals, cost, risk, "
    "and confidence. Scoring is deterministic outside the LLM where possible. Every "
    "judgment returns Recommended Action, Why, Evidence, Expected Upside, Risk, "
    "Confidence, Alternative, and What Would Change Our Decision (reversal triggers)."
)

SCORING_OUTSIDE_LLM = (
    "Primary judgment score is computed deterministically from weighted signal "
    "inputs outside the LLM. LLM text may narrate outputs but must not replace "
    "the deterministic score."
)


class Judge2Judgment(Base, WorkspaceTenantMixin):
    """A Peacock Judge 2.0 recommendation judgment."""

    __tablename__ = "judge2_judgments"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_brand: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    decision_question: Mapped[str] = mapped_column(Text, nullable=False)
    judgment_status: Mapped[str] = mapped_column(
        String(32), default="completed", nullable=False, index=True
    )
    methodology: Mapped[str] = mapped_column(
        String(64), default=METHODOLOGY, nullable=False
    )
    scoring_outside_llm: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    scoring_note: Mapped[str] = mapped_column(Text, nullable=False)

    # Required output fields
    recommended_action: Mapped[str] = mapped_column(Text, nullable=False)
    why: Mapped[str] = mapped_column(Text, nullable=False)
    expected_upside: Mapped[str] = mapped_column(Text, nullable=False)
    expected_upside_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_summary: Mapped[str] = mapped_column(Text, nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    alternative: Mapped[str] = mapped_column(Text, nullable=False)
    what_would_change_decision: Mapped[str] = mapped_column(Text, nullable=False)

    composite_score: Mapped[float] = mapped_column(Float, nullable=False)
    action_code: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True
    )  # proceed|conditional|defer|reject
    council2_session_id: Mapped[str | None] = mapped_column(String(36), index=True)
    summary: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)

    signal_scores: Mapped[list[J2SignalScore]] = relationship(
        back_populates="judgment", cascade="all, delete-orphan", passive_deletes=True
    )
    evidence_items: Mapped[list[J2Evidence]] = relationship(
        back_populates="judgment", cascade="all, delete-orphan", passive_deletes=True
    )
    reversal_conditions: Mapped[list[J2ReversalCondition]] = relationship(
        back_populates="judgment", cascade="all, delete-orphan", passive_deletes=True
    )


class J2SignalScore(Base, WorkspaceTenantMixin):
    """Deterministic contribution of one Judge signal family."""

    __tablename__ = "j2_signal_scores"
    __table_args__ = (UniqueConstraint("judgment_id", "signal_code"),)

    judgment_id: Mapped[str] = mapped_column(
        ForeignKey("judge2_judgments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    signal_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    raw_value: Mapped[float] = mapped_column(Float, nullable=False)  # 0–100
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    inverted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    contribution: Mapped[float] = mapped_column(Float, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    computed_outside_llm: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    judgment: Mapped[Judge2Judgment] = relationship(back_populates="signal_scores")


class J2Evidence(Base, WorkspaceTenantMixin):
    """Evidence supporting the judgment."""

    __tablename__ = "j2_evidence"

    judgment_id: Mapped[str] = mapped_column(
        ForeignKey("judge2_judgments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    evidence_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    source_ref: Mapped[str | None] = mapped_column(String(512))
    reliability: Mapped[float] = mapped_column(Float, default=50.0, nullable=False)
    signal_code: Mapped[str | None] = mapped_column(String(64), index=True)

    judgment: Mapped[Judge2Judgment] = relationship(back_populates="evidence_items")


class J2ReversalCondition(Base, WorkspaceTenantMixin):
    """«What Would Change Our Decision» — explicit re-evaluation triggers."""

    __tablename__ = "j2_reversal_conditions"

    judgment_id: Mapped[str] = mapped_column(
        ForeignKey("judge2_judgments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    condition_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    metric_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    operator: Mapped[str] = mapped_column(String(16), nullable=False)  # gt|lt|gte|lte|change_pct
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(32))
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    reevaluate_action: Mapped[str] = mapped_column(
        String(64), default="re-evaluate", nullable=False
    )
    priority: Mapped[float] = mapped_column(Float, default=50.0, nullable=False)

    judgment: Mapped[Judge2Judgment] = relationship(back_populates="reversal_conditions")
