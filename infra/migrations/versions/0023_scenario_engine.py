"""Peacock Scenario Engine — counterfactual strategy ranges

Revision ID: 0023_scenario_engine
Revises: 0022_judge2
Create Date: 2026-08-12
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0023_scenario_engine"
down_revision: Union[str, None] = "0022_judge2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ix(table: str, cols: list[str]) -> None:
    for col in cols:
        op.create_index(op.f(f"ix_{table}_{col}"), table, [col], unique=False)


def upgrade() -> None:
    op.create_table(
        "scenario_analyses",
        sa.Column("website_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("client_brand", sa.String(length=255), nullable=False),
        sa.Column("horizon_days", sa.Integer(), nullable=False),
        sa.Column("primary_metric", sa.String(length=64), nullable=False),
        sa.Column("primary_metric_label", sa.String(length=255), nullable=False),
        sa.Column("analysis_status", sa.String(length=32), nullable=False),
        sa.Column("methodology", sa.String(length=64), nullable=False),
        sa.Column("ranges_not_fake_precision", sa.Boolean(), nullable=False),
        sa.Column("ranges_disclaimer", sa.Text(), nullable=False),
        sa.Column("overall_data_quality", sa.Float(), nullable=False),
        sa.Column("overall_uncertainty", sa.Float(), nullable=False),
        sa.Column("overall_confidence", sa.Float(), nullable=False),
        sa.Column("assumptions_summary", sa.Text(), nullable=False),
        sa.Column("recommended_strategy_code", sa.String(length=64), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_scenario_analyses_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_scenario_analyses_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["website_id"], ["websites.id"], name=op.f("fk_scenario_analyses_website_id_websites"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_scenario_analyses_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_scenario_analyses")),
    )
    _ix(
        "scenario_analyses",
        [
            "website_id",
            "client_brand",
            "primary_metric",
            "analysis_status",
            "recommended_strategy_code",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "se_scenarios",
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("strategy_code", sa.String(length=64), nullable=False),
        sa.Column("strategy_label", sa.String(length=255), nullable=False),
        sa.Column("is_baseline", sa.Boolean(), nullable=False),
        sa.Column("is_peacock_recommended", sa.Boolean(), nullable=False),
        sa.Column("range_low_pct", sa.Float(), nullable=False),
        sa.Column("range_high_pct", sa.Float(), nullable=False),
        sa.Column("range_mid_pct", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("data_quality", sa.Float(), nullable=False),
        sa.Column("uncertainty", sa.Float(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["scenario_analyses.id"], name=op.f("fk_se_scenarios_analysis_id_scenario_analyses"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_se_scenarios_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_se_scenarios_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_se_scenarios_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_se_scenarios")),
        sa.UniqueConstraint("analysis_id", "strategy_code", name=op.f("uq_se_scenarios_analysis_id")),
    )
    _ix(
        "se_scenarios",
        ["analysis_id", "strategy_code", "organisation_id", "workspace_id", "created_by", "status"],
    )

    op.create_table(
        "se_metric_ranges",
        sa.Column("scenario_id", sa.String(length=36), nullable=False),
        sa.Column("metric_code", sa.String(length=64), nullable=False),
        sa.Column("metric_label", sa.String(length=255), nullable=False),
        sa.Column("range_low_pct", sa.Float(), nullable=False),
        sa.Column("range_high_pct", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_se_metric_ranges_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_se_metric_ranges_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["scenario_id"], ["se_scenarios.id"], name=op.f("fk_se_metric_ranges_scenario_id_se_scenarios"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_se_metric_ranges_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_se_metric_ranges")),
        sa.UniqueConstraint("scenario_id", "metric_code", name=op.f("uq_se_metric_ranges_scenario_id")),
    )
    _ix(
        "se_metric_ranges",
        ["scenario_id", "metric_code", "organisation_id", "workspace_id", "created_by", "status"],
    )

    op.create_table(
        "se_assumptions",
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("assumption_key", sa.String(length=128), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("sensitivity", sa.String(length=32), nullable=False),
        sa.Column("affects_strategies", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["scenario_analyses.id"], name=op.f("fk_se_assumptions_analysis_id_scenario_analyses"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_se_assumptions_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_se_assumptions_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_se_assumptions_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_se_assumptions")),
    )
    _ix(
        "se_assumptions",
        ["analysis_id", "assumption_key", "organisation_id", "workspace_id", "created_by", "status"],
    )


def downgrade() -> None:
    op.drop_table("se_assumptions")
    op.drop_table("se_metric_ranges")
    op.drop_table("se_scenarios")
    op.drop_table("scenario_analyses")
