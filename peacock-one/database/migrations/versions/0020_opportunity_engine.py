"""Peacock Opportunity Engine — always-on intelligence layer

Revision ID: 0020_opportunity_engine
Revises: 0019_writer_intelligence
Create Date: 2026-08-12
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0020_opportunity_engine"
down_revision: Union[str, None] = "0019_writer_intelligence"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "opportunity_scans",
        sa.Column("website_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("client_brand", sa.String(length=255), nullable=False),
        sa.Column("scan_status", sa.String(length=32), nullable=False),
        sa.Column("methodology", sa.String(length=64), nullable=False),
        sa.Column("always_on_layer", sa.Boolean(), nullable=False),
        sa.Column("ranking_model_version", sa.Integer(), nullable=False),
        sa.Column("ranking_is_adaptive", sa.Boolean(), nullable=False),
        sa.Column("fixed_formula_rejected", sa.Boolean(), nullable=False),
        sa.Column("opportunity_count", sa.Integer(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_opportunity_scans_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_opportunity_scans_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["website_id"], ["websites.id"], name=op.f("fk_opportunity_scans_website_id_websites"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_opportunity_scans_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_opportunity_scans")),
    )
    for col in ("website_id", "client_brand", "scan_status", "organisation_id", "workspace_id", "created_by", "status"):
        op.create_index(op.f(f"ix_opportunity_scans_{col}"), "opportunity_scans", [col], unique=False)

    op.create_table(
        "peacock_opportunities",
        sa.Column("scan_id", sa.String(length=36), nullable=False),
        sa.Column("opportunity_key", sa.String(length=128), nullable=False),
        sa.Column("opportunity_type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("impact", sa.Float(), nullable=False),
        sa.Column("urgency", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("difficulty", sa.Float(), nullable=False),
        sa.Column("expected_value", sa.Float(), nullable=False),
        sa.Column("recommended_action", sa.Text(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("opportunity_score", sa.Float(), nullable=False),
        sa.Column("ranking_explanation", sa.Text(), nullable=False),
        sa.Column("related_entity", sa.String(length=512), nullable=True),
        sa.Column("related_url", sa.String(length=2048), nullable=True),
        sa.Column("status_label", sa.String(length=32), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_peacock_opportunities_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_peacock_opportunities_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["scan_id"], ["opportunity_scans.id"], name=op.f("fk_peacock_opportunities_scan_id_opportunity_scans"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_peacock_opportunities_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_peacock_opportunities")),
        sa.UniqueConstraint("scan_id", "opportunity_key", name=op.f("uq_peacock_opportunities_scan_id")),
    )
    for col in ("scan_id", "opportunity_key", "opportunity_type", "status_label", "organisation_id", "workspace_id", "created_by", "status"):
        op.create_index(op.f(f"ix_peacock_opportunities_{col}"), "peacock_opportunities", [col], unique=False)

    op.create_table(
        "po_evidence",
        sa.Column("opportunity_id", sa.String(length=36), nullable=False),
        sa.Column("evidence_type", sa.String(length=64), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("source_ref", sa.String(length=512), nullable=True),
        sa.Column("strength", sa.Float(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_po_evidence_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["opportunity_id"], ["peacock_opportunities.id"], name=op.f("fk_po_evidence_opportunity_id_peacock_opportunities"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_po_evidence_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_po_evidence_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_po_evidence")),
    )
    for col in ("opportunity_id", "evidence_type", "organisation_id", "workspace_id", "created_by", "status"):
        op.create_index(op.f(f"ix_po_evidence_{col}"), "po_evidence", [col], unique=False)

    op.create_table(
        "po_ranking_factors",
        sa.Column("opportunity_id", sa.String(length=36), nullable=False),
        sa.Column("feature_code", sa.String(length=64), nullable=False),
        sa.Column("feature_value", sa.Float(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("contribution", sa.Float(), nullable=False),
        sa.Column("weight_source", sa.String(length=32), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_po_ranking_factors_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["opportunity_id"], ["peacock_opportunities.id"], name=op.f("fk_po_ranking_factors_opportunity_id_peacock_opportunities"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_po_ranking_factors_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_po_ranking_factors_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_po_ranking_factors")),
        sa.UniqueConstraint("opportunity_id", "feature_code", name=op.f("uq_po_ranking_factors_opportunity_id")),
    )
    for col in ("opportunity_id", "feature_code", "organisation_id", "workspace_id", "created_by", "status"):
        op.create_index(op.f(f"ix_po_ranking_factors_{col}"), "po_ranking_factors", [col], unique=False)

    op.create_table(
        "po_ranking_weights",
        sa.Column("scan_id", sa.String(length=36), nullable=False),
        sa.Column("feature_code", sa.String(length=64), nullable=False),
        sa.Column("base_weight", sa.Float(), nullable=False),
        sa.Column("learned_weight", sa.Float(), nullable=False),
        sa.Column("effective_weight", sa.Float(), nullable=False),
        sa.Column("learning_sample_size", sa.Integer(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_po_ranking_weights_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_po_ranking_weights_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["scan_id"], ["opportunity_scans.id"], name=op.f("fk_po_ranking_weights_scan_id_opportunity_scans"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_po_ranking_weights_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_po_ranking_weights")),
        sa.UniqueConstraint("scan_id", "feature_code", name=op.f("uq_po_ranking_weights_scan_id")),
    )
    for col in ("scan_id", "feature_code", "organisation_id", "workspace_id", "created_by", "status"):
        op.create_index(op.f(f"ix_po_ranking_weights_{col}"), "po_ranking_weights", [col], unique=False)

    op.create_table(
        "po_outcome_feedback",
        sa.Column("website_id", sa.String(length=36), nullable=False),
        sa.Column("opportunity_type", sa.String(length=64), nullable=False),
        sa.Column("opportunity_key", sa.String(length=128), nullable=True),
        sa.Column("impact", sa.Float(), nullable=False),
        sa.Column("urgency", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("difficulty", sa.Float(), nullable=False),
        sa.Column("expected_value", sa.Float(), nullable=False),
        sa.Column("predicted_score", sa.Float(), nullable=False),
        sa.Column("realized_outcome", sa.Float(), nullable=False),
        sa.Column("outcome_label", sa.String(length=64), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_po_outcome_feedback_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_po_outcome_feedback_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["website_id"], ["websites.id"], name=op.f("fk_po_outcome_feedback_website_id_websites"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_po_outcome_feedback_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_po_outcome_feedback")),
    )
    for col in ("website_id", "opportunity_type", "opportunity_key", "organisation_id", "workspace_id", "created_by", "status"):
        op.create_index(op.f(f"ix_po_outcome_feedback_{col}"), "po_outcome_feedback", [col], unique=False)


def downgrade() -> None:
    op.drop_table("po_outcome_feedback")
    op.drop_table("po_ranking_weights")
    op.drop_table("po_ranking_factors")
    op.drop_table("po_evidence")
    op.drop_table("peacock_opportunities")
    op.drop_table("opportunity_scans")
