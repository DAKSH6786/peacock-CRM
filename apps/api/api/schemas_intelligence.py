from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class StrategicRunRequest(BaseModel):
    request_text: str = Field(min_length=3, max_length=8000)
    workspace_id: str | None = None
    website_id: str | None = None
    crawl_id: str | None = None
    audit_id: str | None = None
    requested_output: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class StrategicRunResponse(BaseModel):
    id: str
    organisation_id: str
    workspace_id: str
    status: str
    classification: dict[str, Any]
    layers: list[dict[str, Any]]
    recommendations: list[dict[str, Any]]
    tasks: list[dict[str, Any]]
    evidence_summary: dict[str, int]
    context_summary: dict[str, Any]
    verification: dict[str, Any] | None = None
    learning: list[dict[str, Any]] = Field(default_factory=list)
    interpretation: str | None = None


class IntelligenceCaseUpsertRequest(BaseModel):
    """Create/update a PINE IntelligenceCase (relational aggregate)."""

    objective: str = Field(min_length=3, max_length=8000)
    workspace_id: str | None = None
    case_id: str | None = None
    title: str | None = None
    confidence: float = 0.0
    cost_usd_micros: int = 0
    latency_ms: int = 0
    website_id: str | None = None
    strategic_run_id: str | None = None
    status: str = "active"
    context: list[dict[str, Any]] = Field(default_factory=list)
    observations: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    hypotheses: list[dict[str, Any]] = Field(default_factory=list)
    agent_findings: list[dict[str, Any]] = Field(default_factory=list)
    contradictions: list[dict[str, Any]] = Field(default_factory=list)
    unknowns: list[dict[str, Any]] = Field(default_factory=list)
    assumptions: list[dict[str, Any]] = Field(default_factory=list)
    risks: list[dict[str, Any]] = Field(default_factory=list)
    opportunities: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[dict[str, Any]] = Field(default_factory=list)
    models_used: list[dict[str, Any]] = Field(default_factory=list)
    tools_used: list[dict[str, Any]] = Field(default_factory=list)


class IntelligenceCaseResponse(BaseModel):
    case_id: str
    organization_id: str
    organisation_id: str
    workspace_id: str
    objective: str
    title: str | None = None
    confidence: float
    cost: dict[str, int]
    latency: dict[str, int]
    created_at: str | None = None
    updated_at: str | None = None
    status: str
    website_id: str | None = None
    strategic_run_id: str | None = None
    context: list[dict[str, Any]] = Field(default_factory=list)
    observations: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    hypotheses: list[dict[str, Any]] = Field(default_factory=list)
    agent_findings: list[dict[str, Any]] = Field(default_factory=list)
    contradictions: list[dict[str, Any]] = Field(default_factory=list)
    unknowns: list[dict[str, Any]] = Field(default_factory=list)
    assumptions: list[dict[str, Any]] = Field(default_factory=list)
    risks: list[dict[str, Any]] = Field(default_factory=list)
    opportunities: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[dict[str, Any]] = Field(default_factory=list)
    models_used: list[dict[str, Any]] = Field(default_factory=list)
    tools_used: list[dict[str, Any]] = Field(default_factory=list)