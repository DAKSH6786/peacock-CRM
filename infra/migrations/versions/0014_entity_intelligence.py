"""Peacock Entity Intelligence — associations, gaps, strategy

Revision ID: 0014_entity_intelligence
Revises: 0013_retrieval_pathway
Create Date: 2026-08-12
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0014_entity_intelligence"
down_revision: Union[str, None] = "0013_retrieval_pathway"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_table(
        "entity_intelligence_analyses",
        sa.Column("website_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("client_brand", sa.String(length=255), nullable=False),
        sa.Column("industry", sa.String(length=255), nullable=True),
        sa.Column("analysis_status", sa.String(length=32), nullable=False),
        sa.Column("methodology", sa.String(length=64), nullable=False),
        sa.Column("entity_count", sa.Integer(), nullable=False),
        sa.Column("association_count", sa.Integer(), nullable=False),
        sa.Column("gap_count", sa.Integer(), nullable=False),
        sa.Column("strategy_count", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_entity_intelligence_analyses_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["website_id"], ["websites.id"], name=op.f("fk_entity_intelligence_analyses_website_id_websites"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_entity_intelligence_analyses_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_entity_intelligence_analyses_created_by_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_entity_intelligence_analyses")),
    )
    op.create_index(op.f("ix_entity_intelligence_analyses_client_brand"), "entity_intelligence_analyses", ["client_brand"], unique=False)
    op.create_index(op.f("ix_entity_intelligence_analyses_website_id"), "entity_intelligence_analyses", ["website_id"], unique=False)
    op.create_index(op.f("ix_entity_intelligence_analyses_organisation_id"), "entity_intelligence_analyses", ["organisation_id"], unique=False)
    op.create_index(op.f("ix_entity_intelligence_analyses_status"), "entity_intelligence_analyses", ["status"], unique=False)
    op.create_index(op.f("ix_entity_intelligence_analyses_industry"), "entity_intelligence_analyses", ["industry"], unique=False)
    op.create_index(op.f("ix_entity_intelligence_analyses_created_by"), "entity_intelligence_analyses", ["created_by"], unique=False)
    op.create_index(op.f("ix_entity_intelligence_analyses_analysis_status"), "entity_intelligence_analyses", ["analysis_status"], unique=False)
    op.create_index(op.f("ix_entity_intelligence_analyses_workspace_id"), "entity_intelligence_analyses", ["workspace_id"], unique=False)

    op.create_table(
        "ei_entities",
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("canonical_name", sa.String(length=255), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("is_client", sa.Boolean(), nullable=False),
        sa.Column("is_competitor", sa.Boolean(), nullable=False),
        sa.Column("aliases", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("ownership_brand", sa.String(length=255), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_ei_entities_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_ei_entities_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_ei_entities_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["analysis_id"], ["entity_intelligence_analyses.id"], name=op.f("fk_ei_entities_analysis_id_entity_intelligence_analyses"), ondelete="CASCADE"),
        sa.UniqueConstraint("analysis_id", "canonical_name", "entity_type", name=op.f("uq_ei_entities_analysis_id_canonical_name_entity_type")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ei_entities")),
    )
    op.create_index(op.f("ix_ei_entities_workspace_id"), "ei_entities", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_ei_entities_created_by"), "ei_entities", ["created_by"], unique=False)
    op.create_index(op.f("ix_ei_entities_canonical_name"), "ei_entities", ["canonical_name"], unique=False)
    op.create_index(op.f("ix_ei_entities_is_competitor"), "ei_entities", ["is_competitor"], unique=False)
    op.create_index(op.f("ix_ei_entities_is_client"), "ei_entities", ["is_client"], unique=False)
    op.create_index(op.f("ix_ei_entities_organisation_id"), "ei_entities", ["organisation_id"], unique=False)
    op.create_index(op.f("ix_ei_entities_analysis_id"), "ei_entities", ["analysis_id"], unique=False)
    op.create_index(op.f("ix_ei_entities_status"), "ei_entities", ["status"], unique=False)
    op.create_index(op.f("ix_ei_entities_entity_type"), "ei_entities", ["entity_type"], unique=False)
    op.create_index(op.f("ix_ei_entities_ownership_brand"), "ei_entities", ["ownership_brand"], unique=False)

    op.create_table(
        "ei_associations",
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("source_entity_name", sa.String(length=255), nullable=False),
        sa.Column("source_entity_type", sa.String(length=64), nullable=False),
        sa.Column("target_entity_name", sa.String(length=255), nullable=False),
        sa.Column("target_entity_type", sa.String(length=64), nullable=False),
        sa.Column("is_client_owned", sa.Boolean(), nullable=False),
        sa.Column("is_competitor_owned", sa.Boolean(), nullable=False),
        sa.Column("association_strength", sa.Float(), nullable=False),
        sa.Column("co_occurrence", sa.Float(), nullable=False),
        sa.Column("semantic_proximity", sa.Float(), nullable=False),
        sa.Column("ownership_signal", sa.Float(), nullable=False),
        sa.Column("citation_linkage", sa.Float(), nullable=False),
        sa.Column("topical_centrality", sa.Float(), nullable=False),
        sa.Column("recency", sa.Float(), nullable=False),
        sa.Column("cross_source_consistency", sa.Float(), nullable=False),
        sa.Column("observation_count", sa.Integer(), nullable=False),
        sa.Column("component_explanations", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["entity_intelligence_analyses.id"], name=op.f("fk_ei_associations_analysis_id_entity_intelligence_analyses"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_ei_associations_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_ei_associations_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_ei_associations_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.UniqueConstraint("analysis_id", "source_entity_name", "target_entity_name", name=op.f("uq_ei_associations_analysis_id_source_entity_name_target_entity_name")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ei_associations")),
    )
    op.create_index(op.f("ix_ei_associations_source_entity_type"), "ei_associations", ["source_entity_type"], unique=False)
    op.create_index(op.f("ix_ei_associations_organisation_id"), "ei_associations", ["organisation_id"], unique=False)
    op.create_index(op.f("ix_ei_associations_is_client_owned"), "ei_associations", ["is_client_owned"], unique=False)
    op.create_index(op.f("ix_ei_associations_analysis_id"), "ei_associations", ["analysis_id"], unique=False)
    op.create_index(op.f("ix_ei_associations_status"), "ei_associations", ["status"], unique=False)
    op.create_index(op.f("ix_ei_associations_target_entity_name"), "ei_associations", ["target_entity_name"], unique=False)
    op.create_index(op.f("ix_ei_associations_created_by"), "ei_associations", ["created_by"], unique=False)
    op.create_index(op.f("ix_ei_associations_workspace_id"), "ei_associations", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_ei_associations_target_entity_type"), "ei_associations", ["target_entity_type"], unique=False)
    op.create_index(op.f("ix_ei_associations_source_entity_name"), "ei_associations", ["source_entity_name"], unique=False)

    op.create_table(
        "ei_entity_gaps",
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("target_concept", sa.String(length=255), nullable=False),
        sa.Column("target_entity_type", sa.String(length=64), nullable=False),
        sa.Column("client_brand", sa.String(length=255), nullable=False),
        sa.Column("client_association", sa.Float(), nullable=False),
        sa.Column("leading_competitor_name", sa.String(length=255), nullable=True),
        sa.Column("leading_competitor_association", sa.Float(), nullable=False),
        sa.Column("competitor_associations_json", sa.Text(), nullable=True),
        sa.Column("gap_size", sa.Float(), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["entity_intelligence_analyses.id"], name=op.f("fk_ei_entity_gaps_analysis_id_entity_intelligence_analyses"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_ei_entity_gaps_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_ei_entity_gaps_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_ei_entity_gaps_organisation_id_organisations"), ondelete="CASCADE"),
        sa.UniqueConstraint("analysis_id", "target_concept", name=op.f("uq_ei_entity_gaps_analysis_id_target_concept")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ei_entity_gaps")),
    )
    op.create_index(op.f("ix_ei_entity_gaps_workspace_id"), "ei_entity_gaps", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_ei_entity_gaps_analysis_id"), "ei_entity_gaps", ["analysis_id"], unique=False)
    op.create_index(op.f("ix_ei_entity_gaps_created_by"), "ei_entity_gaps", ["created_by"], unique=False)
    op.create_index(op.f("ix_ei_entity_gaps_target_concept"), "ei_entity_gaps", ["target_concept"], unique=False)
    op.create_index(op.f("ix_ei_entity_gaps_status"), "ei_entity_gaps", ["status"], unique=False)
    op.create_index(op.f("ix_ei_entity_gaps_severity"), "ei_entity_gaps", ["severity"], unique=False)
    op.create_index(op.f("ix_ei_entity_gaps_organisation_id"), "ei_entity_gaps", ["organisation_id"], unique=False)

    op.create_table(
        "ei_strategies",
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("gap_id", sa.String(length=36), nullable=True),
        sa.Column("target_concept", sa.String(length=255), nullable=False),
        sa.Column("action_type", sa.String(length=64), nullable=False),
        sa.Column("priority", sa.String(length=16), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("recommended_moves", sa.Text(), nullable=False),
        sa.Column("expected_association_lift", sa.Float(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["entity_intelligence_analyses.id"], name=op.f("fk_ei_strategies_analysis_id_entity_intelligence_analyses"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["gap_id"], ["ei_entity_gaps.id"], name=op.f("fk_ei_strategies_gap_id_ei_entity_gaps"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_ei_strategies_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_ei_strategies_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_ei_strategies_created_by_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ei_strategies")),
    )
    op.create_index(op.f("ix_ei_strategies_action_type"), "ei_strategies", ["action_type"], unique=False)
    op.create_index(op.f("ix_ei_strategies_created_by"), "ei_strategies", ["created_by"], unique=False)
    op.create_index(op.f("ix_ei_strategies_analysis_id"), "ei_strategies", ["analysis_id"], unique=False)
    op.create_index(op.f("ix_ei_strategies_target_concept"), "ei_strategies", ["target_concept"], unique=False)
    op.create_index(op.f("ix_ei_strategies_priority"), "ei_strategies", ["priority"], unique=False)
    op.create_index(op.f("ix_ei_strategies_workspace_id"), "ei_strategies", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_ei_strategies_organisation_id"), "ei_strategies", ["organisation_id"], unique=False)
    op.create_index(op.f("ix_ei_strategies_status"), "ei_strategies", ["status"], unique=False)
    op.create_index(op.f("ix_ei_strategies_gap_id"), "ei_strategies", ["gap_id"], unique=False)

def downgrade() -> None:
    op.drop_table("ei_strategies")
    op.drop_table("ei_entity_gaps")
    op.drop_table("ei_associations")
    op.drop_table("ei_entities")
    op.drop_table("entity_intelligence_analyses")

