"""Peacock Action Engine API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ActionDraftRequest(BaseModel):
    action_type: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=255)
    payload_summary: str = Field(min_length=1)
    description: str | None = None
    target_ref: str | None = Field(default=None, max_length=255)
    risk_level: str = Field(default="low", pattern="^(low|medium|high)$")
    requires_approval: bool = True
    notes: str | None = None


class CreateActionRequest(BaseModel):
    website_id: str
    workspace_id: str | None = None
    draft: ActionDraftRequest


class ApprovalRequest(BaseModel):
    comment: str | None = None


class RevertRequest(BaseModel):
    reason: str = "Reverted by operator."


class GrantPermissionRequest(BaseModel):
    workspace_id: str | None = None
    website_id: str | None = None
    connector: str = Field(min_length=1, max_length=64)
    permission_scope: str = Field(min_length=1, max_length=64)
    notes: str | None = None


class TransitionResponse(BaseModel):
    from_status: str | None
    to_status: str
    reason: str


class ExecutionResponse(BaseModel):
    outcome: str
    detail: str
    external_side_effects: bool
    executor: str


class ActionResponse(BaseModel):
    action_id: str
    methodology: str
    action_type: str
    action_label: str
    title: str
    description: str | None
    payload_summary: str
    action_status: str
    requires_approval: bool
    is_destructive_external: bool
    permission_scope_required: str | None
    permission_granted: bool
    risk_level: str
    target_ref: str | None
    result_summary: str | None
    failure_reason: str | None
    destructive_guardrail: str
    transitions: list[TransitionResponse]
    executions: list[ExecutionResponse]
    notes: str | None = None


class ActionCatalogResponse(BaseModel):
    action_types: dict[str, str]
    action_statuses: list[str]
    permission_scopes: list[str]
    destructive_external_actions: list[str]
    destructive_guardrail: str
    methodology_note: str
    status_lifecycle: list[str]


class PermissionResponse(BaseModel):
    permission_id: str
    connector: str
    permission_scope: str
    granted: bool
