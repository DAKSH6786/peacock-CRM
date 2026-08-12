from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class LedgerEvidenceRequest(BaseModel):
    evidence_type: str
    source: str = Field(min_length=1, max_length=255)
    summary: str = Field(min_length=1)
    scope_kind: str = Field(min_length=1, max_length=64)
    scope_ref: str = Field(min_length=1, max_length=1024)
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    observed_at: datetime | None = None
    freshness_hours: float = 0.0
    freshness_score: float = Field(ge=0.0, le=1.0, default=1.0)
    supporting_value_text: str | None = None
    supporting_value_number: float | None = None
    supporting_value_bool: bool | None = None
    supporting_value_unit: str | None = None
    code: str | None = None
    source_url: str | None = None
    workspace_id: str | None = None
    website_id: str | None = None
    crawl_id: str | None = None
    intelligence_case_id: str | None = None


class LedgerFindingRequest(BaseModel):
    statement: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    summary: str | None = None
    finding_kind: str = "insight"
    agent_name: str | None = None
    is_llm_derived: bool = False
    severity: str | None = None
    code: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    workspace_id: str | None = None
    website_id: str | None = None
    intelligence_case_id: str | None = None


class LedgerRecommendationRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    rationale: str = Field(min_length=1)
    priority: str = "medium"
    impact: float = 0.0
    effort: float = 0.0
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    priority_score: float = 0.0
    suggested_fix: str | None = None
    code: str | None = None
    finding_ids: list[str] = Field(default_factory=list)
    workspace_id: str | None = None
    website_id: str | None = None
    central_recommendation_id: str | None = None
    intelligence_case_id: str | None = None


class LedgerActionRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    owner_role: str | None = None
    success_metric: str | None = None
    action_status: str = "planned"
    due_at: datetime | None = None
    code: str | None = None
    recommendation_ids: list[str] = Field(default_factory=list)
    workspace_id: str | None = None
    website_id: str | None = None
    roadmap_task_id: str | None = None
    execution_id: str | None = None


class LedgerOutcomeRequest(BaseModel):
    metric_key: str = Field(min_length=1, max_length=128)
    metric_value: float
    observed_at: datetime | None = None
    baseline_value: float | None = None
    target_value: float | None = None
    notes: str | None = None
    outcome_kind: str = "measured"
    code: str | None = None
    action_ids: list[str] = Field(default_factory=list)
    workspace_id: str | None = None
    website_id: str | None = None
    central_outcome_id: str | None = None


class ClaimEvidenceRequest(BaseModel):
    claim_kind: str = Field(min_length=1, max_length=64)
    claim_ref: str = Field(min_length=1, max_length=255)
    evidence_id: str
    claim_text: str | None = None
    role: str = "supports"
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    workspace_id: str | None = None


class LedgerNodeResponse(BaseModel):
    node: dict[str, Any]


class EvidenceGraphResponse(BaseModel):
    organization_id: str
    organisation_id: str
    workspace_id: str
    evidences: list[dict[str, Any]] = Field(default_factory=list)
    findings: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[dict[str, Any]] = Field(default_factory=list)
    actions: list[dict[str, Any]] = Field(default_factory=list)
    outcomes: list[dict[str, Any]] = Field(default_factory=list)
    edges: list[dict[str, Any]] = Field(default_factory=list)
    claim_pointers: list[dict[str, Any]] = Field(default_factory=list)
    chain: list[str] = Field(default_factory=list)
