"""Peacock Enterprise Reliability — resilient multi-provider controls

Revision ID: 0038_enterprise_reliability
Revises: 0037_cost_intelligence
Create Date: 2026-08-13
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0038_enterprise_reliability"
down_revision: Union[str, None] = "0037_cost_intelligence"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ix(table: str, cols: list[str]) -> None:
    for col in cols:
        op.create_index(op.f(f"ix_{table}_{col}"), table, [col], unique=False)


def _tenant_cols() -> list:
    return [
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def _tenant_fks(table: str) -> list:
    return [
        sa.ForeignKeyConstraint(
            ["created_by"], ["users.id"], name=op.f(f"fk_{table}_created_by_users"), ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["organisation_id"],
            ["organisations.id"],
            name=op.f(f"fk_{table}_organisation_id_organisations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name=op.f(f"fk_{table}_workspace_id_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f(f"pk_{table}")),
    ]


def upgrade() -> None:
    op.create_table(
        "enterprise_reliability_runs",
        sa.Column("website_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("client_brand", sa.String(length=255), nullable=False),
        sa.Column("report_status", sa.String(length=32), nullable=False),
        sa.Column("engines_attempted", sa.Integer(), nullable=False),
        sa.Column("engines_succeeded", sa.Integer(), nullable=False),
        sa.Column("engines_failed", sa.Integer(), nullable=False),
        sa.Column("partial_result_summary", sa.Text(), nullable=False),
        sa.Column("unavailable_providers", sa.Text(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("cancelled", sa.Boolean(), nullable=False),
        sa.Column("recovered_from_checkpoint", sa.Boolean(), nullable=False),
        sa.Column("cost_limit_usd_micros", sa.Integer(), nullable=False),
        sa.Column("cost_used_usd_micros", sa.Integer(), nullable=False),
        sa.Column("rate_limit_rpm", sa.Integer(), nullable=False),
        sa.Column("dlq_events_count", sa.Integer(), nullable=False),
        sa.Column("controls_active_count", sa.Integer(), nullable=False),
        sa.Column("methodology", sa.String(length=64), nullable=False),
        sa.Column("reliability_positioning", sa.Text(), nullable=False),
        sa.Column("partial_results_policy", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("analysed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        *_tenant_cols(),
        sa.ForeignKeyConstraint(
            ["website_id"],
            ["websites.id"],
            name=op.f("fk_enterprise_reliability_runs_website_id_websites"),
            ondelete="CASCADE",
        ),
        *_tenant_fks("enterprise_reliability_runs"),
    )
    _ix(
        "enterprise_reliability_runs",
        [
            "website_id",
            "client_brand",
            "report_status",
            "idempotency_key",
            "analysed_at",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "er_provider_measurements",
        sa.Column("run_id", sa.String(length=36), nullable=False),
        sa.Column("engine_code", sa.String(length=64), nullable=False),
        sa.Column("engine_name", sa.String(length=128), nullable=False),
        sa.Column("provider_code", sa.String(length=64), nullable=False),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("failover_from", sa.String(length=64), nullable=True),
        sa.Column("latency_ms", sa.Float(), nullable=True),
        sa.Column("cost_usd_micros", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("included_in_report", sa.Boolean(), nullable=False),
        sa.Column("rank_order", sa.Integer(), nullable=False),
        *_tenant_cols(),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["enterprise_reliability_runs.id"],
            name=op.f("fk_er_provider_measurements_run_id_enterprise_reliability_runs"),
            ondelete="CASCADE",
        ),
        *_tenant_fks("er_provider_measurements"),
        sa.UniqueConstraint(
            "run_id", "engine_code", name=op.f("uq_er_provider_measurements_run_id")
        ),
    )
    _ix(
        "er_provider_measurements",
        [
            "run_id",
            "engine_code",
            "provider_code",
            "outcome",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "er_control_activations",
        sa.Column("run_id", sa.String(length=36), nullable=False),
        sa.Column("control_kind", sa.String(length=64), nullable=False),
        sa.Column("control_label", sa.String(length=255), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("rank_order", sa.Integer(), nullable=False),
        *_tenant_cols(),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["enterprise_reliability_runs.id"],
            name=op.f("fk_er_control_activations_run_id_enterprise_reliability_runs"),
            ondelete="CASCADE",
        ),
        *_tenant_fks("er_control_activations"),
        sa.UniqueConstraint(
            "run_id", "control_kind", name=op.f("uq_er_control_activations_run_id")
        ),
    )
    _ix(
        "er_control_activations",
        [
            "run_id",
            "control_kind",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "er_dead_letter_events",
        sa.Column("run_id", sa.String(length=36), nullable=False),
        sa.Column("source_kind", sa.String(length=64), nullable=False),
        sa.Column("source_ref", sa.String(length=128), nullable=False),
        sa.Column("error_class", sa.String(length=128), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("replay_status", sa.String(length=32), nullable=False),
        sa.Column("payload_summary", sa.Text(), nullable=True),
        *_tenant_cols(),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["enterprise_reliability_runs.id"],
            name=op.f("fk_er_dead_letter_events_run_id_enterprise_reliability_runs"),
            ondelete="CASCADE",
        ),
        *_tenant_fks("er_dead_letter_events"),
    )
    _ix(
        "er_dead_letter_events",
        [
            "run_id",
            "source_kind",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "er_circuit_states",
        sa.Column("run_id", sa.String(length=36), nullable=False),
        sa.Column("provider_code", sa.String(length=64), nullable=False),
        sa.Column("circuit_state", sa.String(length=32), nullable=False),
        sa.Column("failure_count", sa.Integer(), nullable=False),
        sa.Column("cooldown_seconds", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        *_tenant_cols(),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["enterprise_reliability_runs.id"],
            name=op.f("fk_er_circuit_states_run_id_enterprise_reliability_runs"),
            ondelete="CASCADE",
        ),
        *_tenant_fks("er_circuit_states"),
        sa.UniqueConstraint(
            "run_id", "provider_code", name=op.f("uq_er_circuit_states_run_id")
        ),
    )
    _ix(
        "er_circuit_states",
        [
            "run_id",
            "provider_code",
            "circuit_state",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "er_workflow_checkpoints",
        sa.Column("run_id", sa.String(length=36), nullable=False),
        sa.Column("phase", sa.String(length=64), nullable=False),
        sa.Column("checkpoint_status", sa.String(length=32), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("resumable", sa.Boolean(), nullable=False),
        sa.Column("rank_order", sa.Integer(), nullable=False),
        *_tenant_cols(),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["enterprise_reliability_runs.id"],
            name=op.f("fk_er_workflow_checkpoints_run_id_enterprise_reliability_runs"),
            ondelete="CASCADE",
        ),
        *_tenant_fks("er_workflow_checkpoints"),
        sa.UniqueConstraint(
            "run_id", "phase", name=op.f("uq_er_workflow_checkpoints_run_id")
        ),
    )
    _ix(
        "er_workflow_checkpoints",
        [
            "run_id",
            "phase",
            "checkpoint_status",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )


def downgrade() -> None:
    op.drop_table("er_workflow_checkpoints")
    op.drop_table("er_circuit_states")
    op.drop_table("er_dead_letter_events")
    op.drop_table("er_control_activations")
    op.drop_table("er_provider_measurements")
    op.drop_table("enterprise_reliability_runs")
