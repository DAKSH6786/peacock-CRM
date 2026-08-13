"""Peacock Research Mode — controlled search intelligence laboratory studies

Revision ID: 0035_research_mode
Revises: 0034_proprietary_metrics
Create Date: 2026-08-13
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0035_research_mode"
down_revision: Union[str, None] = "0034_proprietary_metrics"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ix(table: str, cols: list[str]) -> None:
    for col in cols:
        op.create_index(op.f(f"ix_{table}_{col}"), table, [col], unique=False)


def upgrade() -> None:
    op.create_table(
        "research_studies",
        sa.Column("website_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("client_brand", sa.String(length=255), nullable=False),
        sa.Column("research_question", sa.Text(), nullable=False),
        sa.Column("hypothesis", sa.Text(), nullable=False),
        sa.Column("metric_key", sa.String(length=64), nullable=False),
        sa.Column("metric_label", sa.String(length=128), nullable=False),
        sa.Column("treatment_description", sa.Text(), nullable=False),
        sa.Column("study_status", sa.String(length=32), nullable=False),
        sa.Column("methodology", sa.String(length=64), nullable=False),
        sa.Column("laboratory_positioning", sa.Text(), nullable=False),
        sa.Column("causality_warning", sa.Text(), nullable=False),
        sa.Column("completed_phases", sa.Text(), nullable=False),
        sa.Column("baseline_mean", sa.Float(), nullable=True),
        sa.Column("treatment_mean", sa.Float(), nullable=True),
        sa.Column("absolute_delta", sa.Float(), nullable=True),
        sa.Column("relative_delta_pct", sa.Float(), nullable=True),
        sa.Column("control_adjusted_delta", sa.Float(), nullable=True),
        sa.Column("uncertainty_band", sa.String(length=32), nullable=False),
        sa.Column("uncertainty_score", sa.Float(), nullable=False),
        sa.Column("finding_verdict", sa.String(length=64), nullable=False),
        sa.Column("finding_summary", sa.Text(), nullable=False),
        sa.Column("observation_rounds", sa.Integer(), nullable=False),
        sa.Column("pages_count", sa.Integer(), nullable=False),
        sa.Column("prompts_count", sa.Integer(), nullable=False),
        sa.Column("analysed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_research_studies_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_research_studies_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["website_id"], ["websites.id"], name=op.f("fk_research_studies_website_id_websites"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_research_studies_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_research_studies")),
    )
    _ix(
        "research_studies",
        [
            "website_id",
            "client_brand",
            "metric_key",
            "study_status",
            "uncertainty_band",
            "finding_verdict",
            "analysed_at",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "rm_pages",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("page_role", sa.String(length=32), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=True),
        sa.Column("rank_order", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_rm_pages_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_rm_pages_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["study_id"], ["research_studies.id"], name=op.f("fk_rm_pages_study_id_research_studies"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_rm_pages_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_rm_pages")),
        sa.UniqueConstraint("study_id", "url", name=op.f("uq_rm_pages_study_id")),
    )
    _ix(
        "rm_pages",
        ["study_id", "page_role", "organisation_id", "workspace_id", "created_by", "status"],
    )

    op.create_table(
        "rm_prompts",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("prompt_text", sa.Text(), nullable=False),
        sa.Column("prompt_cluster", sa.String(length=128), nullable=True),
        sa.Column("rank_order", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_rm_prompts_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_rm_prompts_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["study_id"], ["research_studies.id"], name=op.f("fk_rm_prompts_study_id_research_studies"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_rm_prompts_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_rm_prompts")),
        sa.UniqueConstraint("study_id", "prompt_text", name=op.f("uq_rm_prompts_study_id")),
    )
    _ix(
        "rm_prompts",
        ["study_id", "prompt_cluster", "organisation_id", "workspace_id", "created_by", "status"],
    )

    op.create_table(
        "rm_observations",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("arm", sa.String(length=32), nullable=False),
        sa.Column("round_index", sa.Integer(), nullable=False),
        sa.Column("page_url", sa.String(length=2048), nullable=False),
        sa.Column("page_role", sa.String(length=32), nullable=False),
        sa.Column("prompt_text", sa.Text(), nullable=False),
        sa.Column("metric_key", sa.String(length=64), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_rm_observations_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_rm_observations_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["study_id"], ["research_studies.id"], name=op.f("fk_rm_observations_study_id_research_studies"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_rm_observations_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_rm_observations")),
        sa.UniqueConstraint(
            "study_id",
            "arm",
            "round_index",
            "page_url",
            "prompt_text",
            name="uq_rm_observations_point",
        ),
    )
    _ix(
        "rm_observations",
        [
            "study_id",
            "arm",
            "round_index",
            "page_role",
            "metric_key",
            "observed_at",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "rm_findings",
        sa.Column("study_id", sa.String(length=36), nullable=False),
        sa.Column("finding_index", sa.Integer(), nullable=False),
        sa.Column("verdict", sa.String(length=64), nullable=False),
        sa.Column("claim", sa.Text(), nullable=False),
        sa.Column("evidence", sa.Text(), nullable=False),
        sa.Column("uncertainty_band", sa.String(length=32), nullable=False),
        sa.Column("uncertainty_rationale", sa.Text(), nullable=False),
        sa.Column("auto_causal_conclusion_rejected", sa.Boolean(), nullable=False),
        sa.Column("next_step", sa.Text(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_rm_findings_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_rm_findings_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["study_id"], ["research_studies.id"], name=op.f("fk_rm_findings_study_id_research_studies"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_rm_findings_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_rm_findings")),
        sa.UniqueConstraint("study_id", "finding_index", name=op.f("uq_rm_findings_study_id")),
    )
    _ix(
        "rm_findings",
        ["study_id", "verdict", "organisation_id", "workspace_id", "created_by", "status"],
    )


def downgrade() -> None:
    op.drop_table("rm_findings")
    op.drop_table("rm_observations")
    op.drop_table("rm_prompts")
    op.drop_table("rm_pages")
    op.drop_table("research_studies")
