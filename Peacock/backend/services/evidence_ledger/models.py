"""Peacock One Evidence Ledger — typed graph contract.

Evidence → Finding → Recommendation → Action → Outcome
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any, Literal


class EvidenceType(StrEnum):
    CRAWL = "CRAWL"
    SERP = "SERP"
    ANALYTICS = "ANALYTICS"
    SEARCH_CONSOLE = "SEARCH_CONSOLE"
    BACKLINK = "BACKLINK"
    AI_RESPONSE = "AI_RESPONSE"
    COMPETITOR_PAGE = "COMPETITOR_PAGE"
    USER_DATA = "USER_DATA"
    MODEL_INFERENCE = "MODEL_INFERENCE"
    EXTERNAL_SOURCE = "EXTERNAL_SOURCE"
    HISTORICAL_OUTCOME = "HISTORICAL_OUTCOME"
    EXPERIMENT = "EXPERIMENT"


LinkRole = Literal[
    "supports",
    "contradicts",
    "contextualises",
    "motivates",
    "implements",
    "measures",
]


@dataclass(slots=True)
class SupportingValue:
    """Typed scalar supporting value for an evidence node."""

    text: str | None = None
    number: float | None = None
    boolean: bool | None = None
    unit: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class LedgerEvidenceNode:
    evidence_type: EvidenceType | str
    source: str
    observed_at: datetime
    confidence: float
    scope_kind: str
    scope_ref: str
    summary: str
    code: str | None = None
    id: str | None = None
    freshness_hours: float = 0.0
    freshness_score: float = 1.0
    supporting_value: SupportingValue = field(default_factory=SupportingValue)
    source_url: str | None = None
    website_id: str | None = None
    crawl_id: str | None = None
    intelligence_case_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "evidence_type": str(self.evidence_type),
            "source": self.source,
            "timestamp": self.observed_at.isoformat() if self.observed_at else None,
            "freshness": {
                "hours": self.freshness_hours,
                "score": self.freshness_score,
            },
            "confidence": self.confidence,
            "scope": {"kind": self.scope_kind, "ref": self.scope_ref},
            "supporting_value": self.supporting_value.to_dict(),
            "summary": self.summary,
            "source_url": self.source_url,
            "website_id": self.website_id,
            "crawl_id": self.crawl_id,
            "intelligence_case_id": self.intelligence_case_id,
        }


@dataclass(slots=True)
class LedgerFindingNode:
    statement: str
    confidence: float
    code: str | None = None
    id: str | None = None
    summary: str | None = None
    finding_kind: str = "insight"
    agent_name: str | None = None
    is_llm_derived: bool = False
    severity: str | None = None
    website_id: str | None = None
    intelligence_case_id: str | None = None
    evidence_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "statement": self.statement,
            "summary": self.summary,
            "confidence": self.confidence,
            "finding_kind": self.finding_kind,
            "agent_name": self.agent_name,
            "is_llm_derived": self.is_llm_derived,
            "severity": self.severity,
            "website_id": self.website_id,
            "intelligence_case_id": self.intelligence_case_id,
            "evidence_ids": list(self.evidence_ids),
        }


@dataclass(slots=True)
class LedgerRecommendationNode:
    title: str
    rationale: str
    priority: str
    impact: float
    effort: float
    confidence: float
    code: str | None = None
    id: str | None = None
    priority_score: float = 0.0
    suggested_fix: str | None = None
    website_id: str | None = None
    central_recommendation_id: str | None = None
    intelligence_case_id: str | None = None
    finding_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "title": self.title,
            "rationale": self.rationale,
            "priority": self.priority,
            "impact": self.impact,
            "effort": self.effort,
            "confidence": self.confidence,
            "priority_score": self.priority_score,
            "suggested_fix": self.suggested_fix,
            "website_id": self.website_id,
            "central_recommendation_id": self.central_recommendation_id,
            "intelligence_case_id": self.intelligence_case_id,
            "finding_ids": list(self.finding_ids),
        }


@dataclass(slots=True)
class LedgerActionNode:
    title: str
    description: str
    code: str | None = None
    id: str | None = None
    owner_role: str | None = None
    success_metric: str | None = None
    action_status: str = "planned"
    due_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    website_id: str | None = None
    roadmap_task_id: str | None = None
    execution_id: str | None = None
    recommendation_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "title": self.title,
            "description": self.description,
            "owner_role": self.owner_role,
            "success_metric": self.success_metric,
            "action_status": self.action_status,
            "due_at": self.due_at.isoformat() if self.due_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "website_id": self.website_id,
            "roadmap_task_id": self.roadmap_task_id,
            "execution_id": self.execution_id,
            "recommendation_ids": list(self.recommendation_ids),
        }


@dataclass(slots=True)
class LedgerOutcomeNode:
    metric_key: str
    metric_value: float
    observed_at: datetime
    code: str | None = None
    id: str | None = None
    baseline_value: float | None = None
    target_value: float | None = None
    notes: str | None = None
    outcome_kind: str = "measured"
    website_id: str | None = None
    central_outcome_id: str | None = None
    action_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "metric_key": self.metric_key,
            "metric_value": self.metric_value,
            "baseline_value": self.baseline_value,
            "target_value": self.target_value,
            "observed_at": self.observed_at.isoformat() if self.observed_at else None,
            "notes": self.notes,
            "outcome_kind": self.outcome_kind,
            "website_id": self.website_id,
            "central_outcome_id": self.central_outcome_id,
            "action_ids": list(self.action_ids),
        }


@dataclass(slots=True)
class ClaimEvidencePointer:
    """Optional link from any Peacock claim to ledger evidence."""

    claim_kind: str
    claim_ref: str
    evidence_id: str
    claim_text: str | None = None
    role: str = "supports"
    confidence: float = 0.0
    id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class EvidenceGraphEdge:
    from_kind: Literal["evidence", "finding", "recommendation", "action", "outcome"]
    from_id: str
    to_kind: Literal["evidence", "finding", "recommendation", "action", "outcome"]
    to_id: str
    role: str
    weight: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class EvidenceGraph:
    """Full Evidence → Finding → Recommendation → Action → Outcome graph."""

    organisation_id: str
    workspace_id: str
    evidences: list[LedgerEvidenceNode] = field(default_factory=list)
    findings: list[LedgerFindingNode] = field(default_factory=list)
    recommendations: list[LedgerRecommendationNode] = field(default_factory=list)
    actions: list[LedgerActionNode] = field(default_factory=list)
    outcomes: list[LedgerOutcomeNode] = field(default_factory=list)
    edges: list[EvidenceGraphEdge] = field(default_factory=list)
    claim_pointers: list[ClaimEvidencePointer] = field(default_factory=list)

    @property
    def organization_id(self) -> str:
        return self.organisation_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "organization_id": self.organization_id,
            "organisation_id": self.organisation_id,
            "workspace_id": self.workspace_id,
            "evidences": [node.to_dict() for node in self.evidences],
            "findings": [node.to_dict() for node in self.findings],
            "recommendations": [node.to_dict() for node in self.recommendations],
            "actions": [node.to_dict() for node in self.actions],
            "outcomes": [node.to_dict() for node in self.outcomes],
            "edges": [edge.to_dict() for edge in self.edges],
            "claim_pointers": [ptr.to_dict() for ptr in self.claim_pointers],
            "chain": ["evidence", "finding", "recommendation", "action", "outcome"],
        }
