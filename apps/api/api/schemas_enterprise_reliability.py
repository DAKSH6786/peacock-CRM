"""Peacock Enterprise Reliability API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ReliabilityBriefRequest(BaseModel):
    client_brand: str = Field(min_length=1, max_length=255)
    engines: list[str] = Field(default_factory=list)
    unavailable_engines: list[str] = Field(default_factory=lambda: ["deepseek"])
    idempotency_key: str | None = Field(default=None, max_length=128)
    cancel_requested: bool = False
    recover_from_checkpoint: bool = False
    cost_limit_usd_micros: int = Field(default=50_000, ge=0)
    rate_limit_rpm: int = Field(default=60, ge=1)
    analysed_at: datetime | None = None


class ReliabilityRunCreateRequest(BaseModel):
    website_id: str
    workspace_id: str | None = None
    name: str = Field(min_length=2, max_length=255)
    brief: ReliabilityBriefRequest
    notes: str | None = None


class ProviderMeasurementResponse(BaseModel):
    engine_code: str
    engine_name: str
    provider_code: str
    outcome: str
    attempts: int
    failover_from: str | None
    latency_ms: float | None
    cost_usd_micros: int
    error_message: str | None
    included_in_report: bool
    rank_order: int


class ControlActivationResponse(BaseModel):
    control_kind: str
    control_label: str
    active: bool
    detail: str
    rank_order: int


class DeadLetterResponse(BaseModel):
    source_kind: str
    source_ref: str
    error_class: str
    error_message: str
    attempts: int
    replay_status: str
    payload_summary: str | None


class CircuitStateResponse(BaseModel):
    provider_code: str
    circuit_state: str
    failure_count: int
    cooldown_seconds: int
    reason: str | None


class WorkflowCheckpointResponse(BaseModel):
    phase: str
    checkpoint_status: str
    detail: str
    resumable: bool
    rank_order: int


class ReliabilityRunResponse(BaseModel):
    run_id: str
    name: str
    client_brand: str
    methodology: str
    report_status: str
    engines_attempted: int
    engines_succeeded: int
    engines_failed: int
    partial_result_summary: str
    unavailable_providers: list[str]
    idempotency_key: str | None
    cancelled: bool
    recovered_from_checkpoint: bool
    cost_limit_usd_micros: int
    cost_used_usd_micros: int
    rate_limit_rpm: int
    dlq_events_count: int
    controls_active_count: int
    provider_measurements: list[ProviderMeasurementResponse]
    control_activations: list[ControlActivationResponse]
    dead_letter_events: list[DeadLetterResponse]
    circuit_states: list[CircuitStateResponse]
    workflow_checkpoints: list[WorkflowCheckpointResponse]
    reliability_positioning: str
    partial_results_policy: str
    methodology_note: str
    summary: str
    analysed_at: str


class ReliabilityPreviewResponse(BaseModel):
    client_brand: str
    report_status: str
    engines_attempted: int
    engines_succeeded: int
    engines_failed: int
    partial_result_summary: str
    unavailable_providers: list[str]
    idempotency_key: str | None
    cancelled: bool
    recovered_from_checkpoint: bool
    cost_limit_usd_micros: int
    cost_used_usd_micros: int
    rate_limit_rpm: int
    dlq_events_count: int
    controls_active_count: int
    provider_measurements: list[ProviderMeasurementResponse]
    control_activations: list[ControlActivationResponse]
    dead_letter_events: list[DeadLetterResponse]
    circuit_states: list[CircuitStateResponse]
    workflow_checkpoints: list[WorkflowCheckpointResponse]
    reliability_positioning: str
    partial_results_policy: str
    methodology_note: str
    summary: str
    analysed_at: str


class ReliabilityCatalogResponse(BaseModel):
    reliability_controls: list[str]
    control_labels: dict[str, str]
    report_statuses: list[str]
    default_ai_engines: list[str]
    retry_policy: dict[str, Any]
    rate_limit_default_rpm: int
    cost_limit_default_usd_micros: int
    partial_results_policy: str
    reliability_positioning: str
    methodology_note: str
    product_note: str
    example_partial_summary: str
