"""Peacock Learning Engine 2.0 — closed-loop recommendation learning

Revision ID: 0028_learning_engine2
Revises: 0027_revenue_attribution
Create Date: 2026-08-12
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0028_learning_engine2"
down_revision: Union[str, None] = "0027_revenue_attribution"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ix(table: str, cols: list[str]) -> None:
    for col in cols:
        op.create_index(op.f(f"ix_{table}_{col}"), table, [col], unique=False)


def upgrade() -> None:
    op.create_table(
        "learning2_records",
        sa.Column("website_id", sa.String(length=36), nullable=False),
        sa.Column("central_recommendation_id", sa.String(length=36), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("industry", sa.String(length=64), nullable=False),
        sa.Column("record_status", sa.String(length=32), nullable=False),
        sa.Column("context_summary", sa.Text(), nullable=False),
        sa.Column("recommendation_text", sa.Text(), nullable=False),
        sa.Column("expected_impact", sa.Text(), nullable=False),
        sa.Column("expected_impact_score", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("execution_summary", sa.Text(), nullable=True),
        sa.Column("execution_status", sa.String(length=32), nullable=True),
        sa.Column("actual_outcome", sa.Text(), nullable=True),
        sa.Column("actual_outcome_score", sa.Float(), nullable=True),
        sa.Column("outcome_delta", sa.Float(), nullable=True),
        sa.Column("topic_key", sa.String(length=128), nullable=True),
        sa.Column("format_key", sa.String(length=128), nullable=True),
        sa.Column("source_key", sa.String(length=128), nullable=True),
        sa.Column("writer_key", sa.String(length=128), nullable=True),
        sa.Column("intervention_key", sa.String(length=128), nullable=True),
        sa.Column("engine_key", sa.String(length=128), nullable=True),
        sa.Column("methodology", sa.String(length=64), nullable=False),
        sa.Column("not_universal_geo_strategy", sa.Boolean(), nullable=False),
        sa.Column("not_universal_geo_note", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["central_recommendation_id"], ["recommendations.id"], name=op.f("fk_learning2_records_central_recommendation_id_recommendations"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_learning2_records_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_learning2_records_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["website_id"], ["websites.id"], name=op.f("fk_learning2_records_website_id_websites"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_learning2_records_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_learning2_records")),
    )
    _ix(
        "learning2_records",
        [
            "website_id",
            "central_recommendation_id",
            "industry",
            "record_status",
            "execution_status",
            "topic_key",
            "format_key",
            "source_key",
            "writer_key",
            "intervention_key",
            "engine_key",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "le2_context_factors",
        sa.Column("record_id", sa.String(length=36), nullable=False),
        sa.Column("factor_key", sa.String(length=128), nullable=False),
        sa.Column("factor_value", sa.Text(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_le2_context_factors_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_le2_context_factors_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["record_id"], ["learning2_records.id"], name=op.f("fk_le2_context_factors_record_id_learning2_records"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_le2_context_factors_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_le2_context_factors")),
        sa.UniqueConstraint("record_id", "factor_key", name=op.f("uq_le2_context_factors_record_id")),
    )
    _ix(
        "le2_context_factors",
        ["record_id", "factor_key", "organisation_id", "workspace_id", "created_by", "status"],
    )

    op.create_table(
        "le2_industry_policies",
        sa.Column("industry", sa.String(length=64), nullable=False),
        sa.Column("policy_code", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("guidance", sa.Text(), nullable=False),
        sa.Column("preferred_formats", sa.Text(), nullable=True),
        sa.Column("preferred_sources", sa.Text(), nullable=True),
        sa.Column("citation_interventions", sa.Text(), nullable=True),
        sa.Column("forbidden_universal_claims", sa.Text(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("sample_size", sa.Integer(), nullable=False),
        sa.Column("success_rate", sa.Float(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_le2_industry_policies_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_le2_industry_policies_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_le2_industry_policies_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_le2_industry_policies")),
        sa.UniqueConstraint("organisation_id", "industry", "policy_code", name=op.f("uq_le2_industry_policies_organisation_id")),
    )
    _ix(
        "le2_industry_policies",
        ["industry", "policy_code", "active", "organisation_id", "workspace_id", "created_by", "status"],
    )

    op.create_table(
        "le2_dimension_insights",
        sa.Column("dimension", sa.String(length=64), nullable=False),
        sa.Column("dimension_key", sa.String(length=128), nullable=False),
        sa.Column("industry", sa.String(length=64), nullable=False),
        sa.Column("sample_size", sa.Integer(), nullable=False),
        sa.Column("avg_expected_impact", sa.Float(), nullable=False),
        sa.Column("avg_actual_outcome", sa.Float(), nullable=False),
        sa.Column("avg_confidence", sa.Float(), nullable=False),
        sa.Column("success_rate", sa.Float(), nullable=False),
        sa.Column("insight_summary", sa.Text(), nullable=False),
        sa.Column("not_universal_geo_strategy", sa.Boolean(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_le2_dimension_insights_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_le2_dimension_insights_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_le2_dimension_insights_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_le2_dimension_insights")),
        sa.UniqueConstraint(
            "organisation_id",
            "dimension",
            "dimension_key",
            "industry",
            name=op.f("uq_le2_dimension_insights_organisation_id"),
        ),
    )
    _ix(
        "le2_dimension_insights",
        [
            "dimension",
            "dimension_key",
            "industry",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "le2_learning_runs",
        sa.Column("website_id", sa.String(length=36), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("records_considered", sa.Integer(), nullable=False),
        sa.Column("insights_generated", sa.Integer(), nullable=False),
        sa.Column("industries_touched", sa.Text(), nullable=False),
        sa.Column("not_universal_geo_strategy", sa.Boolean(), nullable=False),
        sa.Column("methodology_note", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_le2_learning_runs_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_le2_learning_runs_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["website_id"], ["websites.id"], name=op.f("fk_le2_learning_runs_website_id_websites"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_le2_learning_runs_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_le2_learning_runs")),
    )
    _ix(
        "le2_learning_runs",
        ["website_id", "organisation_id", "workspace_id", "created_by", "status"],
    )


def downgrade() -> None:
    op.drop_table("le2_learning_runs")
    op.drop_table("le2_dimension_insights")
    op.drop_table("le2_industry_policies")
    op.drop_table("le2_context_factors")
    op.drop_table("learning2_records")
