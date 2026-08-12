"""Peacock One Evidence Ledger — relational evidence graph.

Chain: Evidence → Finding → Recommendation → Action → Outcome

Distinct from the lightweight ``evidences`` explainability table and from
PINE ``intelligence_case_evidence`` case slices. This ledger is the
cross-product provenance spine.
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

# Evidence type codes (persisted as String; validated in the service layer)
EVIDENCE_TYPES = (
    "CRAWL",
    "SERP",
    "ANALYTICS",
    "SEARCH_CONSOLE",
    "BACKLINK",
    "AI_RESPONSE",
    "COMPETITOR_PAGE",
    "USER_DATA",
    "MODEL_INFERENCE",
    "EXTERNAL_SOURCE",
    "HISTORICAL_OUTCOME",
    "EXPERIMENT",
)


class LedgerEvidence(Base, WorkspaceTenantMixin):
    """A single evidence node in the Peacock Evidence Ledger."""

    __tablename__ = "ledger_evidences"

    code: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    evidence_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    # When the underlying observation was made
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    # Freshness: hours since observation at write/refresh + normalised score 0–1
    freshness_hours: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    freshness_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    # What the evidence applies to (page, site, keyword, market, …)
    scope_kind: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    scope_ref: Mapped[str] = mapped_column(String(1024), nullable=False)
    # Typed supporting value — not a JSON bag
    value_text: Mapped[str | None] = mapped_column(Text)
    value_number: Mapped[float | None] = mapped_column(Float)
    value_bool: Mapped[bool | None] = mapped_column(Boolean)
    value_unit: Mapped[str | None] = mapped_column(String(64))
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(2048))
    website_id: Mapped[str | None] = mapped_column(
        ForeignKey("websites.id", ondelete="SET NULL"), nullable=True, index=True
    )
    crawl_id: Mapped[str | None] = mapped_column(
        ForeignKey("crawls.id", ondelete="SET NULL"), nullable=True, index=True
    )
    intelligence_case_id: Mapped[str | None] = mapped_column(
        ForeignKey("intelligence_cases.id", ondelete="SET NULL"), nullable=True, index=True
    )

    finding_links: Mapped[list[LedgerEvidenceFindingLink]] = relationship(
        back_populates="evidence", cascade="all, delete-orphan", passive_deletes=True
    )
    claim_links: Mapped[list[LedgerClaimEvidenceLink]] = relationship(
        back_populates="evidence", cascade="all, delete-orphan", passive_deletes=True
    )


class LedgerFinding(Base, WorkspaceTenantMixin):
    """A finding / claim node supported by one or more evidence rows."""

    __tablename__ = "ledger_findings"

    code: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    finding_kind: Mapped[str] = mapped_column(String(64), default="insight", nullable=False, index=True)
    agent_name: Mapped[str | None] = mapped_column(String(128), index=True)
    is_llm_derived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    severity: Mapped[str | None] = mapped_column(String(16), index=True)
    website_id: Mapped[str | None] = mapped_column(
        ForeignKey("websites.id", ondelete="SET NULL"), nullable=True, index=True
    )
    intelligence_case_id: Mapped[str | None] = mapped_column(
        ForeignKey("intelligence_cases.id", ondelete="SET NULL"), nullable=True, index=True
    )

    evidence_links: Mapped[list[LedgerEvidenceFindingLink]] = relationship(
        back_populates="finding", cascade="all, delete-orphan", passive_deletes=True
    )
    recommendation_links: Mapped[list[LedgerFindingRecommendationLink]] = relationship(
        back_populates="finding", cascade="all, delete-orphan", passive_deletes=True
    )


class LedgerRecommendation(Base, WorkspaceTenantMixin):
    """Recommendation node in the evidence graph (optionally bridges to learning)."""

    __tablename__ = "ledger_recommendations"

    code: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(16), default="medium", nullable=False, index=True)
    impact: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    effort: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    priority_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    suggested_fix: Mapped[str | None] = mapped_column(Text)
    website_id: Mapped[str | None] = mapped_column(
        ForeignKey("websites.id", ondelete="SET NULL"), nullable=True, index=True
    )
    central_recommendation_id: Mapped[str | None] = mapped_column(
        ForeignKey("recommendations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    intelligence_case_id: Mapped[str | None] = mapped_column(
        ForeignKey("intelligence_cases.id", ondelete="SET NULL"), nullable=True, index=True
    )

    finding_links: Mapped[list[LedgerFindingRecommendationLink]] = relationship(
        back_populates="recommendation", cascade="all, delete-orphan", passive_deletes=True
    )
    action_links: Mapped[list[LedgerRecommendationActionLink]] = relationship(
        back_populates="recommendation", cascade="all, delete-orphan", passive_deletes=True
    )


class LedgerAction(Base, WorkspaceTenantMixin):
    """Executable action derived from a recommendation."""

    __tablename__ = "ledger_actions"

    code: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    owner_role: Mapped[str | None] = mapped_column(String(64))
    success_metric: Mapped[str | None] = mapped_column(String(255))
    action_status: Mapped[str] = mapped_column(String(32), default="planned", nullable=False, index=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    website_id: Mapped[str | None] = mapped_column(
        ForeignKey("websites.id", ondelete="SET NULL"), nullable=True, index=True
    )
    roadmap_task_id: Mapped[str | None] = mapped_column(
        ForeignKey("roadmap_tasks.id", ondelete="SET NULL"), nullable=True, index=True
    )
    execution_id: Mapped[str | None] = mapped_column(
        ForeignKey("recommendation_executions.id", ondelete="SET NULL"), nullable=True, index=True
    )

    recommendation_links: Mapped[list[LedgerRecommendationActionLink]] = relationship(
        back_populates="action", cascade="all, delete-orphan", passive_deletes=True
    )
    outcome_links: Mapped[list[LedgerActionOutcomeLink]] = relationship(
        back_populates="action", cascade="all, delete-orphan", passive_deletes=True
    )


class LedgerOutcome(Base, WorkspaceTenantMixin):
    """Measured outcome closing the evidence → action loop."""

    __tablename__ = "ledger_outcomes"

    code: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    metric_key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    baseline_value: Mapped[float | None] = mapped_column(Float)
    target_value: Mapped[float | None] = mapped_column(Float)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    outcome_kind: Mapped[str] = mapped_column(String(64), default="measured", nullable=False, index=True)
    website_id: Mapped[str | None] = mapped_column(
        ForeignKey("websites.id", ondelete="SET NULL"), nullable=True, index=True
    )
    central_outcome_id: Mapped[str | None] = mapped_column(
        ForeignKey("recommendation_outcomes.id", ondelete="SET NULL"), nullable=True, index=True
    )

    action_links: Mapped[list[LedgerActionOutcomeLink]] = relationship(
        back_populates="outcome", cascade="all, delete-orphan", passive_deletes=True
    )


# ---------------------------------------------------------------------------
# Graph edges: Evidence → Finding → Recommendation → Action → Outcome
# ---------------------------------------------------------------------------


class LedgerEvidenceFindingLink(Base, TimestampMixin):
    __tablename__ = "ledger_evidence_finding_links"
    __table_args__ = (UniqueConstraint("evidence_id", "finding_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    organisation_id: Mapped[str] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    evidence_id: Mapped[str] = mapped_column(
        ForeignKey("ledger_evidences.id", ondelete="CASCADE"), nullable=False, index=True
    )
    finding_id: Mapped[str] = mapped_column(
        ForeignKey("ledger_findings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(32), default="supports", nullable=False, index=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)

    evidence: Mapped[LedgerEvidence] = relationship(back_populates="finding_links")
    finding: Mapped[LedgerFinding] = relationship(back_populates="evidence_links")


class LedgerFindingRecommendationLink(Base, TimestampMixin):
    __tablename__ = "ledger_finding_recommendation_links"
    __table_args__ = (UniqueConstraint("finding_id", "recommendation_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    organisation_id: Mapped[str] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    finding_id: Mapped[str] = mapped_column(
        ForeignKey("ledger_findings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recommendation_id: Mapped[str] = mapped_column(
        ForeignKey("ledger_recommendations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(32), default="motivates", nullable=False, index=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)

    finding: Mapped[LedgerFinding] = relationship(back_populates="recommendation_links")
    recommendation: Mapped[LedgerRecommendation] = relationship(back_populates="finding_links")


class LedgerRecommendationActionLink(Base, TimestampMixin):
    __tablename__ = "ledger_recommendation_action_links"
    __table_args__ = (UniqueConstraint("recommendation_id", "action_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    organisation_id: Mapped[str] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recommendation_id: Mapped[str] = mapped_column(
        ForeignKey("ledger_recommendations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action_id: Mapped[str] = mapped_column(
        ForeignKey("ledger_actions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(32), default="implements", nullable=False, index=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)

    recommendation: Mapped[LedgerRecommendation] = relationship(back_populates="action_links")
    action: Mapped[LedgerAction] = relationship(back_populates="recommendation_links")


class LedgerActionOutcomeLink(Base, TimestampMixin):
    __tablename__ = "ledger_action_outcome_links"
    __table_args__ = (UniqueConstraint("action_id", "outcome_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    organisation_id: Mapped[str] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action_id: Mapped[str] = mapped_column(
        ForeignKey("ledger_actions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    outcome_id: Mapped[str] = mapped_column(
        ForeignKey("ledger_outcomes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(32), default="measures", nullable=False, index=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)

    action: Mapped[LedgerAction] = relationship(back_populates="outcome_links")
    outcome: Mapped[LedgerOutcome] = relationship(back_populates="action_links")


class LedgerClaimEvidenceLink(Base, TimestampMixin):
    """Optional pointer from any meaningful claim to ledger evidence.

    ``claim_kind`` + ``claim_ref`` identify the producer (agent claim, audit
    issue, hypothesis code, SEO finding id, …) without forcing every domain
    table to take an evidence FK.
    """

    __tablename__ = "ledger_claim_evidence_links"
    __table_args__ = (UniqueConstraint("claim_kind", "claim_ref", "evidence_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    organisation_id: Mapped[str] = mapped_column(
        ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    claim_kind: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    claim_ref: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    claim_text: Mapped[str | None] = mapped_column(Text)
    evidence_id: Mapped[str] = mapped_column(
        ForeignKey("ledger_evidences.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(32), default="supports", nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)

    evidence: Mapped[LedgerEvidence] = relationship(back_populates="claim_links")
