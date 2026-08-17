"""Peacock Proprietary Metrics — documented scoring framework

Revision ID: 0034_proprietary_metrics
Revises: 0033_executive_brain
Create Date: 2026-08-13
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0034_proprietary_metrics"
down_revision: Union[str, None] = "0033_executive_brain"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ix(table: str, cols: list[str]) -> None:
    for col in cols:
        op.create_index(op.f(f"ix_{table}_{col}"), table, [col], unique=False)


def upgrade() -> None:
    op.create_table(
        "proprietary_metric_scorecards",
        sa.Column("website_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("client_brand", sa.String(length=255), nullable=False),
        sa.Column("scorecard_status", sa.String(length=32), nullable=False),
        sa.Column("methodology", sa.String(length=64), nullable=False),
        sa.Column("scored_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metrics_scored", sa.Integer(), nullable=False),
        sa.Column("proprietary_disclaimer", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_proprietary_metric_scorecards_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_proprietary_metric_scorecards_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["website_id"], ["websites.id"], name=op.f("fk_proprietary_metric_scorecards_website_id_websites"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_proprietary_metric_scorecards_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_proprietary_metric_scorecards")),
    )
    _ix(
        "proprietary_metric_scorecards",
        [
            "website_id",
            "client_brand",
            "scorecard_status",
            "scored_at",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "pm_metric_scores",
        sa.Column("scorecard_id", sa.String(length=36), nullable=False),
        sa.Column("metric_key", sa.String(length=64), nullable=False),
        sa.Column("metric_label", sa.String(length=128), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=False),
        sa.Column("formula_id", sa.String(length=64), nullable=False),
        sa.Column("formula_text", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("proprietary_note", sa.Text(), nullable=False),
        sa.Column("rank_order", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_pm_metric_scores_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_pm_metric_scores_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["scorecard_id"], ["proprietary_metric_scorecards.id"], name=op.f("fk_pm_metric_scores_scorecard_id_proprietary_metric_scorecards"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_pm_metric_scores_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_pm_metric_scores")),
        sa.UniqueConstraint("scorecard_id", "metric_key", name=op.f("uq_pm_metric_scores_scorecard_id")),
    )
    _ix(
        "pm_metric_scores",
        [
            "scorecard_id",
            "metric_key",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "pm_metric_components",
        sa.Column("metric_score_id", sa.String(length=36), nullable=False),
        sa.Column("component_key", sa.String(length=64), nullable=False),
        sa.Column("component_label", sa.String(length=128), nullable=False),
        sa.Column("raw_value", sa.Float(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("contribution", sa.Float(), nullable=False),
        sa.Column("rank_order", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_pm_metric_components_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["metric_score_id"], ["pm_metric_scores.id"], name=op.f("fk_pm_metric_components_metric_score_id_pm_metric_scores"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_pm_metric_components_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_pm_metric_components_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_pm_metric_components")),
        sa.UniqueConstraint("metric_score_id", "component_key", name=op.f("uq_pm_metric_components_metric_score_id")),
    )
    _ix(
        "pm_metric_components",
        [
            "metric_score_id",
            "component_key",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )


def downgrade() -> None:
    op.drop_table("pm_metric_components")
    op.drop_table("pm_metric_scores")
    op.drop_table("proprietary_metric_scorecards")
