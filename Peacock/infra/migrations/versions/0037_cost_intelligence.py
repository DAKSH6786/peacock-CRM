"""Peacock Cost Intelligence — Intelligence Budget Engine

Revision ID: 0037_cost_intelligence
Revises: 0036_moat_data_model
Create Date: 2026-08-13
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0037_cost_intelligence"
down_revision: Union[str, None] = "0036_moat_data_model"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ix(table: str, cols: list[str]) -> None:
    for col in cols:
        op.create_index(op.f(f"ix_{table}_{col}"), table, [col], unique=False)


def upgrade() -> None:
    op.create_table(
        "intelligence_budget_estimates",
        sa.Column("website_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("client_brand", sa.String(length=255), nullable=False),
        sa.Column("workflow_intent", sa.String(length=64), nullable=False),
        sa.Column("decision_value", sa.String(length=32), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("selected_method_kind", sa.String(length=32), nullable=False),
        sa.Column("selected_method_label", sa.String(length=255), nullable=False),
        sa.Column("selected_peacock_mode", sa.String(length=64), nullable=True),
        sa.Column("selection_rationale", sa.Text(), nullable=False),
        sa.Column("rejected_expensive", sa.Boolean(), nullable=False),
        sa.Column("expected_calls", sa.Integer(), nullable=False),
        sa.Column("expected_tokens", sa.Integer(), nullable=False),
        sa.Column("expected_searches", sa.Integer(), nullable=False),
        sa.Column("expected_runtime_seconds", sa.Float(), nullable=False),
        sa.Column("expected_cost_usd_micros", sa.Integer(), nullable=False),
        sa.Column("candidates_count", sa.Integer(), nullable=False),
        sa.Column("methodology", sa.String(length=64), nullable=False),
        sa.Column("cost_positioning", sa.Text(), nullable=False),
        sa.Column("policy_note", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("analysed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name=op.f("fk_intelligence_budget_estimates_created_by_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["organisation_id"],
            ["organisations.id"],
            name=op.f("fk_intelligence_budget_estimates_organisation_id_organisations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["website_id"],
            ["websites.id"],
            name=op.f("fk_intelligence_budget_estimates_website_id_websites"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name=op.f("fk_intelligence_budget_estimates_workspace_id_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_intelligence_budget_estimates")),
    )
    _ix(
        "intelligence_budget_estimates",
        [
            "website_id",
            "client_brand",
            "workflow_intent",
            "decision_value",
            "selected_method_kind",
            "selected_peacock_mode",
            "analysed_at",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "ibe_method_candidates",
        sa.Column("estimate_id", sa.String(length=36), nullable=False),
        sa.Column("method_kind", sa.String(length=32), nullable=False),
        sa.Column("method_label", sa.String(length=255), nullable=False),
        sa.Column("peacock_mode", sa.String(length=64), nullable=True),
        sa.Column("reliable_enough", sa.Boolean(), nullable=False),
        sa.Column("allowed_for_value", sa.Boolean(), nullable=False),
        sa.Column("selected", sa.Boolean(), nullable=False),
        sa.Column("expected_calls", sa.Integer(), nullable=False),
        sa.Column("expected_tokens", sa.Integer(), nullable=False),
        sa.Column("expected_searches", sa.Integer(), nullable=False),
        sa.Column("expected_runtime_seconds", sa.Float(), nullable=False),
        sa.Column("expected_cost_usd_micros", sa.Integer(), nullable=False),
        sa.Column("reliability_score", sa.Float(), nullable=False),
        sa.Column("cost_efficiency_score", sa.Float(), nullable=False),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("rank_order", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name=op.f("fk_ibe_method_candidates_created_by_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["estimate_id"],
            ["intelligence_budget_estimates.id"],
            name=op.f("fk_ibe_method_candidates_estimate_id_intelligence_budget_estimates"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["organisation_id"],
            ["organisations.id"],
            name=op.f("fk_ibe_method_candidates_organisation_id_organisations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name=op.f("fk_ibe_method_candidates_workspace_id_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ibe_method_candidates")),
        sa.UniqueConstraint(
            "estimate_id", "method_kind", name=op.f("uq_ibe_method_candidates_estimate_id")
        ),
    )
    _ix(
        "ibe_method_candidates",
        [
            "estimate_id",
            "method_kind",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )


def downgrade() -> None:
    op.drop_table("ibe_method_candidates")
    op.drop_table("intelligence_budget_estimates")
