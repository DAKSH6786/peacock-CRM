"""Peacock Content Lab — multi-opportunity content evaluation

Revision ID: 0016_content_lab
Revises: 0015_deep_competitor
Create Date: 2026-08-12
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0016_content_lab"
down_revision: Union[str, None] = "0015_deep_competitor"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_table(
        "content_lab_analyses",
        sa.Column("website_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("client_brand", sa.String(length=255), nullable=False),
        sa.Column("topic_cluster", sa.String(length=255), nullable=True),
        sa.Column("analysis_status", sa.String(length=32), nullable=False),
        sa.Column("methodology", sa.String(length=64), nullable=False),
        sa.Column("proposal_count", sa.Integer(), nullable=False),
        sa.Column("citability_is_proprietary_estimate", sa.Boolean(), nullable=False),
        sa.Column("citability_disclaimer", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_content_lab_analyses_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_content_lab_analyses_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["website_id"], ["websites.id"], name=op.f("fk_content_lab_analyses_website_id_websites"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_content_lab_analyses_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_content_lab_analyses")),
    )
    op.create_index(op.f("ix_content_lab_analyses_topic_cluster"), "content_lab_analyses", ["topic_cluster"], unique=False)
    op.create_index(op.f("ix_content_lab_analyses_created_by"), "content_lab_analyses", ["created_by"], unique=False)
    op.create_index(op.f("ix_content_lab_analyses_analysis_status"), "content_lab_analyses", ["analysis_status"], unique=False)
    op.create_index(op.f("ix_content_lab_analyses_website_id"), "content_lab_analyses", ["website_id"], unique=False)
    op.create_index(op.f("ix_content_lab_analyses_organisation_id"), "content_lab_analyses", ["organisation_id"], unique=False)
    op.create_index(op.f("ix_content_lab_analyses_workspace_id"), "content_lab_analyses", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_content_lab_analyses_client_brand"), "content_lab_analyses", ["client_brand"], unique=False)
    op.create_index(op.f("ix_content_lab_analyses_status"), "content_lab_analyses", ["status"], unique=False)

    op.create_table(
        "cl_content_proposals",
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("content_format", sa.String(length=64), nullable=False),
        sa.Column("angle", sa.Text(), nullable=True),
        sa.Column("target_url", sa.String(length=2048), nullable=True),
        sa.Column("lab_priority_score", sa.Float(), nullable=False),
        sa.Column("seo_opportunity", sa.Float(), nullable=False),
        sa.Column("aeo_opportunity", sa.Float(), nullable=False),
        sa.Column("geo_opportunity", sa.Float(), nullable=False),
        sa.Column("ai_citation_opportunity", sa.Float(), nullable=False),
        sa.Column("business_value", sa.Float(), nullable=False),
        sa.Column("audience_relevance", sa.Float(), nullable=False),
        sa.Column("competitor_gap", sa.Float(), nullable=False),
        sa.Column("information_gain", sa.Float(), nullable=False),
        sa.Column("originality_opportunity", sa.Float(), nullable=False),
        sa.Column("topical_authority_impact", sa.Float(), nullable=False),
        sa.Column("conversion_potential", sa.Float(), nullable=False),
        sa.Column("backlink_potential", sa.Float(), nullable=False),
        sa.Column("entity_impact", sa.Float(), nullable=False),
        sa.Column("effort", sa.Float(), nullable=False),
        sa.Column("time_sensitivity", sa.Float(), nullable=False),
        sa.Column("information_gain_score", sa.Float(), nullable=False),
        sa.Column("content_moat_score", sa.Float(), nullable=False),
        sa.Column("generative_citability_score", sa.Float(), nullable=False),
        sa.Column("information_gain_breakdown", sa.Text(), nullable=True),
        sa.Column("moat_rationale", sa.Text(), nullable=True),
        sa.Column("citability_breakdown", sa.Text(), nullable=True),
        sa.Column("recommendation_summary", sa.Text(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_cl_content_proposals_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_cl_content_proposals_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_cl_content_proposals_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["analysis_id"], ["content_lab_analyses.id"], name=op.f("fk_cl_content_proposals_analysis_id_content_lab_analyses"), ondelete="CASCADE"),
        sa.UniqueConstraint("analysis_id", "slug", name=op.f("uq_cl_content_proposals_analysis_id_slug")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cl_content_proposals")),
    )
    op.create_index(op.f("ix_cl_content_proposals_created_by"), "cl_content_proposals", ["created_by"], unique=False)
    op.create_index(op.f("ix_cl_content_proposals_workspace_id"), "cl_content_proposals", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_cl_content_proposals_analysis_id"), "cl_content_proposals", ["analysis_id"], unique=False)
    op.create_index(op.f("ix_cl_content_proposals_slug"), "cl_content_proposals", ["slug"], unique=False)
    op.create_index(op.f("ix_cl_content_proposals_content_format"), "cl_content_proposals", ["content_format"], unique=False)
    op.create_index(op.f("ix_cl_content_proposals_organisation_id"), "cl_content_proposals", ["organisation_id"], unique=False)
    op.create_index(op.f("ix_cl_content_proposals_status"), "cl_content_proposals", ["status"], unique=False)

    op.create_table(
        "cl_info_gain_signals",
        sa.Column("proposal_id", sa.String(length=36), nullable=False),
        sa.Column("signal_code", sa.String(length=64), nullable=False),
        sa.Column("polarity", sa.String(length=16), nullable=False),
        sa.Column("strength", sa.Float(), nullable=False),
        sa.Column("evidence", sa.Text(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["proposal_id"], ["cl_content_proposals.id"], name=op.f("fk_cl_info_gain_signals_proposal_id_cl_content_proposals"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_cl_info_gain_signals_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_cl_info_gain_signals_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_cl_info_gain_signals_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cl_info_gain_signals")),
    )
    op.create_index(op.f("ix_cl_info_gain_signals_created_by"), "cl_info_gain_signals", ["created_by"], unique=False)
    op.create_index(op.f("ix_cl_info_gain_signals_status"), "cl_info_gain_signals", ["status"], unique=False)
    op.create_index(op.f("ix_cl_info_gain_signals_workspace_id"), "cl_info_gain_signals", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_cl_info_gain_signals_organisation_id"), "cl_info_gain_signals", ["organisation_id"], unique=False)
    op.create_index(op.f("ix_cl_info_gain_signals_proposal_id"), "cl_info_gain_signals", ["proposal_id"], unique=False)
    op.create_index(op.f("ix_cl_info_gain_signals_signal_code"), "cl_info_gain_signals", ["signal_code"], unique=False)

    op.create_table(
        "cl_citability_components",
        sa.Column("proposal_id", sa.String(length=36), nullable=False),
        sa.Column("component_code", sa.String(length=64), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_cl_citability_components_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_cl_citability_components_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_cl_citability_components_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["proposal_id"], ["cl_content_proposals.id"], name=op.f("fk_cl_citability_components_proposal_id_cl_content_proposals"), ondelete="CASCADE"),
        sa.UniqueConstraint("proposal_id", "component_code", name=op.f("uq_cl_citability_components_proposal_id_component_code")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cl_citability_components")),
    )
    op.create_index(op.f("ix_cl_citability_components_proposal_id"), "cl_citability_components", ["proposal_id"], unique=False)
    op.create_index(op.f("ix_cl_citability_components_workspace_id"), "cl_citability_components", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_cl_citability_components_status"), "cl_citability_components", ["status"], unique=False)
    op.create_index(op.f("ix_cl_citability_components_component_code"), "cl_citability_components", ["component_code"], unique=False)
    op.create_index(op.f("ix_cl_citability_components_created_by"), "cl_citability_components", ["created_by"], unique=False)
    op.create_index(op.f("ix_cl_citability_components_organisation_id"), "cl_citability_components", ["organisation_id"], unique=False)

def downgrade() -> None:
    op.drop_table("cl_citability_components")
    op.drop_table("cl_info_gain_signals")
    op.drop_table("cl_content_proposals")
    op.drop_table("content_lab_analyses")

