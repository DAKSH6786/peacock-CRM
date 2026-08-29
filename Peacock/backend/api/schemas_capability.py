from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CapabilityRouteRequest(BaseModel):
    task_type: str | None = None
    gateway_role: str | None = None
    workspace_id: str | None = None
    allowed_providers: list[str] = Field(default_factory=list)


class CapabilityObservationRequest(BaseModel):
    provider_code: str
    model_code: str
    task_type: str
    latency_ms: float = Field(ge=0)
    cost_usd_micros: int = Field(ge=0, default=0)
    succeeded: bool = True
    quality_score: float | None = Field(default=None, ge=0.0, le=1.0)
    json_compliant: bool | None = None
    citation_accuracy: float | None = Field(default=None, ge=0.0, le=1.0)
    historical_agreement: float | None = Field(default=None, ge=0.0, le=1.0)
    gateway_role: str | None = None
    template_id: str | None = None
    llm_request_id: str | None = None
    notes: str | None = None
    workspace_id: str | None = None


class CapabilityProfileResponse(BaseModel):
    profile: dict[str, Any]


class CapabilityRouteResponse(BaseModel):
    decision: dict[str, Any]


class CapabilityCatalogResponse(BaseModel):
    task_types: list[str]
    soft_priors: list[dict[str, Any]]
    gateway_role_task_defaults: dict[str, str]
    permanent_role_locks: bool = False


class OrganisationPolicySchema(BaseModel):
    allowed_providers: list[str] = Field(default_factory=list)
    denied_providers: list[str] = Field(default_factory=list)
    allowed_models: list[str] = Field(default_factory=list)
    denied_models: list[str] = Field(default_factory=list)
    max_cost_usd_micros: int | None = None
    prefer_observed: bool = True
    require_json_capable: bool = False
    prefer_eu_compatible: bool = False
    notes: str | None = None


class ModelRouterRequestSchema(BaseModel):
    task_type: str
    complexity: str = "medium"
    freshness_requirement: str = "none"
    required_capabilities: list[str] = Field(default_factory=list)
    expected_context_size: int = Field(default=8000, ge=1)
    accuracy_requirement: float = Field(default=0.7, ge=0.0, le=1.0)
    latency_target: float = Field(default=5000.0, ge=1.0)
    budget: int = Field(default=50000, ge=0)
    organisation_policy: OrganisationPolicySchema = Field(default_factory=OrganisationPolicySchema)
    workspace_id: str | None = None


class ModelRouterResponse(BaseModel):
    primary_model: dict[str, Any]
    secondary_model: dict[str, Any] | None = None
    fallback_model: dict[str, Any] | None = None
    reason: str
    task_type: str
    candidates_considered: int = 0
    constraints_applied: list[str] = Field(default_factory=list)
    permanent_role_locks: bool = False
