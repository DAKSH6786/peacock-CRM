"""Writer Intelligence 2.0 — proprietary outcome decision system

Revision ID: 0019_writer_intelligence
Revises: 0018_geo_lab
Create Date: 2026-08-12
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0019_writer_intelligence"
down_revision: Union[str, None] = "0018_geo_lab"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "writer_intelligence_analyses",
        sa.Column("website_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("client_brand", sa.String(length=255), nullable=False),
        sa.Column("industry", sa.String(length=255), nullable=False),
        sa.Column("topic", sa.String(length=512), nullable=False),
        sa.Column("audience", sa.String(length=512), nullable=False),
        sa.Column("analysis_status", sa.String(length=32), nullable=False),
        sa.Column("methodology", sa.String(length=64), nullable=False),
        sa.Column("similarity_only_rejected", sa.Boolean(), nullable=False),
        sa.Column("similarity_rejection_note", sa.Text(), nullable=False),
        sa.Column("decision_question", sa.Text(), nullable=False),
        sa.Column("top_writer_key", sa.String(length=128), nullable=True),
        sa.Column("top_outcome_score", sa.Float(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_writer_intelligence_analyses_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_writer_intelligence_analyses_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["website_id"], ["websites.id"], name=op.f("fk_writer_intelligence_analyses_website_id_websites"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_writer_intelligence_analyses_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_writer_intelligence_analyses")),
    )
    for col in (
        "website_id", "client_brand", "industry", "topic", "analysis_status",
        "top_writer_key", "organisation_id", "workspace_id", "created_by", "status",
    ):
        op.create_index(op.f(f"ix_writer_intelligence_analyses_{col}"), "writer_intelligence_analyses", [col], unique=False)

    op.create_table(
        "wi_writer_dna",
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("writer_key", sa.String(length=128), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("dna_composite_score", sa.Float(), nullable=False),
        sa.Column("dna_summary", sa.Text(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["writer_intelligence_analyses.id"], name=op.f("fk_wi_writer_dna_analysis_id_writer_intelligence_analyses"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_wi_writer_dna_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_wi_writer_dna_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_wi_writer_dna_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_wi_writer_dna")),
        sa.UniqueConstraint("analysis_id", "writer_key", name=op.f("uq_wi_writer_dna_analysis_id")),
    )
    for col in ("analysis_id", "writer_key", "organisation_id", "workspace_id", "created_by", "status"):
        op.create_index(op.f(f"ix_wi_writer_dna_{col}"), "wi_writer_dna", [col], unique=False)

    op.create_table(
        "wi_dna_traits",
        sa.Column("dna_id", sa.String(length=36), nullable=False),
        sa.Column("trait_code", sa.String(length=64), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("evidence", sa.Text(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_wi_dna_traits_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["dna_id"], ["wi_writer_dna.id"], name=op.f("fk_wi_dna_traits_dna_id_wi_writer_dna"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_wi_dna_traits_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_wi_dna_traits_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_wi_dna_traits")),
        sa.UniqueConstraint("dna_id", "trait_code", name=op.f("uq_wi_dna_traits_dna_id")),
    )
    for col in ("dna_id", "trait_code", "organisation_id", "workspace_id", "created_by", "status"):
        op.create_index(op.f(f"ix_wi_dna_traits_{col}"), "wi_dna_traits", [col], unique=False)

    op.create_table(
        "wi_outcome_nodes",
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("node_kind", sa.String(length=32), nullable=False),
        sa.Column("node_key", sa.String(length=255), nullable=False),
        sa.Column("label", sa.String(length=512), nullable=False),
        sa.Column("attributes_json", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["writer_intelligence_analyses.id"], name=op.f("fk_wi_outcome_nodes_analysis_id_writer_intelligence_analyses"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_wi_outcome_nodes_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_wi_outcome_nodes_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_wi_outcome_nodes_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_wi_outcome_nodes")),
        sa.UniqueConstraint("analysis_id", "node_kind", "node_key", name=op.f("uq_wi_outcome_nodes_analysis_id")),
    )
    for col in ("analysis_id", "node_kind", "node_key", "organisation_id", "workspace_id", "created_by", "status"):
        op.create_index(op.f(f"ix_wi_outcome_nodes_{col}"), "wi_outcome_nodes", [col], unique=False)

    op.create_table(
        "wi_outcome_edges",
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("edge_type", sa.String(length=32), nullable=False),
        sa.Column("from_node_kind", sa.String(length=32), nullable=False),
        sa.Column("from_node_key", sa.String(length=255), nullable=False),
        sa.Column("to_node_kind", sa.String(length=32), nullable=False),
        sa.Column("to_node_key", sa.String(length=255), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["writer_intelligence_analyses.id"], name=op.f("fk_wi_outcome_edges_analysis_id_writer_intelligence_analyses"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_wi_outcome_edges_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_wi_outcome_edges_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_wi_outcome_edges_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_wi_outcome_edges")),
    )
    for col in ("analysis_id", "edge_type", "from_node_key", "to_node_key", "organisation_id", "workspace_id", "created_by", "status"):
        op.create_index(op.f(f"ix_wi_outcome_edges_{col}"), "wi_outcome_edges", [col], unique=False)

    op.create_table(
        "wi_performance_records",
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("article_key", sa.String(length=128), nullable=False),
        sa.Column("writer_key", sa.String(length=128), nullable=False),
        sa.Column("client_key", sa.String(length=128), nullable=False),
        sa.Column("industry", sa.String(length=255), nullable=False),
        sa.Column("topic", sa.String(length=512), nullable=False),
        sa.Column("approval", sa.Float(), nullable=True),
        sa.Column("revision_rounds", sa.Float(), nullable=True),
        sa.Column("ranking", sa.Float(), nullable=True),
        sa.Column("impressions", sa.Float(), nullable=True),
        sa.Column("ai_citations", sa.Float(), nullable=True),
        sa.Column("engagement", sa.Float(), nullable=True),
        sa.Column("links_earned", sa.Float(), nullable=True),
        sa.Column("conversion", sa.Float(), nullable=True),
        sa.Column("composite_outcome", sa.Float(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["writer_intelligence_analyses.id"], name=op.f("fk_wi_performance_records_analysis_id_writer_intelligence_analyses"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_wi_performance_records_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_wi_performance_records_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_wi_performance_records_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_wi_performance_records")),
        sa.UniqueConstraint("analysis_id", "article_key", name=op.f("uq_wi_performance_records_analysis_id")),
    )
    for col in ("analysis_id", "article_key", "writer_key", "client_key", "industry", "topic", "organisation_id", "workspace_id", "created_by", "status"):
        op.create_index(op.f(f"ix_wi_performance_records_{col}"), "wi_performance_records", [col], unique=False)

    op.create_table(
        "wi_recommendations",
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("writer_key", sa.String(length=128), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("predicted_outcome_score", sa.Float(), nullable=False),
        sa.Column("dna_fit_score", sa.Float(), nullable=False),
        sa.Column("topic_fit_score", sa.Float(), nullable=False),
        sa.Column("client_fit_score", sa.Float(), nullable=False),
        sa.Column("audience_fit_score", sa.Float(), nullable=False),
        sa.Column("historical_outcome_score", sa.Float(), nullable=False),
        sa.Column("similarity_score_unused", sa.Float(), nullable=True),
        sa.Column("similarity_not_used_as_primary", sa.Boolean(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("decision_answer", sa.Text(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["writer_intelligence_analyses.id"], name=op.f("fk_wi_recommendations_analysis_id_writer_intelligence_analyses"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_wi_recommendations_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_wi_recommendations_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_wi_recommendations_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_wi_recommendations")),
        sa.UniqueConstraint("analysis_id", "writer_key", name=op.f("uq_wi_recommendations_analysis_id")),
    )
    for col in ("analysis_id", "writer_key", "organisation_id", "workspace_id", "created_by", "status"):
        op.create_index(op.f(f"ix_wi_recommendations_{col}"), "wi_recommendations", [col], unique=False)


def downgrade() -> None:
    op.drop_table("wi_recommendations")
    op.drop_table("wi_performance_records")
    op.drop_table("wi_outcome_edges")
    op.drop_table("wi_outcome_nodes")
    op.drop_table("wi_dna_traits")
    op.drop_table("wi_writer_dna")
    op.drop_table("writer_intelligence_analyses")
