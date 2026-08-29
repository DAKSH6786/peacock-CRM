"""PINE IntelligenceCase — relational aggregate (no monolithic JSON blob).

British spelling ``organisation_id`` is canonical in persistence.
The typed runtime object also exposes ``organization_id`` as an alias.
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

from db_models.base import Base, TimestampMixin, WorkspaceTenantMixin, new_uuid


class IntelligenceCaseRecord(Base, WorkspaceTenantMixin):
    """Root case record for a PINE strategic intelligence run."""

    __tablename__ = "intelligence_cases"

    objective: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(String(255))
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    cost_usd_micros: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    website_id: Mapped[str | None] = mapped_column(
        ForeignKey("websites.id", ondelete="SET NULL"), nullable=True, index=True
    )
    strategic_run_id: Mapped[str | None] = mapped_column(String(36), index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    context_items: Mapped[list[IntelligenceCaseContextItem]] = relationship(
        back_populates="case", cascade="all, delete-orphan", passive_deletes=True
    )
    observations: Mapped[list[IntelligenceCaseObservation]] = relationship(
        back_populates="case", cascade="all, delete-orphan", passive_deletes=True
    )
    evidence_items: Mapped[list[IntelligenceCaseEvidence]] = relationship(
        back_populates="case", cascade="all, delete-orphan", passive_deletes=True
    )
    hypotheses: Mapped[list[IntelligenceCaseHypothesis]] = relationship(
        back_populates="case", cascade="all, delete-orphan", passive_deletes=True
    )
    agent_findings: Mapped[list[IntelligenceCaseAgentFinding]] = relationship(
        back_populates="case", cascade="all, delete-orphan", passive_deletes=True
    )
    contradictions: Mapped[list[IntelligenceCaseContradiction]] = relationship(
        back_populates="case", cascade="all, delete-orphan", passive_deletes=True
    )
    unknowns: Mapped[list[IntelligenceCaseUnknown]] = relationship(
        back_populates="case", cascade="all, delete-orphan", passive_deletes=True
    )
    assumptions: Mapped[list[IntelligenceCaseAssumption]] = relationship(
        back_populates="case", cascade="all, delete-orphan", passive_deletes=True
    )
    risks: Mapped[list[IntelligenceCaseRisk]] = relationship(
        back_populates="case", cascade="all, delete-orphan", passive_deletes=True
    )
    opportunities: Mapped[list[IntelligenceCaseOpportunity]] = relationship(
        back_populates="case", cascade="all, delete-orphan", passive_deletes=True
    )
    recommendations: Mapped[list[IntelligenceCaseRecommendation]] = relationship(
        back_populates="case", cascade="all, delete-orphan", passive_deletes=True
    )
    models_used: Mapped[list[IntelligenceCaseModelUsed]] = relationship(
        back_populates="case", cascade="all, delete-orphan", passive_deletes=True
    )
    tools_used: Mapped[list[IntelligenceCaseToolUsed]] = relationship(
        back_populates="case", cascade="all, delete-orphan", passive_deletes=True
    )


class _CaseChildMixin(TimestampMixin):
    """Shared fields for IntelligenceCase child rows."""

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    organisation_id: Mapped[str] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    case_id: Mapped[str] = mapped_column(
        ForeignKey("intelligence_cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=100, nullable=False)


class IntelligenceCaseContextItem(Base, _CaseChildMixin):
    __tablename__ = "intelligence_case_context_items"

    kind: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    key: Mapped[str] = mapped_column(String(128), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    relevance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    tokens_estimate: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    source: Mapped[str] = mapped_column(String(128), nullable=False)

    case: Mapped[IntelligenceCaseRecord] = relationship(back_populates="context_items")


class IntelligenceCaseObservation(Base, _CaseChildMixin):
    __tablename__ = "intelligence_case_observations"

    code: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(128), nullable=False)
    observed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    case: Mapped[IntelligenceCaseRecord] = relationship(back_populates="observations")


class IntelligenceCaseEvidence(Base, _CaseChildMixin):
    __tablename__ = "intelligence_case_evidence"

    code: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    # Typed scalar value — prefer typed columns over JSON bags
    value_text: Mapped[str | None] = mapped_column(Text)
    value_number: Mapped[float | None] = mapped_column(Float)
    value_bool: Mapped[bool | None] = mapped_column(Boolean)
    kind: Mapped[str] = mapped_column(String(32), nullable=False, index=True)  # deterministic|research|llm_inference
    source: Mapped[str] = mapped_column(String(128), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(64))

    case: Mapped[IntelligenceCaseRecord] = relationship(back_populates="evidence_items")
    related_urls: Mapped[list[IntelligenceCaseEvidenceUrl]] = relationship(
        back_populates="evidence", cascade="all, delete-orphan", passive_deletes=True
    )


class IntelligenceCaseEvidenceUrl(Base, TimestampMixin):
    __tablename__ = "intelligence_case_evidence_urls"
    __table_args__ = (UniqueConstraint("evidence_id", "url"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    organisation_id: Mapped[str] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    case_id: Mapped[str] = mapped_column(
        ForeignKey("intelligence_cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evidence_id: Mapped[str] = mapped_column(
        ForeignKey("intelligence_case_evidence.id", ondelete="CASCADE"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)

    evidence: Mapped[IntelligenceCaseEvidence] = relationship(back_populates="related_urls")


class IntelligenceCaseHypothesis(Base, _CaseChildMixin):
    __tablename__ = "intelligence_case_hypotheses"

    statement: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status_label: Mapped[str] = mapped_column(String(32), default="open", nullable=False, index=True)
    supporting_evidence_codes: Mapped[str | None] = mapped_column(Text)  # comma-separated codes

    case: Mapped[IntelligenceCaseRecord] = relationship(back_populates="hypotheses")


class IntelligenceCaseAgentFinding(Base, _CaseChildMixin):
    __tablename__ = "intelligence_case_agent_findings"

    agent_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_llm_derived: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    case: Mapped[IntelligenceCaseRecord] = relationship(back_populates="agent_findings")
    claims: Mapped[list[IntelligenceCaseAgentClaim]] = relationship(
        back_populates="finding", cascade="all, delete-orphan", passive_deletes=True
    )


class IntelligenceCaseAgentClaim(Base, TimestampMixin):
    __tablename__ = "intelligence_case_agent_claims"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    organisation_id: Mapped[str] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    case_id: Mapped[str] = mapped_column(
        ForeignKey("intelligence_cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    finding_id: Mapped[str] = mapped_column(
        ForeignKey("intelligence_case_agent_findings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    claim: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)

    finding: Mapped[IntelligenceCaseAgentFinding] = relationship(back_populates="claims")


class IntelligenceCaseContradiction(Base, _CaseChildMixin):
    __tablename__ = "intelligence_case_contradictions"

    claim: Mapped[str] = mapped_column(Text, nullable=False)
    challenge: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    unresolved: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    case: Mapped[IntelligenceCaseRecord] = relationship(back_populates="contradictions")


class IntelligenceCaseUnknown(Base, _CaseChildMixin):
    __tablename__ = "intelligence_case_unknowns"

    question: Mapped[str] = mapped_column(Text, nullable=False)
    impact_if_unknown: Mapped[str | None] = mapped_column(Text)
    suggested_investigation: Mapped[str | None] = mapped_column(Text)

    case: Mapped[IntelligenceCaseRecord] = relationship(back_populates="unknowns")


class IntelligenceCaseAssumption(Base, _CaseChildMixin):
    __tablename__ = "intelligence_case_assumptions"

    statement: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    risk_if_wrong: Mapped[str | None] = mapped_column(Text)

    case: Mapped[IntelligenceCaseRecord] = relationship(back_populates="assumptions")


class IntelligenceCaseRisk(Base, _CaseChildMixin):
    __tablename__ = "intelligence_case_risks"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    likelihood: Mapped[str] = mapped_column(String(16), default="medium", nullable=False)

    case: Mapped[IntelligenceCaseRecord] = relationship(back_populates="risks")


class IntelligenceCaseOpportunity(Base, _CaseChildMixin):
    __tablename__ = "intelligence_case_opportunities"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    impact: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    effort: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    case: Mapped[IntelligenceCaseRecord] = relationship(back_populates="opportunities")


class IntelligenceCaseRecommendation(Base, _CaseChildMixin):
    __tablename__ = "intelligence_case_recommendations"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    impact: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    effort: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    priority_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    depends_on_inference: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    suggested_fix: Mapped[str | None] = mapped_column(Text)
    # Optional link into central learning recommendations
    learning_recommendation_id: Mapped[str | None] = mapped_column(
        ForeignKey("recommendations.id", ondelete="SET NULL"), nullable=True, index=True
    )

    case: Mapped[IntelligenceCaseRecord] = relationship(back_populates="recommendations")
    evidence_refs: Mapped[list[IntelligenceCaseRecommendationEvidence]] = relationship(
        back_populates="recommendation", cascade="all, delete-orphan", passive_deletes=True
    )


class IntelligenceCaseRecommendationEvidence(Base, TimestampMixin):
    __tablename__ = "intelligence_case_recommendation_evidence"
    __table_args__ = (UniqueConstraint("recommendation_id", "evidence_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    organisation_id: Mapped[str] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    case_id: Mapped[str] = mapped_column(
        ForeignKey("intelligence_cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recommendation_id: Mapped[str] = mapped_column(
        ForeignKey("intelligence_case_recommendations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    evidence_code: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)

    recommendation: Mapped[IntelligenceCaseRecommendation] = relationship(back_populates="evidence_refs")


class IntelligenceCaseModelUsed(Base, _CaseChildMixin):
    __tablename__ = "intelligence_case_models_used"

    provider_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    model_code: Mapped[str] = mapped_column(String(128), nullable=False)
    role: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    request_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    cost_usd_micros: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    provider_id: Mapped[str | None] = mapped_column(
        ForeignKey("ai_providers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    model_id: Mapped[str | None] = mapped_column(
        ForeignKey("ai_provider_models.id", ondelete="SET NULL"), nullable=True, index=True
    )

    case: Mapped[IntelligenceCaseRecord] = relationship(back_populates="models_used")


class IntelligenceCaseToolUsed(Base, _CaseChildMixin):
    __tablename__ = "intelligence_case_tools_used"

    tool_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    tool_version: Mapped[str | None] = mapped_column(String(64))
    purpose: Mapped[str | None] = mapped_column(String(255))
    invocation_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    case: Mapped[IntelligenceCaseRecord] = relationship(back_populates="tools_used")
