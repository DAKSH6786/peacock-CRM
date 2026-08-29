"""Strategic intelligence pipeline models — Layers 0–10."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import IntEnum, StrEnum
from typing import Any, Literal


class StrategicLayer(IntEnum):
    REQUEST_CLASSIFICATION = 0
    CONTEXT_ASSEMBLY = 1
    DETERMINISTIC_EVIDENCE = 2
    RESEARCH = 3
    SPECIALIST_REASONING = 4
    ADVERSARIAL_ANALYSIS = 5
    VERIFICATION = 6
    DECISION = 7
    SIMULATION = 8
    EXECUTION_PLAN = 9
    LEARNING = 10


class ThinkingDepth(StrEnum):
    SHALLOW = "shallow"
    STANDARD = "standard"
    DEEP = "deep"
    COUNCIL = "council"
    LAB = "lab"


class EvidenceKind(StrEnum):
    DETERMINISTIC = "deterministic"
    RESEARCH = "research"
    LLM_INFERENCE = "llm_inference"


LAYER_NAMES: dict[StrategicLayer, str] = {
    StrategicLayer.REQUEST_CLASSIFICATION: "Request Classification",
    StrategicLayer.CONTEXT_ASSEMBLY: "Context Assembly",
    StrategicLayer.DETERMINISTIC_EVIDENCE: "Deterministic Evidence",
    StrategicLayer.RESEARCH: "Research",
    StrategicLayer.SPECIALIST_REASONING: "Specialist Reasoning",
    StrategicLayer.ADVERSARIAL_ANALYSIS: "Adversarial Analysis",
    StrategicLayer.VERIFICATION: "Verification",
    StrategicLayer.DECISION: "Decision",
    StrategicLayer.SIMULATION: "Simulation",
    StrategicLayer.EXECUTION_PLAN: "Execution Plan",
    StrategicLayer.LEARNING: "Learning",
}


@dataclass(slots=True)
class StrategicRequest:
    """Inbound strategic request to be decomposed across layers."""

    organisation_id: str
    workspace_id: str
    request_text: str
    website_id: str | None = None
    crawl_id: str | None = None
    audit_id: str | None = None
    requested_output: str | None = None
    # Explicit Peacock mode override (fast|standard|deep|council|lab or peacock_*)
    peacock_mode: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RequestClassification:
    """Layer 0 output."""

    user_intent: str
    requested_output: str
    importance: Literal["low", "medium", "high", "critical"]
    business_risk: Literal["low", "medium", "high", "critical"]
    freshness_requirement: Literal["stale_ok", "recent", "realtime"]
    required_data: list[str]
    thinking_depth: ThinkingDepth
    peacock_mode: str = "peacock_standard"
    mode_budget: dict[str, Any] = field(default_factory=dict)
    mode_capabilities: dict[str, Any] = field(default_factory=dict)
    intent_confidence: float = 0.0
    skip_layers: list[int] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["thinking_depth"] = self.thinking_depth.value
        return payload


@dataclass(slots=True)
class ContextItem:
    """One selected organisation context fragment — never a full-table dump."""

    kind: str
    key: str
    summary: str
    relevance: float
    tokens_estimate: int
    source: str
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ContextBundle:
    """Layer 1 output — budgeted, relevance-ranked context."""

    items: list[ContextItem]
    selected_kinds: list[str]
    rejected_kinds: list[str]
    token_budget: int
    tokens_used: int
    selection_rationale: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "items": [i.to_dict() for i in self.items],
            "selected_kinds": self.selected_kinds,
            "rejected_kinds": self.rejected_kinds,
            "token_budget": self.token_budget,
            "tokens_used": self.tokens_used,
            "selection_rationale": self.selection_rationale,
        }


@dataclass(slots=True)
class EvidenceItem:
    """Quantitative or researched fact with explicit provenance."""

    code: str
    label: str
    value: Any
    kind: EvidenceKind
    source: str
    confidence: float
    unit: str | None = None
    related_urls: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["kind"] = self.kind.value
        return payload


@dataclass(slots=True)
class EvidenceBundle:
    """Layer 2 (+ contributions from 3) — deterministic evidence kept separate."""

    deterministic: list[EvidenceItem] = field(default_factory=list)
    research: list[EvidenceItem] = field(default_factory=list)
    inferences: list[EvidenceItem] = field(default_factory=list)

    def all_items(self) -> list[EvidenceItem]:
        return [*self.deterministic, *self.research, *self.inferences]

    def to_dict(self) -> dict[str, Any]:
        return {
            "deterministic": [e.to_dict() for e in self.deterministic],
            "research": [e.to_dict() for e in self.research],
            "inferences": [e.to_dict() for e in self.inferences],
        }


@dataclass(slots=True)
class SpecialistOutput:
    agent_name: str
    role: str
    summary: str
    claims: list[str] = field(default_factory=list)
    confidence: float = 0.0
    evidence_refs: list[str] = field(default_factory=list)
    is_llm_derived: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Challenge:
    claim: str
    challenge: str
    severity: Literal["low", "medium", "high"]
    unresolved: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class VerificationResult:
    consistent: bool
    blocked: bool
    consensus_score: float
    checks: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RankedRecommendation:
    title: str
    rationale: str
    priority: Literal["critical", "high", "medium", "low"]
    impact: float
    effort: float
    confidence: float
    priority_score: float
    evidence_refs: list[str] = field(default_factory=list)
    depends_on_inference: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SimulationOutcome:
    recommendation_title: str
    expected_upside: str
    expected_downside: str
    alternatives: list[str] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ExecutionTask:
    title: str
    description: str
    owner_role: str
    priority: str
    depends_on: list[str] = field(default_factory=list)
    success_metric: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class LearningRecord:
    recommendation_title: str
    expected_metric: str
    baseline_note: str
    feature_hints: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class LayerResult:
    layer: StrategicLayer
    name: str
    status: Literal["completed", "skipped", "failed"]
    summary: str
    duration_ms: int = 0
    output: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "layer": int(self.layer),
            "name": self.name,
            "status": self.status,
            "summary": self.summary,
            "duration_ms": self.duration_ms,
            "output": self.output,
            "errors": self.errors,
        }


@dataclass(slots=True)
class PipelineState:
    """Mutable state flowing through Layers 0–10."""

    request: StrategicRequest
    classification: RequestClassification | None = None
    context: ContextBundle | None = None
    evidence: EvidenceBundle = field(default_factory=EvidenceBundle)
    specialists: list[SpecialistOutput] = field(default_factory=list)
    challenges: list[Challenge] = field(default_factory=list)
    verification: VerificationResult | None = None
    recommendations: list[RankedRecommendation] = field(default_factory=list)
    simulations: list[SimulationOutcome] = field(default_factory=list)
    tasks: list[ExecutionTask] = field(default_factory=list)
    learning: list[LearningRecord] = field(default_factory=list)
    layer_results: list[LayerResult] = field(default_factory=list)
    # Peacock mode runtime
    peacock_mode: str | None = None
    mode_tracker: Any = None  # ModeBudgetTracker — typed loosely to avoid cycles
    lab_plan: dict[str, Any] | None = None


@dataclass(slots=True)
class PipelineResult:
    id: str
    organisation_id: str
    workspace_id: str
    status: str
    classification: RequestClassification
    layers: list[LayerResult]
    recommendations: list[RankedRecommendation]
    tasks: list[ExecutionTask]
    evidence_summary: dict[str, int]
    context_summary: dict[str, Any]
    verification: VerificationResult | None
    learning: list[LearningRecord]
    interpretation: str | None = None
    peacock_mode: str | None = None
    mode: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organisation_id": self.organisation_id,
            "workspace_id": self.workspace_id,
            "status": self.status,
            "peacock_mode": self.peacock_mode,
            "mode": self.mode,
            "classification": self.classification.to_dict(),
            "layers": [layer.to_dict() for layer in self.layers],
            "recommendations": [r.to_dict() for r in self.recommendations],
            "tasks": [t.to_dict() for t in self.tasks],
            "evidence_summary": self.evidence_summary,
            "context_summary": self.context_summary,
            "verification": self.verification.to_dict() if self.verification else None,
            "learning": [item.to_dict() for item in self.learning],
            "interpretation": self.interpretation,
        }
