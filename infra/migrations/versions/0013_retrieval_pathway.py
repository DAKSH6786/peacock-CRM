"""Retrieval Pathway Intelligence — inferred citation forensics

Revision ID: 0013_retrieval_pathway
Revises: 0012_citation_graph
Create Date: 2026-08-12
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0013_retrieval_pathway"
down_revision: Union[str, None] = "0012_citation_graph"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_table(
        "retrieval_pathway_analyses",
        sa.Column("website_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("query_cluster", sa.String(length=255), nullable=False),
        sa.Column("client_brand", sa.String(length=255), nullable=False),
        sa.Column("target_url", sa.String(length=2048), nullable=False),
        sa.Column("target_domain", sa.String(length=255), nullable=False),
        sa.Column("analysis_status", sa.String(length=32), nullable=False),
        sa.Column("methodology", sa.String(length=64), nullable=False),
        sa.Column("proprietary_ranking_access_claimed", sa.Boolean(), nullable=False),
        sa.Column("methodology_disclaimer", sa.Text(), nullable=False),
        sa.Column("primary_bottleneck_stage", sa.String(length=32), nullable=True),
        sa.Column("primary_bottleneck_label", sa.String(length=128), nullable=True),
        sa.Column("estimated_retrieval_likelihood", sa.Float(), nullable=True),
        sa.Column("estimated_selection_likelihood", sa.Float(), nullable=True),
        sa.Column("retrieval_likelihood_band", sa.String(length=16), nullable=True),
        sa.Column("selection_likelihood_band", sa.String(length=16), nullable=True),
        sa.Column("overall_uncertainty", sa.String(length=16), nullable=True),
        sa.Column("interpretation", sa.Text(), nullable=True),
        sa.Column("recommended_investigation", sa.String(length=255), nullable=True),
        sa.Column("observation_count", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_retrieval_pathway_analyses_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_retrieval_pathway_analyses_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_retrieval_pathway_analyses_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["website_id"], ["websites.id"], name=op.f("fk_retrieval_pathway_analyses_website_id_websites"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_retrieval_pathway_analyses")),
    )
    op.create_index(op.f("ix_retrieval_pathway_analyses_target_domain"), "retrieval_pathway_analyses", ["target_domain"], unique=False)
    op.create_index(op.f("ix_retrieval_pathway_analyses_query_cluster"), "retrieval_pathway_analyses", ["query_cluster"], unique=False)
    op.create_index(op.f("ix_retrieval_pathway_analyses_workspace_id"), "retrieval_pathway_analyses", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_retrieval_pathway_analyses_website_id"), "retrieval_pathway_analyses", ["website_id"], unique=False)
    op.create_index(op.f("ix_retrieval_pathway_analyses_analysis_status"), "retrieval_pathway_analyses", ["analysis_status"], unique=False)
    op.create_index(op.f("ix_retrieval_pathway_analyses_organisation_id"), "retrieval_pathway_analyses", ["organisation_id"], unique=False)
    op.create_index(op.f("ix_retrieval_pathway_analyses_client_brand"), "retrieval_pathway_analyses", ["client_brand"], unique=False)
    op.create_index(op.f("ix_retrieval_pathway_analyses_status"), "retrieval_pathway_analyses", ["status"], unique=False)
    op.create_index(op.f("ix_retrieval_pathway_analyses_created_by"), "retrieval_pathway_analyses", ["created_by"], unique=False)
    op.create_index(op.f("ix_retrieval_pathway_analyses_primary_bottleneck_stage"), "retrieval_pathway_analyses", ["primary_bottleneck_stage"], unique=False)

    op.create_table(
        "rpi_evidence",
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("evidence_code", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("observed_value", sa.Float(), nullable=True),
        sa.Column("observed_text", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["retrieval_pathway_analyses.id"], name=op.f("fk_rpi_evidence_analysis_id_retrieval_pathway_analyses"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_rpi_evidence_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_rpi_evidence_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_rpi_evidence_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_rpi_evidence")),
    )
    op.create_index(op.f("ix_rpi_evidence_organisation_id"), "rpi_evidence", ["organisation_id"], unique=False)
    op.create_index(op.f("ix_rpi_evidence_analysis_id"), "rpi_evidence", ["analysis_id"], unique=False)
    op.create_index(op.f("ix_rpi_evidence_created_by"), "rpi_evidence", ["created_by"], unique=False)
    op.create_index(op.f("ix_rpi_evidence_status"), "rpi_evidence", ["status"], unique=False)
    op.create_index(op.f("ix_rpi_evidence_workspace_id"), "rpi_evidence", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_rpi_evidence_evidence_code"), "rpi_evidence", ["evidence_code"], unique=False)

    op.create_table(
        "rpi_cause_classifications",
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("cause_code", sa.String(length=64), nullable=False),
        sa.Column("estimated_likelihood", sa.Float(), nullable=False),
        sa.Column("likelihood_band", sa.String(length=16), nullable=False),
        sa.Column("uncertainty", sa.String(length=16), nullable=False),
        sa.Column("supporting_evidence", sa.Text(), nullable=True),
        sa.Column("contrary_evidence", sa.Text(), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["retrieval_pathway_analyses.id"], name=op.f("fk_rpi_cause_classifications_analysis_id_retrieval_pathway_analyses"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_rpi_cause_classifications_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_rpi_cause_classifications_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_rpi_cause_classifications_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.UniqueConstraint("analysis_id", "cause_code", name=op.f("uq_rpi_cause_classifications_analysis_id_cause_code")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_rpi_cause_classifications")),
    )
    op.create_index(op.f("ix_rpi_cause_classifications_created_by"), "rpi_cause_classifications", ["created_by"], unique=False)
    op.create_index(op.f("ix_rpi_cause_classifications_status"), "rpi_cause_classifications", ["status"], unique=False)
    op.create_index(op.f("ix_rpi_cause_classifications_is_primary"), "rpi_cause_classifications", ["is_primary"], unique=False)
    op.create_index(op.f("ix_rpi_cause_classifications_cause_code"), "rpi_cause_classifications", ["cause_code"], unique=False)
    op.create_index(op.f("ix_rpi_cause_classifications_workspace_id"), "rpi_cause_classifications", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_rpi_cause_classifications_organisation_id"), "rpi_cause_classifications", ["organisation_id"], unique=False)
    op.create_index(op.f("ix_rpi_cause_classifications_analysis_id"), "rpi_cause_classifications", ["analysis_id"], unique=False)

    op.create_table(
        "rpi_bottleneck_diagnoses",
        sa.Column("analysis_id", sa.String(length=36), nullable=False),
        sa.Column("bottleneck_stage", sa.String(length=32), nullable=False),
        sa.Column("headline", sa.String(length=255), nullable=False),
        sa.Column("retrieval_probability_band", sa.String(length=16), nullable=False),
        sa.Column("citation_selection_band", sa.String(length=16), nullable=False),
        sa.Column("estimated_retrieval_likelihood", sa.Float(), nullable=False),
        sa.Column("estimated_selection_likelihood", sa.Float(), nullable=False),
        sa.Column("interpretation", sa.Text(), nullable=False),
        sa.Column("recommended_investigation", sa.String(length=255), nullable=False),
        sa.Column("uncertainty", sa.String(length=16), nullable=False),
        sa.Column("disclaimer", sa.Text(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_rpi_bottleneck_diagnoses_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_rpi_bottleneck_diagnoses_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_rpi_bottleneck_diagnoses_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["analysis_id"], ["retrieval_pathway_analyses.id"], name=op.f("fk_rpi_bottleneck_diagnoses_analysis_id_retrieval_pathway_analyses"), ondelete="CASCADE"),
        sa.UniqueConstraint("analysis_id", name=op.f("uq_rpi_bottleneck_diagnoses_analysis_id")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_rpi_bottleneck_diagnoses")),
    )
    op.create_index(op.f("ix_rpi_bottleneck_diagnoses_created_by"), "rpi_bottleneck_diagnoses", ["created_by"], unique=False)
    op.create_index(op.f("ix_rpi_bottleneck_diagnoses_status"), "rpi_bottleneck_diagnoses", ["status"], unique=False)
    op.create_index(op.f("ix_rpi_bottleneck_diagnoses_analysis_id"), "rpi_bottleneck_diagnoses", ["analysis_id"], unique=False)
    op.create_index(op.f("ix_rpi_bottleneck_diagnoses_organisation_id"), "rpi_bottleneck_diagnoses", ["organisation_id"], unique=False)
    op.create_index(op.f("ix_rpi_bottleneck_diagnoses_workspace_id"), "rpi_bottleneck_diagnoses", ["workspace_id"], unique=False)
    op.create_index(op.f("ix_rpi_bottleneck_diagnoses_bottleneck_stage"), "rpi_bottleneck_diagnoses", ["bottleneck_stage"], unique=False)

def downgrade() -> None:
    op.drop_table("rpi_bottleneck_diagnoses")
    op.drop_table("rpi_cause_classifications")
    op.drop_table("rpi_evidence")
    op.drop_table("retrieval_pathway_analyses")

