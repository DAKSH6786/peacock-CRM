"""Peacock Cost Intelligence — Intelligence Budget Engine.

Before deep workflows, estimate expected calls, tokens, searches, runtime,
and cost. PINE should choose the cheapest reliable method:

- Do NOT use five LLMs if deterministic data can answer.
- Do NOT run Council mode for a simple page-title recommendation.
- Reserve expensive reasoning for high-value decisions.

Complements Peacock mode hard envelopes (runtime enforcement) with
pre-flight planning and method selection.
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


METHOD_KINDS: tuple[str, ...] = (
    "deterministic",
    "single_llm",
    "multi_llm",
    "council",
    "lab_experiment",
    "web_search",
)

METHOD_KIND_LABELS: dict[str, str] = {
    "deterministic": "Deterministic data / rules",
    "single_llm": "Single LLM pass",
    "multi_llm": "Multi-LLM deep workflow",
    "council": "Council adversarial debate",
    "lab_experiment": "Lab repeated experiments",
    "web_search": "Web / search grounded",
}

DECISION_VALUES: tuple[str, ...] = (
    "trivial",
    "low",
    "medium",
    "high",
    "critical",
)

DECISION_VALUE_LABELS: dict[str, str] = {
    "trivial": "Trivial (cosmetic / copy tweak)",
    "low": "Low (local page fix)",
    "medium": "Medium (topic / cluster decision)",
    "high": "High (visibility / competitive move)",
    "critical": "Critical (executive / strategy bet)",
}

WORKFLOW_INTENTS: tuple[str, ...] = (
    "page_title_recommendation",
    "meta_description",
    "simple_seo_check",
    "share_of_answer_lookup",
    "citation_lookup",
    "content_brief",
    "writer_assignment",
    "entity_gap_analysis",
    "competitor_response",
    "geo_strategy",
    "executive_brief",
    "research_hypothesis",
    "council_strategy",
    "custom",
)

# Max method kind allowed per decision value (cheapest-first ladder)
VALUE_METHOD_CEILING: dict[str, str] = {
    "trivial": "deterministic",
    "low": "single_llm",
    "medium": "multi_llm",
    "high": "council",
    "critical": "lab_experiment",
}

METHOD_LADDER: tuple[str, ...] = (
    "deterministic",
    "web_search",
    "single_llm",
    "multi_llm",
    "council",
    "lab_experiment",
)

METHODOLOGY = "peacock_intelligence_budget_engine_v1"
METHODOLOGY_NOTE = (
    "Intelligence Budget Engine estimates expected calls, tokens, searches, "
    "runtime, and USD cost before deep workflows. PINE selects the cheapest "
    "reliable method for the decision value — deterministic first, expensive "
    "multi-model reasoning only for high-value decisions."
)
COST_POSITIONING = (
    "Because Peacock uses multiple models, searches, and repeated experiments, "
    "cost control is critical. The Intelligence Budget Engine is Peacock Cost "
    "Intelligence: pre-flight estimates plus cheapest-reliable method choice."
)
CHEAPEST_RELIABLE_POLICY = (
    "Do NOT use five LLMs if deterministic data can answer the question. "
    "Do NOT run Council mode for a simple page-title recommendation. "
    "Reserve expensive reasoning for high-value decisions."
)


class IntelligenceBudgetEstimate(Base, WorkspaceTenantMixin):
    """One pre-flight cost / method selection estimate."""

    __tablename__ = "intelligence_budget_estimates"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_brand: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    workflow_intent: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    decision_value: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    selected_method_kind: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    selected_method_label: Mapped[str] = mapped_column(String(255), nullable=False)
    selected_peacock_mode: Mapped[str | None] = mapped_column(String(64), index=True)
    selection_rationale: Mapped[str] = mapped_column(Text, nullable=False)
    rejected_expensive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    expected_calls: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_searches: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_runtime_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    expected_cost_usd_micros: Mapped[int] = mapped_column(Integer, nullable=False)
    candidates_count: Mapped[int] = mapped_column(Integer, nullable=False)
    methodology: Mapped[str] = mapped_column(String(64), default=METHODOLOGY, nullable=False)
    cost_positioning: Mapped[str] = mapped_column(Text, nullable=False)
    policy_note: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    analysed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    notes: Mapped[str | None] = mapped_column(Text)

    candidates: Mapped[list[IbeMethodCandidate]] = relationship(
        back_populates="estimate", cascade="all, delete-orphan", passive_deletes=True
    )


class IbeMethodCandidate(Base, WorkspaceTenantMixin):
    """A method option evaluated for an estimate."""

    __tablename__ = "ibe_method_candidates"
    __table_args__ = (UniqueConstraint("estimate_id", "method_kind"),)

    estimate_id: Mapped[str] = mapped_column(
        ForeignKey("intelligence_budget_estimates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    method_kind: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    method_label: Mapped[str] = mapped_column(String(255), nullable=False)
    peacock_mode: Mapped[str | None] = mapped_column(String(64))
    reliable_enough: Mapped[bool] = mapped_column(Boolean, nullable=False)
    allowed_for_value: Mapped[bool] = mapped_column(Boolean, nullable=False)
    selected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    expected_calls: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_searches: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_runtime_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    expected_cost_usd_micros: Mapped[int] = mapped_column(Integer, nullable=False)
    reliability_score: Mapped[float] = mapped_column(Float, nullable=False)
    cost_efficiency_score: Mapped[float] = mapped_column(Float, nullable=False)
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    rank_order: Mapped[int] = mapped_column(Integer, nullable=False)

    estimate: Mapped[IntelligenceBudgetEstimate] = relationship(back_populates="candidates")
