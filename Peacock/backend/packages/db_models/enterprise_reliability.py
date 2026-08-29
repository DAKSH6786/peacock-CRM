"""Peacock Enterprise Reliability — durable controls for multi-provider runs.

Capabilities:
- idempotent jobs, retry policies, circuit breakers, provider failover
- dead-letter queue, audit trails, rate limits, cost limits
- workflow recovery, cancellation, partial results

If one provider fails, Peacock should not necessarily fail the entire report.
Example: \"4/5 AI engines successfully measured. DeepSeek unavailable during this run.\"
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db_models.base import Base, WorkspaceTenantMixin


RELIABILITY_CONTROLS: tuple[str, ...] = (
    "idempotent_jobs",
    "retry_policies",
    "circuit_breakers",
    "provider_failover",
    "dead_letter_queue",
    "audit_trails",
    "rate_limits",
    "cost_limits",
    "workflow_recovery",
    "cancellation",
    "partial_results",
)

CONTROL_LABELS: dict[str, str] = {
    "idempotent_jobs": "Idempotent jobs",
    "retry_policies": "Retry policies",
    "circuit_breakers": "Circuit breakers",
    "provider_failover": "Provider failover",
    "dead_letter_queue": "Dead-letter queue",
    "audit_trails": "Audit trails",
    "rate_limits": "Rate limits",
    "cost_limits": "Cost limits",
    "workflow_recovery": "Workflow recovery",
    "cancellation": "Cancellation",
    "partial_results": "Partial results",
}

REPORT_STATUSES: tuple[str, ...] = (
    "completed",
    "completed_partial",
    "failed",
    "cancelled",
    "recovering",
)

CIRCUIT_STATES: tuple[str, ...] = (
    "closed",
    "open",
    "half_open",
)

PROVIDER_OUTCOMES: tuple[str, ...] = (
    "succeeded",
    "failed",
    "unavailable",
    "rate_limited",
    "circuit_open",
    "cancelled",
    "failover_used",
)

DEFAULT_AI_ENGINES: tuple[str, ...] = (
    "chatgpt",
    "gemini",
    "claude",
    "perplexity",
    "deepseek",
)

METHODOLOGY = "peacock_enterprise_reliability_v1"
METHODOLOGY_NOTE = (
    "Enterprise Reliability keeps multi-model Peacock runs resilient: "
    "idempotent jobs, retries, circuit breakers, provider failover, DLQ, "
    "audit trails, rate/cost limits, workflow recovery, cancellation, and "
    "partial results so one unavailable provider does not fail the whole report."
)
PARTIAL_RESULTS_POLICY = (
    "If one provider fails, Peacock should not necessarily fail the entire report. "
    "It should state how many AI engines succeeded and which were unavailable."
)
RELIABILITY_POSITIONING = (
    "Enterprise Reliability is the control plane for Peacock's multi-provider "
    "intelligence stack — degrade gracefully, recover workflows, and keep audits."
)


class EnterpriseReliabilityRun(Base, WorkspaceTenantMixin):
    """One reliability-aware multi-provider measurement / control demo run."""

    __tablename__ = "enterprise_reliability_runs"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_brand: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    report_status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    engines_attempted: Mapped[int] = mapped_column(Integer, nullable=False)
    engines_succeeded: Mapped[int] = mapped_column(Integer, nullable=False)
    engines_failed: Mapped[int] = mapped_column(Integer, nullable=False)
    partial_result_summary: Mapped[str] = mapped_column(Text, nullable=False)
    unavailable_providers: Mapped[str] = mapped_column(Text, nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), index=True)
    cancelled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recovered_from_checkpoint: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    cost_limit_usd_micros: Mapped[int] = mapped_column(Integer, nullable=False)
    cost_used_usd_micros: Mapped[int] = mapped_column(Integer, nullable=False)
    rate_limit_rpm: Mapped[int] = mapped_column(Integer, nullable=False)
    dlq_events_count: Mapped[int] = mapped_column(Integer, nullable=False)
    controls_active_count: Mapped[int] = mapped_column(Integer, nullable=False)
    methodology: Mapped[str] = mapped_column(String(64), default=METHODOLOGY, nullable=False)
    reliability_positioning: Mapped[str] = mapped_column(Text, nullable=False)
    partial_results_policy: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    analysed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    notes: Mapped[str | None] = mapped_column(Text)

    provider_measurements: Mapped[list[ErProviderMeasurement]] = relationship(
        back_populates="run", cascade="all, delete-orphan", passive_deletes=True
    )
    control_activations: Mapped[list[ErControlActivation]] = relationship(
        back_populates="run", cascade="all, delete-orphan", passive_deletes=True
    )
    dead_letter_events: Mapped[list[ErDeadLetterEvent]] = relationship(
        back_populates="run", cascade="all, delete-orphan", passive_deletes=True
    )
    circuit_states: Mapped[list[ErCircuitState]] = relationship(
        back_populates="run", cascade="all, delete-orphan", passive_deletes=True
    )
    workflow_checkpoints: Mapped[list[ErWorkflowCheckpoint]] = relationship(
        back_populates="run", cascade="all, delete-orphan", passive_deletes=True
    )


class ErProviderMeasurement(Base, WorkspaceTenantMixin):
    """Per AI-engine measurement outcome within a reliability run."""

    __tablename__ = "er_provider_measurements"
    __table_args__ = (UniqueConstraint("run_id", "engine_code"),)

    run_id: Mapped[str] = mapped_column(
        ForeignKey("enterprise_reliability_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    engine_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    engine_name: Mapped[str] = mapped_column(String(128), nullable=False)
    provider_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    outcome: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False)
    failover_from: Mapped[str | None] = mapped_column(String(64))
    latency_ms: Mapped[float | None] = mapped_column(Float)
    cost_usd_micros: Mapped[int] = mapped_column(Integer, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    included_in_report: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    rank_order: Mapped[int] = mapped_column(Integer, nullable=False)

    run: Mapped[EnterpriseReliabilityRun] = relationship(
        back_populates="provider_measurements"
    )


class ErControlActivation(Base, WorkspaceTenantMixin):
    """Which reliability controls fired during the run."""

    __tablename__ = "er_control_activations"
    __table_args__ = (UniqueConstraint("run_id", "control_kind"),)

    run_id: Mapped[str] = mapped_column(
        ForeignKey("enterprise_reliability_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    control_kind: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    control_label: Mapped[str] = mapped_column(String(255), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False)
    rank_order: Mapped[int] = mapped_column(Integer, nullable=False)

    run: Mapped[EnterpriseReliabilityRun] = relationship(
        back_populates="control_activations"
    )


class ErDeadLetterEvent(Base, WorkspaceTenantMixin):
    """Dead-letter queue entries for exhausted retries."""

    __tablename__ = "er_dead_letter_events"

    run_id: Mapped[str] = mapped_column(
        ForeignKey("enterprise_reliability_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_kind: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    error_class: Mapped[str] = mapped_column(String(128), nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False)
    replay_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    payload_summary: Mapped[str | None] = mapped_column(Text)

    run: Mapped[EnterpriseReliabilityRun] = relationship(
        back_populates="dead_letter_events"
    )


class ErCircuitState(Base, WorkspaceTenantMixin):
    """Circuit breaker snapshot per provider."""

    __tablename__ = "er_circuit_states"
    __table_args__ = (UniqueConstraint("run_id", "provider_code"),)

    run_id: Mapped[str] = mapped_column(
        ForeignKey("enterprise_reliability_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    circuit_state: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False)
    cooldown_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)

    run: Mapped[EnterpriseReliabilityRun] = relationship(back_populates="circuit_states")


class ErWorkflowCheckpoint(Base, WorkspaceTenantMixin):
    """Workflow recovery checkpoints / cancellation markers."""

    __tablename__ = "er_workflow_checkpoints"
    __table_args__ = (UniqueConstraint("run_id", "phase"),)

    run_id: Mapped[str] = mapped_column(
        ForeignKey("enterprise_reliability_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    phase: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    checkpoint_status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    detail: Mapped[str] = mapped_column(Text, nullable=False)
    resumable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    rank_order: Mapped[int] = mapped_column(Integer, nullable=False)

    run: Mapped[EnterpriseReliabilityRun] = relationship(
        back_populates="workflow_checkpoints"
    )
