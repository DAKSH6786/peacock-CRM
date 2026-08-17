"""Peacock Cost Intelligence API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class BudgetBriefRequest(BaseModel):
    client_brand: str = Field(min_length=1, max_length=255)
    question: str = Field(min_length=1)
    workflow_intent: str = Field(default="custom", max_length=64)
    decision_value: str | None = Field(default=None, max_length=32)
    analysed_at: datetime | None = None


class BudgetEstimateCreateRequest(BaseModel):
    website_id: str
    workspace_id: str | None = None
    name: str = Field(min_length=2, max_length=255)
    brief: BudgetBriefRequest
    notes: str | None = None


class MethodCandidateResponse(BaseModel):
    method_kind: str
    method_label: str
    peacock_mode: str | None
    reliable_enough: bool
    allowed_for_value: bool
    selected: bool
    expected_calls: int
    expected_tokens: int
    expected_searches: int
    expected_runtime_seconds: float
    expected_cost_usd_micros: int
    reliability_score: float
    cost_efficiency_score: float
    rejection_reason: str | None
    rank_order: int


class BudgetEstimateResponse(BaseModel):
    estimate_id: str
    name: str
    client_brand: str
    methodology: str
    workflow_intent: str
    decision_value: str
    question: str
    selected_method_kind: str
    selected_method_label: str
    selected_peacock_mode: str | None
    selection_rationale: str
    rejected_expensive: bool
    expected_calls: int
    expected_tokens: int
    expected_searches: int
    expected_runtime_seconds: float
    expected_cost_usd_micros: int
    candidates: list[MethodCandidateResponse]
    candidates_count: int
    cost_positioning: str
    policy_note: str
    methodology_note: str
    summary: str
    analysed_at: str


class BudgetPreviewResponse(BaseModel):
    client_brand: str
    workflow_intent: str
    decision_value: str
    question: str
    selected_method_kind: str
    selected_method_label: str
    selected_peacock_mode: str | None
    selection_rationale: str
    rejected_expensive: bool
    expected_calls: int
    expected_tokens: int
    expected_searches: int
    expected_runtime_seconds: float
    expected_cost_usd_micros: int
    candidates: list[MethodCandidateResponse]
    candidates_count: int
    cost_positioning: str
    policy_note: str
    methodology_note: str
    summary: str
    analysed_at: str


class BudgetCatalogResponse(BaseModel):
    method_kinds: list[str]
    method_kind_labels: dict[str, str]
    decision_values: list[str]
    decision_value_labels: dict[str, str]
    workflow_intents: list[str]
    method_ladder: list[str]
    value_method_ceiling: dict[str, str]
    method_profiles: dict[str, Any]
    cost_positioning: str
    policy_note: str
    methodology_note: str
    product_note: str
    examples: list[str]
