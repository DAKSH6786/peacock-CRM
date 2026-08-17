"""Peacock Revenue Attribution — visibility to business value with uncertainty

Revision ID: 0027_revenue_attribution
Revises: 0026_agentic_readiness
Create Date: 2026-08-12
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0027_revenue_attribution"
down_revision: Union[str, None] = "0026_agentic_readiness"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ix(table: str, cols: list[str]) -> None:
    for col in cols:
        op.create_index(op.f(f"ix_{table}_{col}"), table, [col], unique=False)


def upgrade() -> None:
    op.create_table(
        "revenue_attribution_analyses",
        sa.Column("website_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("client_brand", sa.String(length=255), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("horizon_days", sa.Integer(), nullable=False),
        sa.Column("analysis_status", sa.String(length=32), nullable=False),
        sa.Column("methodology", sa.String(length=64), nullable=False),
        sa.Column("causality_warning", sa.Text(), nullable=False),
        sa.Column("overall_causality_level", sa.String(length=32), nullable=False),
        sa.Column("overall_uncertainty", sa.Float(), nullable=False),
        sa.Column("data_completeness", sa.Float(), nullable=False),
        sa.Column("attributed_revenue_low", sa.Float(), nullable=False),
        sa.Column("attributed_revenue_high", sa.Float(), nullable=False),
        sa.Column("attributed_revenue_mid", sa.Float(), nullable=True),
        sa.Column("sources_available", sa.Text(), nullable=False),
        sa.Column("sources_missing", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_revenue_attribution_analyses_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_revenue_attribution_analyses_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["website_id"], ["websites.id"], name=op.f("fk_revenue_attribution_analyses_website_id_websites"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_revenue_attribution_analyses_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_revenue_attribution_analyses")),
    )
    _ix(
        "revenue_attribution_analyses",
        [
            "website_id",
            "client_brand",
            "analysis_status",
            "overall_causality_level",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "ra_funnel_stages",
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("stage_code", sa.String(length=32), nullable=False),
        sa.Column("stage_label", sa.String(length=64), nullable=False),
        sa.Column("sequence_order", sa.Integer(), nullable=False),
        sa.Column("value_low", sa.Float(), nullable=False),
        sa.Column("value_high", sa.Float(), nullable=False),
        sa.Column("value_mid", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(length=32), nullable=False),
        sa.Column("uncertainty", sa.Float(), nullable=False),
        sa.Column("data_quality", sa.Float(), nullable=False),
        sa.Column("primary_source", sa.String(length=64), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["revenue_attribution_analyses.id"], name=op.f("fk_ra_funnel_stages_analysis_id_revenue_attribution_analyses"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_ra_funnel_stages_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_ra_funnel_stages_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_ra_funnel_stages_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ra_funnel_stages")),
        sa.UniqueConstraint("analysis_id", "stage_code", name=op.f("uq_ra_funnel_stages_analysis_id")),
    )
    _ix(
        "ra_funnel_stages",
        ["analysis_id", "stage_code", "organisation_id", "workspace_id", "created_by", "status"],
    )

    op.create_table(
        "ra_chain_links",
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("from_stage", sa.String(length=32), nullable=False),
        sa.Column("to_stage", sa.String(length=32), nullable=False),
        sa.Column("rate_low", sa.Float(), nullable=False),
        sa.Column("rate_high", sa.Float(), nullable=False),
        sa.Column("causality_level", sa.String(length=32), nullable=False),
        sa.Column("uncertainty", sa.Float(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["revenue_attribution_analyses.id"], name=op.f("fk_ra_chain_links_analysis_id_revenue_attribution_analyses"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_ra_chain_links_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_ra_chain_links_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_ra_chain_links_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ra_chain_links")),
        sa.UniqueConstraint("analysis_id", "from_stage", "to_stage", name=op.f("uq_ra_chain_links_analysis_id")),
    )
    _ix(
        "ra_chain_links",
        [
            "analysis_id",
            "from_stage",
            "to_stage",
            "causality_level",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "ra_source_snapshots",
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("source_code", sa.String(length=64), nullable=False),
        sa.Column("source_label", sa.String(length=64), nullable=False),
        sa.Column("available", sa.Boolean(), nullable=False),
        sa.Column("contribution_note", sa.Text(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["revenue_attribution_analyses.id"], name=op.f("fk_ra_source_snapshots_analysis_id_revenue_attribution_analyses"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_ra_source_snapshots_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_ra_source_snapshots_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_ra_source_snapshots_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ra_source_snapshots")),
        sa.UniqueConstraint("analysis_id", "source_code", name=op.f("uq_ra_source_snapshots_analysis_id")),
    )
    _ix(
        "ra_source_snapshots",
        [
            "analysis_id",
            "source_code",
            "available",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )


def downgrade() -> None:
    op.drop_table("ra_source_snapshots")
    op.drop_table("ra_chain_links")
    op.drop_table("ra_funnel_stages")
    op.drop_table("revenue_attribution_analyses")
