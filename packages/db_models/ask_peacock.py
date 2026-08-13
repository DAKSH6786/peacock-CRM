"""Ask Peacock 2.0 — natural-language interface over the intelligence graph.

Answers are structured into OBSERVED / INFERRED / RECOMMENDED / FORECAST /
CONFIDENCE and always include evidence citations into graph surfaces.
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


ANSWER_SECTIONS: tuple[str, ...] = (
    "OBSERVED",
    "INFERRED",
    "RECOMMENDED",
    "FORECAST",
    "CONFIDENCE",
)

QUERY_INTENTS: tuple[str, ...] = (
    "competitor_beating_us",
    "budget_allocation_90d",
    "top_geo_pages",
    "writer_for_topic",
    "weakest_generative_engine",
    "external_sources_influencing",
    "what_changed_week",
    "ceo_brief",
    "custom",
)

INTENT_LABELS: dict[str, str] = {
    "competitor_beating_us": "Why is a competitor beating us?",
    "budget_allocation_90d": "How should we allocate budget over 90 days?",
    "top_geo_pages": "Which pages offer the highest GEO improvement?",
    "writer_for_topic": "Which writer should cover a topic?",
    "weakest_generative_engine": "Where is our weakest generative engine?",
    "external_sources_influencing": "What external sources influence AI opinions?",
    "what_changed_week": "What changed this week?",
    "ceo_brief": "What should the CEO know?",
    "custom": "Custom intelligence-graph question",
}

EXAMPLE_QUESTIONS: tuple[str, ...] = (
    "Why is Competitor A beating us?",
    "What should we do with ₹10 lakh over the next 90 days?",
    "Which ten pages could generate the highest GEO improvement?",
    "Which writer should write Topic X?",
    "Where is our weakest generative engine?",
    "What external sources are influencing AI opinions about us?",
    "What changed this week?",
    "What should the CEO know?",
)

# Surfaces across the Peacock intelligence graph that Ask Peacock can cite
GRAPH_SURFACES: tuple[str, ...] = (
    "deep_competitor",
    "share_of_answer",
    "citation_graph",
    "entity_intelligence",
    "retrieval_pathway",
    "opportunity_engine",
    "peacock90",
    "writer_intelligence",
    "temporal_intelligence",
    "anomaly_engine",
    "scenario_engine",
    "revenue_attribution",
    "content_lab",
    "geo_lab",
    "agentic_readiness",
    "learning_engine2",
    "judge2",
    "council2",
    "action_engine",
)

METHODOLOGY = "ask_peacock_2_structured_graph_answers"
METHODOLOGY_NOTE = (
    "Ask Peacock 2.0 is the natural-language interface over the Peacock "
    "intelligence graph. Every answer is structured into OBSERVED, INFERRED, "
    "RECOMMENDED, FORECAST, and CONFIDENCE, and cites evidence from graph "
    "surfaces. Inferences are not presented as certainty; confidence reflects "
    "evidence coverage and signal agreement."
)


class AskPeacockSession(Base, WorkspaceTenantMixin):
    """One Ask Peacock 2.0 Q&A session over the intelligence graph."""

    __tablename__ = "ask_peacock_sessions"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_brand: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    session_status: Mapped[str] = mapped_column(
        String(32), default="completed", nullable=False, index=True
    )
    methodology: Mapped[str] = mapped_column(String(64), default=METHODOLOGY, nullable=False)
    questions_asked: Mapped[int] = mapped_column(Integer, nullable=False)
    answers_produced: Mapped[int] = mapped_column(Integer, nullable=False)
    evidence_items: Mapped[int] = mapped_column(Integer, nullable=False)
    mean_confidence: Mapped[float | None] = mapped_column(Float)
    primary_intent: Mapped[str | None] = mapped_column(String(64), index=True)
    summary: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)

    answers: Mapped[list[ApAnswer]] = relationship(
        back_populates="session", cascade="all, delete-orphan", passive_deletes=True
    )


class ApAnswer(Base, WorkspaceTenantMixin):
    """Structured Ask Peacock answer for one natural-language question."""

    __tablename__ = "ap_answers"
    __table_args__ = (UniqueConstraint("session_id", "question_index"),)

    session_id: Mapped[str] = mapped_column(
        ForeignKey("ask_peacock_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_index: Mapped[int] = mapped_column(Integer, nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    intent_label: Mapped[str] = mapped_column(String(255), nullable=False)
    observed: Mapped[str] = mapped_column(Text, nullable=False)
    inferred: Mapped[str] = mapped_column(Text, nullable=False)
    recommended: Mapped[str] = mapped_column(Text, nullable=False)
    forecast: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    confidence_rationale: Mapped[str] = mapped_column(Text, nullable=False)
    graph_surfaces_used: Mapped[str] = mapped_column(Text, nullable=False)
    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )

    session: Mapped[AskPeacockSession] = relationship(back_populates="answers")
    evidence: Mapped[list[ApEvidence]] = relationship(
        back_populates="answer", cascade="all, delete-orphan", passive_deletes=True
    )


class ApEvidence(Base, WorkspaceTenantMixin):
    """Evidence citation linking an answer to an intelligence-graph surface."""

    __tablename__ = "ap_evidence"
    __table_args__ = (
        UniqueConstraint("answer_id", "evidence_index", name="uq_ap_evidence_answer_idx"),
    )

    answer_id: Mapped[str] = mapped_column(
        ForeignKey("ap_answers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    evidence_index: Mapped[int] = mapped_column(Integer, nullable=False)
    graph_surface: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    claim: Mapped[str] = mapped_column(Text, nullable=False)
    ref_id: Mapped[str | None] = mapped_column(String(128))
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    section: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    answer: Mapped[ApAnswer] = relationship(back_populates="evidence")
