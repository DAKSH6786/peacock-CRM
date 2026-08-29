"""Content Digital Twin — pre-publish article simulation

Revision ID: 0017_content_digital_twin
Revises: 0016_content_lab
Create Date: 2026-08-12
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0017_content_digital_twin"
down_revision: Union[str, None] = "0016_content_lab"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "content_digital_twins",
        sa.Column("website_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("client_brand", sa.String(length=255), nullable=False),
        sa.Column("topic_cluster", sa.String(length=255), nullable=True),
        sa.Column("twin_status", sa.String(length=32), nullable=False),
        sa.Column("article_plan_json", sa.Text(), nullable=False),
        sa.Column("simulation_context_json", sa.Text(), nullable=False),
        sa.Column("plan_revision", sa.Integer(), nullable=False),
        sa.Column("evaluation_count", sa.Integer(), nullable=False),
        sa.Column("latest_evaluation_id", sa.String(length=36), nullable=True),
        sa.Column("content_lab_proposal_id", sa.String(length=36), nullable=True),
        sa.Column("methodology", sa.String(length=64), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
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
            name=op.f("fk_content_digital_twins_created_by_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["organisation_id"],
            ["organisations.id"],
            name=op.f("fk_content_digital_twins_organisation_id_organisations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["website_id"],
            ["websites.id"],
            name=op.f("fk_content_digital_twins_website_id_websites"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name=op.f("fk_content_digital_twins_workspace_id_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_content_digital_twins")),
    )
    op.create_index(
        op.f("ix_content_digital_twins_website_id"),
        "content_digital_twins",
        ["website_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_content_digital_twins_client_brand"),
        "content_digital_twins",
        ["client_brand"],
        unique=False,
    )
    op.create_index(
        op.f("ix_content_digital_twins_topic_cluster"),
        "content_digital_twins",
        ["topic_cluster"],
        unique=False,
    )
    op.create_index(
        op.f("ix_content_digital_twins_twin_status"),
        "content_digital_twins",
        ["twin_status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_content_digital_twins_latest_evaluation_id"),
        "content_digital_twins",
        ["latest_evaluation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_content_digital_twins_content_lab_proposal_id"),
        "content_digital_twins",
        ["content_lab_proposal_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_content_digital_twins_organisation_id"),
        "content_digital_twins",
        ["organisation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_content_digital_twins_workspace_id"),
        "content_digital_twins",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_content_digital_twins_created_by"),
        "content_digital_twins",
        ["created_by"],
        unique=False,
    )
    op.create_index(
        op.f("ix_content_digital_twins_status"),
        "content_digital_twins",
        ["status"],
        unique=False,
    )

    op.create_table(
        "cdt_evaluations",
        sa.Column("twin_id", sa.String(length=36), nullable=False),
        sa.Column("evaluation_number", sa.Integer(), nullable=False),
        sa.Column("plan_revision", sa.Integer(), nullable=False),
        sa.Column("article_plan_snapshot_json", sa.Text(), nullable=False),
        sa.Column("simulation_context_snapshot_json", sa.Text(), nullable=False),
        sa.Column("predicted_strength_score", sa.Float(), nullable=False),
        sa.Column("readiness_score", sa.Float(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("evaluation_status", sa.String(length=32), nullable=False),
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
            name=op.f("fk_cdt_evaluations_created_by_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["organisation_id"],
            ["organisations.id"],
            name=op.f("fk_cdt_evaluations_organisation_id_organisations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["twin_id"],
            ["content_digital_twins.id"],
            name=op.f("fk_cdt_evaluations_twin_id_content_digital_twins"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name=op.f("fk_cdt_evaluations_workspace_id_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cdt_evaluations")),
        sa.UniqueConstraint(
            "twin_id",
            "evaluation_number",
            name=op.f("uq_cdt_evaluations_twin_id"),
        ),
    )
    op.create_index(
        op.f("ix_cdt_evaluations_twin_id"), "cdt_evaluations", ["twin_id"], unique=False
    )
    op.create_index(
        op.f("ix_cdt_evaluations_evaluation_status"),
        "cdt_evaluations",
        ["evaluation_status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cdt_evaluations_organisation_id"),
        "cdt_evaluations",
        ["organisation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cdt_evaluations_workspace_id"),
        "cdt_evaluations",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cdt_evaluations_created_by"),
        "cdt_evaluations",
        ["created_by"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cdt_evaluations_status"), "cdt_evaluations", ["status"], unique=False
    )

    op.create_table(
        "cdt_requirement_scores",
        sa.Column("evaluation_id", sa.String(length=36), nullable=False),
        sa.Column("surface", sa.String(length=64), nullable=False),
        sa.Column("coverage_score", sa.Float(), nullable=False),
        sa.Column("matched_count", sa.Integer(), nullable=False),
        sa.Column("missing_count", sa.Integer(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
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
            name=op.f("fk_cdt_requirement_scores_created_by_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["evaluation_id"],
            ["cdt_evaluations.id"],
            name=op.f("fk_cdt_requirement_scores_evaluation_id_cdt_evaluations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["organisation_id"],
            ["organisations.id"],
            name=op.f("fk_cdt_requirement_scores_organisation_id_organisations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name=op.f("fk_cdt_requirement_scores_workspace_id_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cdt_requirement_scores")),
        sa.UniqueConstraint(
            "evaluation_id",
            "surface",
            name=op.f("uq_cdt_requirement_scores_evaluation_id"),
        ),
    )
    op.create_index(
        op.f("ix_cdt_requirement_scores_evaluation_id"),
        "cdt_requirement_scores",
        ["evaluation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cdt_requirement_scores_surface"),
        "cdt_requirement_scores",
        ["surface"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cdt_requirement_scores_organisation_id"),
        "cdt_requirement_scores",
        ["organisation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cdt_requirement_scores_workspace_id"),
        "cdt_requirement_scores",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cdt_requirement_scores_created_by"),
        "cdt_requirement_scores",
        ["created_by"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cdt_requirement_scores_status"),
        "cdt_requirement_scores",
        ["status"],
        unique=False,
    )

    op.create_table(
        "cdt_findings",
        sa.Column("evaluation_id", sa.String(length=36), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("related_surface", sa.String(length=64), nullable=True),
        sa.Column("related_item", sa.String(length=512), nullable=True),
        sa.Column("priority", sa.Float(), nullable=False),
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
            name=op.f("fk_cdt_findings_created_by_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["evaluation_id"],
            ["cdt_evaluations.id"],
            name=op.f("fk_cdt_findings_evaluation_id_cdt_evaluations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["organisation_id"],
            ["organisations.id"],
            name=op.f("fk_cdt_findings_organisation_id_organisations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name=op.f("fk_cdt_findings_workspace_id_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cdt_findings")),
    )
    op.create_index(
        op.f("ix_cdt_findings_evaluation_id"),
        "cdt_findings",
        ["evaluation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cdt_findings_category"), "cdt_findings", ["category"], unique=False
    )
    op.create_index(
        op.f("ix_cdt_findings_severity"), "cdt_findings", ["severity"], unique=False
    )
    op.create_index(
        op.f("ix_cdt_findings_related_surface"),
        "cdt_findings",
        ["related_surface"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cdt_findings_organisation_id"),
        "cdt_findings",
        ["organisation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cdt_findings_workspace_id"),
        "cdt_findings",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cdt_findings_created_by"), "cdt_findings", ["created_by"], unique=False
    )
    op.create_index(
        op.f("ix_cdt_findings_status"), "cdt_findings", ["status"], unique=False
    )


def downgrade() -> None:
    op.drop_table("cdt_findings")
    op.drop_table("cdt_requirement_scores")
    op.drop_table("cdt_evaluations")
    op.drop_table("content_digital_twins")
