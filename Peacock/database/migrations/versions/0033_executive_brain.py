"""Peacock Executive Brain — CEO/CMO executive briefing view

Revision ID: 0033_executive_brain
Revises: 0032_command_centre
Create Date: 2026-08-13
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0033_executive_brain"
down_revision: Union[str, None] = "0032_command_centre"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ix(table: str, cols: list[str]) -> None:
    for col in cols:
        op.create_index(op.f(f"ix_{table}_{col}"), table, [col], unique=False)


def upgrade() -> None:
    op.create_table(
        "executive_brain_briefs",
        sa.Column("website_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("client_brand", sa.String(length=255), nullable=False),
        sa.Column("brief_status", sa.String(length=32), nullable=False),
        sa.Column("methodology", sa.String(length=64), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("horizon_days", sa.Integer(), nullable=False),
        sa.Column("budget_label", sa.String(length=64), nullable=True),
        sa.Column("overall_confidence", sa.Float(), nullable=False),
        sa.Column("headline", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_executive_brain_briefs_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_executive_brain_briefs_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["website_id"], ["websites.id"], name=op.f("fk_executive_brain_briefs_website_id_websites"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_executive_brain_briefs_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_executive_brain_briefs")),
    )
    _ix(
        "executive_brain_briefs",
        [
            "website_id",
            "client_brand",
            "brief_status",
            "generated_at",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "eb_answers",
        sa.Column("brief_id", sa.String(length=36), nullable=False),
        sa.Column("question_key", sa.String(length=64), nullable=False),
        sa.Column("question_label", sa.String(length=255), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("evidence_note", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("rank_order", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["brief_id"], ["executive_brain_briefs.id"], name=op.f("fk_eb_answers_brief_id_executive_brain_briefs"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_eb_answers_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_eb_answers_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_eb_answers_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_eb_answers")),
        sa.UniqueConstraint("brief_id", "question_key", name=op.f("uq_eb_answers_brief_id")),
    )
    _ix(
        "eb_answers",
        [
            "brief_id",
            "question_key",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "eb_role_summaries",
        sa.Column("brief_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("call_to_action", sa.Text(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["brief_id"], ["executive_brain_briefs.id"], name=op.f("fk_eb_role_summaries_brief_id_executive_brain_briefs"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_eb_role_summaries_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_eb_role_summaries_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_eb_role_summaries_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_eb_role_summaries")),
        sa.UniqueConstraint("brief_id", "role", name=op.f("uq_eb_role_summaries_brief_id")),
    )
    _ix(
        "eb_role_summaries",
        [
            "brief_id",
            "role",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )


def downgrade() -> None:
    op.drop_table("eb_role_summaries")
    op.drop_table("eb_answers")
    op.drop_table("executive_brain_briefs")
