"""Peacock Council 2.0 — multi-model opposing-role debate for major decisions.

Never asks «What do you think?». Assigns opposing roles. Stores only structured
artifacts: claim, evidence, counterargument, confidence, decision.
Never persists hidden chain-of-thought.
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


# Opposing council roles — not open-ended opinion prompts
COUNCIL_ROLES: tuple[str, ...] = (
    "seo_researcher",
    "geo_researcher",
    "business_strategist",
    "competitor_analyst",
    "evidence_reviewer",
    "sceptic",
    "risk_analyst",
)

ROLE_MANDATES: dict[str, str] = {
    "seo_researcher": (
        "Argue from classic search demand, rankability, and technical SEO evidence. "
        "Do not give generic opinions."
    ),
    "geo_researcher": (
        "Argue from generative-engine visibility, citability, and answer prominence. "
        "Do not give generic opinions."
    ),
    "business_strategist": (
        "Argue from commercial upside, ICP fit, and resource trade-offs. "
        "Do not give generic opinions."
    ),
    "competitor_analyst": (
        "Argue from rival positioning, gaps, and competitive risk. "
        "Do not give generic opinions."
    ),
    "evidence_reviewer": (
        "Stress-test claims against available evidence quality and provenance. "
        "Do not give generic opinions."
    ),
    "sceptic": (
        "Challenge weak assumptions, overclaiming, and unsupported causality. "
        "Do not give generic opinions."
    ),
    "risk_analyst": (
        "Surface downside, brand/legal/operational risks, and failure modes. "
        "Do not give generic opinions."
    ),
}

# Explicitly forbidden prompt style
FORBIDDEN_PROMPTS: tuple[str, ...] = (
    "What do you think?",
    "what do you think",
    "Any thoughts?",
    "any thoughts?",
)

DEBATE_ROUNDS: tuple[tuple[int, str, str], ...] = (
    (1, "independent_analysis", "Independent analysis"),
    (2, "cross_summary_response", "Each agent receives structured summaries from others"),
    (3, "identify_disagreements", "Identify disagreements"),
    (4, "evidence_for_disputes", "Request evidence specifically for disputed claims"),
    (5, "judge", "Judge"),
)

# Only these artifact kinds may be stored / returned
STORED_ARTIFACT_KINDS: tuple[str, ...] = (
    "claim",
    "evidence",
    "counterargument",
    "confidence",
    "decision",
)

# Explicitly never stored
FORBIDDEN_STORAGE_FIELDS: tuple[str, ...] = (
    "chain_of_thought",
    "hidden_chain_of_thought",
    "reasoning_trace",
    "thinking",
    "private_scratchpad",
    "raw_logits",
)

METHODOLOGY = "peacock_council_2_opposing_role_debate"

METHODOLOGY_NOTE = (
    "Peacock Council 2.0 uses multiple models with opposing assigned roles for major "
    "decisions. It never asks «What do you think?». Debate protocol: (1) independent "
    "analysis, (2) structured cross-summaries, (3) identify disagreements, (4) evidence "
    "for disputed claims, (5) judge. Only claim, evidence, counterargument, confidence, "
    "and decision are stored — never hidden chain-of-thought."
)


class Council2Session(Base, WorkspaceTenantMixin):
    """A Peacock Council 2.0 major-decision debate session."""

    __tablename__ = "council2_sessions"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_brand: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    decision_question: Mapped[str] = mapped_column(Text, nullable=False)
    context_summary: Mapped[str | None] = mapped_column(Text)
    session_status: Mapped[str] = mapped_column(
        String(32), default="completed", nullable=False, index=True
    )
    methodology: Mapped[str] = mapped_column(
        String(64), default=METHODOLOGY, nullable=False
    )
    open_opinion_prompts_rejected: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    chain_of_thought_not_stored: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    stored_artifact_kinds: Mapped[str] = mapped_column(Text, nullable=False)
    round_count: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    final_decision_text: Mapped[str | None] = mapped_column(Text)
    final_confidence: Mapped[float | None] = mapped_column(Float)
    summary: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)

    agents: Mapped[list[C2Agent]] = relationship(
        back_populates="session", cascade="all, delete-orphan", passive_deletes=True
    )
    round_records: Mapped[list[C2RoundRecord]] = relationship(
        back_populates="session", cascade="all, delete-orphan", passive_deletes=True
    )
    claims: Mapped[list[C2Claim]] = relationship(
        back_populates="session", cascade="all, delete-orphan", passive_deletes=True
    )
    evidence_items: Mapped[list[C2Evidence]] = relationship(
        back_populates="session", cascade="all, delete-orphan", passive_deletes=True
    )
    counterarguments: Mapped[list[C2Counterargument]] = relationship(
        back_populates="session", cascade="all, delete-orphan", passive_deletes=True
    )
    disagreements: Mapped[list[C2Disagreement]] = relationship(
        back_populates="session", cascade="all, delete-orphan", passive_deletes=True
    )
    evidence_requests: Mapped[list[C2EvidenceRequest]] = relationship(
        back_populates="session", cascade="all, delete-orphan", passive_deletes=True
    )
    decisions: Mapped[list[C2Decision]] = relationship(
        back_populates="session", cascade="all, delete-orphan", passive_deletes=True
    )


class C2Agent(Base, WorkspaceTenantMixin):
    """Opposing-role agent assignment (never open opinion prompt)."""

    __tablename__ = "c2_agents"
    __table_args__ = (UniqueConstraint("session_id", "role_code"),)

    session_id: Mapped[str] = mapped_column(
        ForeignKey("council2_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    role_mandate: Mapped[str] = mapped_column(Text, nullable=False)
    model_label: Mapped[str] = mapped_column(String(128), nullable=False)
    open_opinion_prompt_rejected: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    session: Mapped[Council2Session] = relationship(back_populates="agents")


class C2RoundRecord(Base, WorkspaceTenantMixin):
    """Debate round marker — protocol step only, no CoT."""

    __tablename__ = "c2_round_records"
    __table_args__ = (UniqueConstraint("session_id", "round_number"),)

    session_id: Mapped[str] = mapped_column(
        ForeignKey("council2_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    round_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    round_label: Mapped[str] = mapped_column(String(255), nullable=False)
    structured_summary: Mapped[str] = mapped_column(Text, nullable=False)

    session: Mapped[Council2Session] = relationship(back_populates="round_records")


class C2Claim(Base, WorkspaceTenantMixin):
    """Structured claim artifact (stored)."""

    __tablename__ = "c2_claims"

    session_id: Mapped[str] = mapped_column(
        ForeignKey("council2_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    claim_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    role_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    stance: Mapped[str] = mapped_column(String(32), nullable=False)  # support|oppose|conditional

    session: Mapped[Council2Session] = relationship(back_populates="claims")


class C2Evidence(Base, WorkspaceTenantMixin):
    """Structured evidence artifact (stored)."""

    __tablename__ = "c2_evidence"

    session_id: Mapped[str] = mapped_column(
        ForeignKey("council2_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    claim_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    role_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    source_ref: Mapped[str | None] = mapped_column(String(512))
    strength: Mapped[float] = mapped_column(Float, nullable=False)

    session: Mapped[Council2Session] = relationship(back_populates="evidence_items")


class C2Counterargument(Base, WorkspaceTenantMixin):
    """Structured counterargument artifact (stored)."""

    __tablename__ = "c2_counterarguments"

    session_id: Mapped[str] = mapped_column(
        ForeignKey("council2_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    claim_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    role_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    session: Mapped[Council2Session] = relationship(back_populates="counterarguments")


class C2Disagreement(Base, WorkspaceTenantMixin):
    """Round-3 disagreement between roles on a claim."""

    __tablename__ = "c2_disagreements"

    session_id: Mapped[str] = mapped_column(
        ForeignKey("council2_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    claim_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    role_a: Mapped[str] = mapped_column(String(64), nullable=False)
    role_b: Mapped[str] = mapped_column(String(64), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[float] = mapped_column(Float, nullable=False)

    session: Mapped[Council2Session] = relationship(back_populates="disagreements")


class C2EvidenceRequest(Base, WorkspaceTenantMixin):
    """Round-4 request for evidence on a disputed claim."""

    __tablename__ = "c2_evidence_requests"

    session_id: Mapped[str] = mapped_column(
        ForeignKey("council2_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    claim_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    requested_by_role: Mapped[str] = mapped_column(String(64), nullable=False)
    request_statement: Mapped[str] = mapped_column(Text, nullable=False)
    fulfilled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fulfillment_evidence: Mapped[str | None] = mapped_column(Text)

    session: Mapped[Council2Session] = relationship(back_populates="evidence_requests")


class C2Decision(Base, WorkspaceTenantMixin):
    """Round-5 judge decision artifact (stored)."""

    __tablename__ = "c2_decisions"

    session_id: Mapped[str] = mapped_column(
        ForeignKey("council2_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    decision: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    supporting_claim_keys: Mapped[str] = mapped_column(Text, nullable=False)
    rejected_claim_keys: Mapped[str] = mapped_column(Text, nullable=False)
    judge_role: Mapped[str] = mapped_column(
        String(64), default="council_judge", nullable=False
    )

    session: Mapped[Council2Session] = relationship(back_populates="decisions")
