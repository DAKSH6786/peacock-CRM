"""Peacock Moat Data Model — proprietary intelligence pathway accumulation

Revision ID: 0036_moat_data_model
Revises: 0035_research_mode
Create Date: 2026-08-13
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0036_moat_data_model"
down_revision: Union[str, None] = "0035_research_mode"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ix(table: str, cols: list[str]) -> None:
    for col in cols:
        op.create_index(op.f(f"ix_{table}_{col}"), table, [col], unique=False)


def upgrade() -> None:
    op.create_table(
        "moat_intelligence_runs",
        sa.Column("website_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("client_brand", sa.String(length=255), nullable=False),
        sa.Column("industry", sa.String(length=64), nullable=True),
        sa.Column("run_status", sa.String(length=32), nullable=False),
        sa.Column("methodology", sa.String(length=64), nullable=False),
        sa.Column("moat_positioning", sa.Text(), nullable=False),
        sa.Column("pathways_count", sa.Integer(), nullable=False),
        sa.Column("nodes_count", sa.Integer(), nullable=False),
        sa.Column("edges_count", sa.Integer(), nullable=False),
        sa.Column("outcomes_count", sa.Integer(), nullable=False),
        sa.Column("moat_strength_score", sa.Float(), nullable=False),
        sa.Column("mean_outcome_delta", sa.Float(), nullable=True),
        sa.Column("mean_confidence", sa.Float(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
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
            ["created_by"], ["users.id"], name=op.f("fk_moat_intelligence_runs_created_by_users"), ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["organisation_id"],
            ["organisations.id"],
            name=op.f("fk_moat_intelligence_runs_organisation_id_organisations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["website_id"],
            ["websites.id"],
            name=op.f("fk_moat_intelligence_runs_website_id_websites"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name=op.f("fk_moat_intelligence_runs_workspace_id_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_moat_intelligence_runs")),
    )
    _ix(
        "moat_intelligence_runs",
        [
            "website_id",
            "client_brand",
            "industry",
            "run_status",
            "analysed_at",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "moat_pathways",
        sa.Column("run_id", sa.String(length=36), nullable=False),
        sa.Column("pathway_kind", sa.String(length=64), nullable=False),
        sa.Column("pathway_label", sa.String(length=255), nullable=False),
        sa.Column("pathway_key", sa.String(length=128), nullable=False),
        sa.Column("industry", sa.String(length=64), nullable=True),
        sa.Column("topic_key", sa.String(length=128), nullable=True),
        sa.Column("expected_score", sa.Float(), nullable=True),
        sa.Column("actual_score", sa.Float(), nullable=True),
        sa.Column("outcome_delta", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("sample_weight", sa.Float(), nullable=False),
        sa.Column("source_system", sa.String(length=64), nullable=True),
        sa.Column("source_ref", sa.String(length=128), nullable=True),
        sa.Column("narrative", sa.Text(), nullable=False),
        sa.Column("rank_order", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by"], ["users.id"], name=op.f("fk_moat_pathways_created_by_users"), ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["organisation_id"],
            ["organisations.id"],
            name=op.f("fk_moat_pathways_organisation_id_organisations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["moat_intelligence_runs.id"],
            name=op.f("fk_moat_pathways_run_id_moat_intelligence_runs"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name=op.f("fk_moat_pathways_workspace_id_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_moat_pathways")),
        sa.UniqueConstraint("run_id", "pathway_key", name=op.f("uq_moat_pathways_run_id")),
    )
    _ix(
        "moat_pathways",
        [
            "run_id",
            "pathway_kind",
            "pathway_key",
            "industry",
            "topic_key",
            "source_system",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "moat_pathway_nodes",
        sa.Column("pathway_id", sa.String(length=36), nullable=False),
        sa.Column("node_ordinal", sa.Integer(), nullable=False),
        sa.Column("node_role", sa.String(length=32), nullable=False),
        sa.Column("node_kind", sa.String(length=64), nullable=False),
        sa.Column("node_key", sa.String(length=128), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by"], ["users.id"], name=op.f("fk_moat_pathway_nodes_created_by_users"), ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["organisation_id"],
            ["organisations.id"],
            name=op.f("fk_moat_pathway_nodes_organisation_id_organisations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["pathway_id"],
            ["moat_pathways.id"],
            name=op.f("fk_moat_pathway_nodes_pathway_id_moat_pathways"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name=op.f("fk_moat_pathway_nodes_workspace_id_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_moat_pathway_nodes")),
        sa.UniqueConstraint(
            "pathway_id", "node_ordinal", name=op.f("uq_moat_pathway_nodes_pathway_id")
        ),
    )
    _ix(
        "moat_pathway_nodes",
        [
            "pathway_id",
            "node_role",
            "node_kind",
            "node_key",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "moat_pathway_edges",
        sa.Column("pathway_id", sa.String(length=36), nullable=False),
        sa.Column("from_ordinal", sa.Integer(), nullable=False),
        sa.Column("to_ordinal", sa.Integer(), nullable=False),
        sa.Column("edge_type", sa.String(length=64), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by"], ["users.id"], name=op.f("fk_moat_pathway_edges_created_by_users"), ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["organisation_id"],
            ["organisations.id"],
            name=op.f("fk_moat_pathway_edges_organisation_id_organisations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["pathway_id"],
            ["moat_pathways.id"],
            name=op.f("fk_moat_pathway_edges_pathway_id_moat_pathways"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name=op.f("fk_moat_pathway_edges_workspace_id_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_moat_pathway_edges")),
        sa.UniqueConstraint(
            "pathway_id",
            "from_ordinal",
            "to_ordinal",
            "edge_type",
            name=op.f("uq_moat_pathway_edges_pathway_id"),
        ),
    )
    _ix(
        "moat_pathway_edges",
        [
            "pathway_id",
            "edge_type",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "moat_pathway_outcomes",
        sa.Column("pathway_id", sa.String(length=36), nullable=False),
        sa.Column("metric_key", sa.String(length=128), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=False),
        sa.Column("baseline_value", sa.Float(), nullable=True),
        sa.Column("delta", sa.Float(), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("provenance", sa.String(length=255), nullable=True),
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
            name=op.f("fk_moat_pathway_outcomes_created_by_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["organisation_id"],
            ["organisations.id"],
            name=op.f("fk_moat_pathway_outcomes_organisation_id_organisations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["pathway_id"],
            ["moat_pathways.id"],
            name=op.f("fk_moat_pathway_outcomes_pathway_id_moat_pathways"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name=op.f("fk_moat_pathway_outcomes_workspace_id_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_moat_pathway_outcomes")),
        sa.UniqueConstraint(
            "pathway_id",
            "metric_key",
            "observed_at",
            name=op.f("uq_moat_pathway_outcomes_pathway_id"),
        ),
    )
    _ix(
        "moat_pathway_outcomes",
        [
            "pathway_id",
            "metric_key",
            "observed_at",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )


def downgrade() -> None:
    op.drop_table("moat_pathway_outcomes")
    op.drop_table("moat_pathway_edges")
    op.drop_table("moat_pathway_nodes")
    op.drop_table("moat_pathways")
    op.drop_table("moat_intelligence_runs")
