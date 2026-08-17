"""Strongly typed PINE IntelligenceCase aggregate.

This is the runtime contract used by Peacock Intelligence (PINE).
Persistence is relational via ``IntelligenceCaseRecord`` and child tables —
not a single JSON blob.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Literal


@dataclass(slots=True)
class CaseContextItem:
    kind: str
    key: str
    summary: str
    relevance: float
    tokens_estimate: int
    source: str
    id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CaseObservation:
    code: str
    label: str
    detail: str
    source: str
    observed_at: datetime | None = None
    id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if self.observed_at is not None:
            payload["observed_at"] = self.observed_at.isoformat()
        return payload


@dataclass(slots=True)
class CaseEvidence:
    code: str
    label: str
    kind: Literal["deterministic", "research", "llm_inference"]
    source: str
    confidence: float
    value_text: str | None = None
    value_number: float | None = None
    value_bool: bool | None = None
    unit: str | None = None
    related_urls: list[str] = field(default_factory=list)
    id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CaseHypothesis:
    statement: str
    confidence: float
    status_label: str = "open"
    supporting_evidence_codes: list[str] = field(default_factory=list)
    id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CaseAgentFinding:
    agent_name: str
    role: str
    summary: str
    confidence: float
    claims: list[str] = field(default_factory=list)
    is_llm_derived: bool = True
    id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CaseContradiction:
    claim: str
    challenge: str
    severity: Literal["low", "medium", "high"]
    unresolved: bool = True
    id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CaseUnknown:
    question: str
    impact_if_unknown: str | None = None
    suggested_investigation: str | None = None
    id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CaseAssumption:
    statement: str
    confidence: float = 0.5
    risk_if_wrong: str | None = None
    id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CaseRisk:
    title: str
    description: str
    severity: Literal["low", "medium", "high", "critical"]
    likelihood: Literal["low", "medium", "high"] = "medium"
    id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CaseOpportunity:
    title: str
    description: str
    impact: float = 0.0
    effort: float = 0.0
    id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CaseRecommendation:
    title: str
    rationale: str
    priority: Literal["critical", "high", "medium", "low"]
    impact: float
    effort: float
    confidence: float
    priority_score: float = 0.0
    evidence_refs: list[str] = field(default_factory=list)
    depends_on_inference: bool = False
    suggested_fix: str | None = None
    id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CaseModelUsed:
    provider_code: str
    model_code: str
    role: str
    request_count: int = 1
    cost_usd_micros: int = 0
    latency_ms: int = 0
    id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CaseToolUsed:
    tool_name: str
    tool_version: str | None = None
    purpose: str | None = None
    invocation_count: int = 1
    latency_ms: int = 0
    id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class IntelligenceCase:
    """PINE strongly typed intelligence case.

    ``organization_id`` is an alias of ``organisation_id`` for product vocabulary.
    Collections are typed lists — never an opaque JSON document.
    """

    case_id: str
    organisation_id: str
    workspace_id: str
    objective: str
    confidence: float = 0.0
    cost_usd_micros: int = 0
    latency_ms: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None
    status: str = "active"
    title: str | None = None
    website_id: str | None = None
    strategic_run_id: str | None = None

    context: list[CaseContextItem] = field(default_factory=list)
    observations: list[CaseObservation] = field(default_factory=list)
    evidence: list[CaseEvidence] = field(default_factory=list)
    hypotheses: list[CaseHypothesis] = field(default_factory=list)
    agent_findings: list[CaseAgentFinding] = field(default_factory=list)
    contradictions: list[CaseContradiction] = field(default_factory=list)
    unknowns: list[CaseUnknown] = field(default_factory=list)
    assumptions: list[CaseAssumption] = field(default_factory=list)
    risks: list[CaseRisk] = field(default_factory=list)
    opportunities: list[CaseOpportunity] = field(default_factory=list)
    recommendations: list[CaseRecommendation] = field(default_factory=list)
    models_used: list[CaseModelUsed] = field(default_factory=list)
    tools_used: list[CaseToolUsed] = field(default_factory=list)

    @property
    def organization_id(self) -> str:
        return self.organisation_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "organization_id": self.organization_id,
            "organisation_id": self.organisation_id,
            "workspace_id": self.workspace_id,
            "objective": self.objective,
            "title": self.title,
            "confidence": self.confidence,
            "cost": {"usd_micros": self.cost_usd_micros},
            "latency": {"ms": self.latency_ms},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "status": self.status,
            "website_id": self.website_id,
            "strategic_run_id": self.strategic_run_id,
            "context": [item.to_dict() for item in self.context],
            "observations": [item.to_dict() for item in self.observations],
            "evidence": [item.to_dict() for item in self.evidence],
            "hypotheses": [item.to_dict() for item in self.hypotheses],
            "agent_findings": [item.to_dict() for item in self.agent_findings],
            "contradictions": [item.to_dict() for item in self.contradictions],
            "unknowns": [item.to_dict() for item in self.unknowns],
            "assumptions": [item.to_dict() for item in self.assumptions],
            "risks": [item.to_dict() for item in self.risks],
            "opportunities": [item.to_dict() for item in self.opportunities],
            "recommendations": [item.to_dict() for item in self.recommendations],
            "models_used": [item.to_dict() for item in self.models_used],
            "tools_used": [item.to_dict() for item in self.tools_used],
        }
