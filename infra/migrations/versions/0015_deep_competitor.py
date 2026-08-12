"""Deep Competitor Intelligence — multi-category discovery and deltas

Revision ID: 0015_deep_competitor
Revises: 0014_entity_intelligence
Create Date: 2026-08-12
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0015_deep_competitor"
down_revision: Union[str, None] = "0014_entity_intelligence"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_table(
        "deep_competitor_analyses",
        sa.Column("website_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("client_brand", sa.String(length=255), nullable=False),
        sa.Column("client_domain", sa.String(length=255), nullable=False),
        sa.Column("topic_cluster", sa.String(length=255), nullable=True),
        sa.Column("analysis_status", sa.String(length=32), nullable=False),
        sa.Column("methodology", sa.String(length=64), nullable=False),
        sa.Column("copy_competitor_content_rejected", sa.Boolean(), nullable=False),
        sa.Column("discovered_count", sa.Integer(), nullable=False),
        sa.Column("delta_count", sa.Integer(), nullable=False),
        sa.Column("content_diff_count", sa.Integer(), nullable=False),
        sa.Column("strategy_count", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_deep_competitor_analyses_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["website_id"], ["websites.id"], name=op.f("fk_deep_competitor_analyses_website_id_websites"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_deep_competitor_analyses_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_deep_competitor_analyses_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_deep_competitor_analyses")),
    )
    op.create_index(op.f("ix_deep_competitor_analyses_topic_cluster"), "deep_competitor_analyses", ["topic_cluster"], unique=False)
    op.create_index(op.f("ix_deep_competitor_analyses_status"), "deep_competitor_analyses", ["status"], unique=False)
    op.create_index(op.f("ix_deep_competitor_analyses_analysis_status"), "deep_competitor_analyses", ["analysis_status"], unique=False)
    op.create_index(op.f("ix_deep_competitor_analyses_client_brand"), "deep_competitor_analyses", ["client_brand"], unique=False)
    op.create_index(op.f("ix_deep_competitor_analyses_created_by"), "deep_competitor_analyses", ["created_by"], unique=False)
    op.create_index(op.f("ix_deep_competitor_analyses_website_id"), "deep_competitor_analyses", ["website_id"], unique=False)
    op.create_index(op.f("ix_deep_competitor_analyses_client_domain"), "deep_competitor_analyses", ["client_domain"], unique=False)
    op.create_index(op.f("ix_deep_competitor_analyses_workspace_id"), "deep_competitor_analyses", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_deep_competitor_analyses_organisation_id"), "deep_competitor_analyses", ["organisation_id"], unique=False)

    op.create_table(
        "dc_competitor_profiles",
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=False),
        sa.Column("categories", sa.String(length=512), nullable=False),
        sa.Column("discovery_method", sa.String(length=64), nullable=False),
        sa.Column("serp_overlap", sa.Float(), nullable=False),
        sa.Column("keyword_overlap", sa.Float(), nullable=False),
        sa.Column("topic_overlap", sa.Float(), nullable=False),
        sa.Column("ai_mention_overlap", sa.Float(), nullable=False),
        sa.Column("citation_overlap", sa.Float(), nullable=False),
        sa.Column("entity_similarity", sa.Float(), nullable=False),
        sa.Column("product_similarity", sa.Float(), nullable=False),
        sa.Column("overall_rivalry_score", sa.Float(), nullable=False),
        sa.Column("is_direct_business_competitor", sa.Boolean(), nullable=False),
        sa.Column("discovery_rationale", sa.Text(), nullable=False),
        sa.Column("legacy_competitor_id", sa.String(length=36), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["legacy_competitor_id"], ["competitors.id"], name=op.f("fk_dc_competitor_profiles_legacy_competitor_id_competitors"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["analysis_id"], ["deep_competitor_analyses.id"], name=op.f("fk_dc_competitor_profiles_analysis_id_deep_competitor_analyses"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_dc_competitor_profiles_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_dc_competitor_profiles_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_dc_competitor_profiles_organisation_id_organisations"), ondelete="CASCADE"),
        sa.UniqueConstraint("analysis_id", "domain", name=op.f("uq_dc_competitor_profiles_analysis_id_domain")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dc_competitor_profiles")),
    )
    op.create_index(op.f("ix_dc_competitor_profiles_domain"), "dc_competitor_profiles", ["domain"], unique=False)
    op.create_index(op.f("ix_dc_competitor_profiles_legacy_competitor_id"), "dc_competitor_profiles", ["legacy_competitor_id"], unique=False)
    op.create_index(op.f("ix_dc_competitor_profiles_organisation_id"), "dc_competitor_profiles", ["organisation_id"], unique=False)
    op.create_index(op.f("ix_dc_competitor_profiles_analysis_id"), "dc_competitor_profiles", ["analysis_id"], unique=False)
    op.create_index(op.f("ix_dc_competitor_profiles_status"), "dc_competitor_profiles", ["status"], unique=False)
    op.create_index(op.f("ix_dc_competitor_profiles_created_by"), "dc_competitor_profiles", ["created_by"], unique=False)
    op.create_index(op.f("ix_dc_competitor_profiles_discovery_method"), "dc_competitor_profiles", ["discovery_method"], unique=False)
    op.create_index(op.f("ix_dc_competitor_profiles_workspace_id"), "dc_competitor_profiles", ["workspace_id"], unique=False)

    op.create_table(
        "dc_competitive_deltas",
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("competitor_domain", sa.String(length=255), nullable=False),
        sa.Column("competitor_name", sa.String(length=255), nullable=False),
        sa.Column("dimension", sa.String(length=64), nullable=False),
        sa.Column("where_stronger", sa.Text(), nullable=False),
        sa.Column("why_stronger", sa.Text(), nullable=False),
        sa.Column("gap_difficulty", sa.String(length=16), nullable=False),
        sa.Column("gap_difficulty_score", sa.Float(), nullable=False),
        sa.Column("how_to_close", sa.Text(), nullable=False),
        sa.Column("how_to_leapfrog", sa.Text(), nullable=False),
        sa.Column("client_score", sa.Float(), nullable=False),
        sa.Column("competitor_score", sa.Float(), nullable=False),
        sa.Column("delta", sa.Float(), nullable=False),
        sa.Column("evidence", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_dc_competitive_deltas_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["analysis_id"], ["deep_competitor_analyses.id"], name=op.f("fk_dc_competitive_deltas_analysis_id_deep_competitor_analyses"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_dc_competitive_deltas_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_dc_competitive_deltas_created_by_users"), ondelete="SET NULL"),
        sa.UniqueConstraint("analysis_id", "competitor_domain", "dimension", name=op.f("uq_dc_competitive_deltas_analysis_id_competitor_domain_dimension")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dc_competitive_deltas")),
    )
    op.create_index(op.f("ix_dc_competitive_deltas_analysis_id"), "dc_competitive_deltas", ["analysis_id"], unique=False)
    op.create_index(op.f("ix_dc_competitive_deltas_gap_difficulty"), "dc_competitive_deltas", ["gap_difficulty"], unique=False)
    op.create_index(op.f("ix_dc_competitive_deltas_competitor_domain"), "dc_competitive_deltas", ["competitor_domain"], unique=False)
    op.create_index(op.f("ix_dc_competitive_deltas_organisation_id"), "dc_competitive_deltas", ["organisation_id"], unique=False)
    op.create_index(op.f("ix_dc_competitive_deltas_dimension"), "dc_competitive_deltas", ["dimension"], unique=False)
    op.create_index(op.f("ix_dc_competitive_deltas_status"), "dc_competitive_deltas", ["status"], unique=False)
    op.create_index(op.f("ix_dc_competitive_deltas_created_by"), "dc_competitive_deltas", ["created_by"], unique=False)
    op.create_index(op.f("ix_dc_competitive_deltas_workspace_id"), "dc_competitive_deltas", ["workspace_id"], unique=False)

    op.create_table(
        "dc_content_diffs",
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("competitor_domain", sa.String(length=255), nullable=False),
        sa.Column("competitor_url", sa.String(length=2048), nullable=False),
        sa.Column("client_url", sa.String(length=2048), nullable=True),
        sa.Column("dimension", sa.String(length=64), nullable=False),
        sa.Column("competitor_advantage", sa.Boolean(), nullable=False),
        sa.Column("client_score", sa.Float(), nullable=False),
        sa.Column("competitor_score", sa.Float(), nullable=False),
        sa.Column("evidence_summary", sa.Text(), nullable=False),
        sa.Column("differentiated_recommendation", sa.Text(), nullable=False),
        sa.Column("copy_rejected", sa.Boolean(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_dc_content_diffs_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["analysis_id"], ["deep_competitor_analyses.id"], name=op.f("fk_dc_content_diffs_analysis_id_deep_competitor_analyses"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_dc_content_diffs_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_dc_content_diffs_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dc_content_diffs")),
    )
    op.create_index(op.f("ix_dc_content_diffs_status"), "dc_content_diffs", ["status"], unique=False)
    op.create_index(op.f("ix_dc_content_diffs_analysis_id"), "dc_content_diffs", ["analysis_id"], unique=False)
    op.create_index(op.f("ix_dc_content_diffs_competitor_domain"), "dc_content_diffs", ["competitor_domain"], unique=False)
    op.create_index(op.f("ix_dc_content_diffs_created_by"), "dc_content_diffs", ["created_by"], unique=False)
    op.create_index(op.f("ix_dc_content_diffs_dimension"), "dc_content_diffs", ["dimension"], unique=False)
    op.create_index(op.f("ix_dc_content_diffs_workspace_id"), "dc_content_diffs", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_dc_content_diffs_organisation_id"), "dc_content_diffs", ["organisation_id"], unique=False)

    op.create_table(
        "dc_differentiated_strategies",
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("competitor_domain", sa.String(length=255), nullable=True),
        sa.Column("priority", sa.String(length=16), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("differentiated_moves", sa.Text(), nullable=False),
        sa.Column("leapfrog_angle", sa.Text(), nullable=False),
        sa.Column("copy_competitor_content_rejected", sa.Boolean(), nullable=False),
        sa.Column("forbidden_modes_note", sa.Text(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_dc_differentiated_strategies_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["analysis_id"], ["deep_competitor_analyses.id"], name=op.f("fk_dc_differentiated_strategies_analysis_id_deep_competitor_analyses"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_dc_differentiated_strategies_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_dc_differentiated_strategies_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dc_differentiated_strategies")),
    )
    op.create_index(op.f("ix_dc_differentiated_strategies_created_by"), "dc_differentiated_strategies", ["created_by"], unique=False)
    op.create_index(op.f("ix_dc_differentiated_strategies_organisation_id"), "dc_differentiated_strategies", ["organisation_id"], unique=False)
    op.create_index(op.f("ix_dc_differentiated_strategies_workspace_id"), "dc_differentiated_strategies", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_dc_differentiated_strategies_competitor_domain"), "dc_differentiated_strategies", ["competitor_domain"], unique=False)
    op.create_index(op.f("ix_dc_differentiated_strategies_analysis_id"), "dc_differentiated_strategies", ["analysis_id"], unique=False)
    op.create_index(op.f("ix_dc_differentiated_strategies_priority"), "dc_differentiated_strategies", ["priority"], unique=False)
    op.create_index(op.f("ix_dc_differentiated_strategies_status"), "dc_differentiated_strategies", ["status"], unique=False)

def downgrade() -> None:
    op.drop_table("dc_differentiated_strategies")
    op.drop_table("dc_content_diffs")
    op.drop_table("dc_competitive_deltas")
    op.drop_table("dc_competitor_profiles")
    op.drop_table("deep_competitor_analyses")

