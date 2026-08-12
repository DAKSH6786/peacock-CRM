"""Peacock 90 2.0 API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ResourceConstraintsRequest(BaseModel):
    budget_amount: float = Field(ge=0.0, description="Available budget (e.g. INR)")
    budget_currency: str = Field(default="INR", max_length=8)
    writers: int = Field(default=5, ge=0)
    developers: int = Field(default=2, ge=0)
    seo_specialists: int = Field(default=1, ge=0)
    articles_per_month_max: int = Field(default=25, ge=0)
    approval_capacity_per_week: int = Field(default=8, ge=0)
    business_priorities: list[str] = Field(
        default_factory=lambda: ["technical_seo", "content", "authority"]
    )
    risk_tolerance: str = Field(default="medium", pattern="^(low|medium|high)$")


class Peacock90BriefRequest(BaseModel):
    client_brand: str = Field(min_length=1, max_length=255)
    horizon_days: int = Field(default=90, ge=1, le=180)
    constraints: ResourceConstraintsRequest


class Peacock90PlanRequest(BaseModel):
    website_id: str
    workspace_id: str | None = None
    name: str = Field(min_length=2, max_length=255)
    brief: Peacock90BriefRequest
    notes: str | None = None


class InitiativeResponse(BaseModel):
    initiative_code: str
    title: str
    priority_family: str
    selected: bool
    impact_score: float
    effort_score: float
    risk_level: str
    budget_cost: float
    writer_days: float
    developer_days: float
    seo_days: float
    articles_required: int
    approval_slots: int
    rank: int | None
    rejection_reason: str | None
    rationale: str


class TaskResponse(BaseModel):
    task_code: str
    title: str
    task_kind: str
    owner_role: str
    week_index: int
    effort_days: float
    sequence_order: int
    initiative_code: str
    description: str | None
    depends_on: list[str]


class DependencyResponse(BaseModel):
    predecessor_task_code: str
    successor_task_code: str
    edge_label: str | None


class CapacityRefusalResponse(BaseModel):
    requested_label: str
    requested_amount: float
    capacity_limit: float
    unit: str
    reason: str


class Peacock90PlanResponse(BaseModel):
    plan_id: str
    name: str
    client_brand: str
    methodology: str
    horizon_days: int
    constraints: dict
    initiatives: list[InitiativeResponse]
    tasks: list[TaskResponse]
    dependencies: list[DependencyResponse]
    capacity_refusals: list[CapacityRefusalResponse]
    total_impact_score: float
    budget_used: float
    articles_planned: int
    initiatives_selected: int
    initiatives_rejected: int
    tasks_scheduled: int
    utilisation_summary: str
    capacity_guardrail: str
    methodology_note: str
    dependency_example: list[str]
    summary: str


class Peacock90CatalogResponse(BaseModel):
    methodology: str
    methodology_note: str
    capacity_guardrail: str
    horizon_days: int
    priority_codes: list[str]
    risk_tolerance_levels: list[str]
    task_kinds: list[str]
    example_resources: dict
    dependency_example: list[str]
