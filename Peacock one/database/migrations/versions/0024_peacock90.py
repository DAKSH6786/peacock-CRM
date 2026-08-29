"""Peacock 90 2.0 — adaptive 90-day roadmap optimisation

Revision ID: 0024_peacock90
Revises: 0023_scenario_engine
Create Date: 2026-08-12
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0024_peacock90"
down_revision: Union[str, None] = "0023_scenario_engine"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ix(table: str, cols: list[str]) -> None:
    for col in cols:
        op.create_index(op.f(f"ix_{table}_{col}"), table, [col], unique=False)


def upgrade() -> None:
    op.create_table(
        "peacock90_plans",
        sa.Column("website_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("client_brand", sa.String(length=255), nullable=False),
        sa.Column("horizon_days", sa.Integer(), nullable=False),
        sa.Column("methodology", sa.String(length=64), nullable=False),
        sa.Column("plan_status", sa.String(length=32), nullable=False),
        sa.Column("budget_amount", sa.Float(), nullable=False),
        sa.Column("budget_currency", sa.String(length=8), nullable=False),
        sa.Column("writers", sa.Integer(), nullable=False),
        sa.Column("developers", sa.Integer(), nullable=False),
        sa.Column("seo_specialists", sa.Integer(), nullable=False),
        sa.Column("articles_per_month_max", sa.Integer(), nullable=False),
        sa.Column("approval_capacity_per_week", sa.Integer(), nullable=False),
        sa.Column("risk_tolerance", sa.String(length=16), nullable=False),
        sa.Column("business_priorities", sa.Text(), nullable=False),
        sa.Column("capacity_guardrail", sa.Text(), nullable=False),
        sa.Column("total_impact_score", sa.Float(), nullable=False),
        sa.Column("budget_used", sa.Float(), nullable=False),
        sa.Column("articles_planned", sa.Integer(), nullable=False),
        sa.Column("initiatives_selected", sa.Integer(), nullable=False),
        sa.Column("initiatives_rejected", sa.Integer(), nullable=False),
        sa.Column("tasks_scheduled", sa.Integer(), nullable=False),
        sa.Column("utilisation_summary", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_peacock90_plans_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_peacock90_plans_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["website_id"], ["websites.id"], name=op.f("fk_peacock90_plans_website_id_websites"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_peacock90_plans_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_peacock90_plans")),
    )
    _ix(
        "peacock90_plans",
        [
            "website_id",
            "client_brand",
            "plan_status",
            "risk_tolerance",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "p90_initiatives",
        sa.Column("plan_id", sa.String(length=36), nullable=False),
        sa.Column("initiative_code", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("priority_family", sa.String(length=64), nullable=False),
        sa.Column("selected", sa.Boolean(), nullable=False),
        sa.Column("impact_score", sa.Float(), nullable=False),
        sa.Column("effort_score", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(length=16), nullable=False),
        sa.Column("budget_cost", sa.Float(), nullable=False),
        sa.Column("writer_days", sa.Float(), nullable=False),
        sa.Column("developer_days", sa.Float(), nullable=False),
        sa.Column("seo_days", sa.Float(), nullable=False),
        sa.Column("articles_required", sa.Integer(), nullable=False),
        sa.Column("approval_slots", sa.Integer(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_p90_initiatives_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_p90_initiatives_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plan_id"], ["peacock90_plans.id"], name=op.f("fk_p90_initiatives_plan_id_peacock90_plans"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_p90_initiatives_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_p90_initiatives")),
        sa.UniqueConstraint("plan_id", "initiative_code", name=op.f("uq_p90_initiatives_plan_id")),
    )
    _ix(
        "p90_initiatives",
        [
            "plan_id",
            "initiative_code",
            "priority_family",
            "selected",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "p90_tasks",
        sa.Column("plan_id", sa.String(length=36), nullable=False),
        sa.Column("initiative_id", sa.String(length=36), nullable=True),
        sa.Column("task_code", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("task_kind", sa.String(length=32), nullable=False),
        sa.Column("owner_role", sa.String(length=32), nullable=False),
        sa.Column("week_index", sa.Integer(), nullable=False),
        sa.Column("effort_days", sa.Float(), nullable=False),
        sa.Column("sequence_order", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_p90_tasks_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["initiative_id"], ["p90_initiatives.id"], name=op.f("fk_p90_tasks_initiative_id_p90_initiatives"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_p90_tasks_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plan_id"], ["peacock90_plans.id"], name=op.f("fk_p90_tasks_plan_id_peacock90_plans"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_p90_tasks_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_p90_tasks")),
        sa.UniqueConstraint("plan_id", "task_code", name=op.f("uq_p90_tasks_plan_id")),
    )
    _ix(
        "p90_tasks",
        [
            "plan_id",
            "initiative_id",
            "task_code",
            "task_kind",
            "week_index",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "p90_dependencies",
        sa.Column("plan_id", sa.String(length=36), nullable=False),
        sa.Column("predecessor_task_code", sa.String(length=64), nullable=False),
        sa.Column("successor_task_code", sa.String(length=64), nullable=False),
        sa.Column("edge_label", sa.String(length=128), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_p90_dependencies_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_p90_dependencies_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plan_id"], ["peacock90_plans.id"], name=op.f("fk_p90_dependencies_plan_id_peacock90_plans"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_p90_dependencies_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_p90_dependencies")),
        sa.UniqueConstraint(
            "plan_id",
            "predecessor_task_code",
            "successor_task_code",
            name=op.f("uq_p90_dependencies_plan_id"),
        ),
    )
    _ix(
        "p90_dependencies",
        [
            "plan_id",
            "predecessor_task_code",
            "successor_task_code",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "p90_capacity_refusals",
        sa.Column("plan_id", sa.String(length=36), nullable=False),
        sa.Column("requested_label", sa.String(length=255), nullable=False),
        sa.Column("requested_amount", sa.Float(), nullable=False),
        sa.Column("capacity_limit", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_p90_capacity_refusals_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_p90_capacity_refusals_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plan_id"], ["peacock90_plans.id"], name=op.f("fk_p90_capacity_refusals_plan_id_peacock90_plans"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_p90_capacity_refusals_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_p90_capacity_refusals")),
    )
    _ix(
        "p90_capacity_refusals",
        ["plan_id", "organisation_id", "workspace_id", "created_by", "status"],
    )


def downgrade() -> None:
    op.drop_table("p90_capacity_refusals")
    op.drop_table("p90_dependencies")
    op.drop_table("p90_tasks")
    op.drop_table("p90_initiatives")
    op.drop_table("peacock90_plans")
