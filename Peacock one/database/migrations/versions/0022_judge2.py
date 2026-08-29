"""Peacock Judge 2.0 — deterministic multi-signal judgment

Revision ID: 0022_judge2
Revises: 0021_council2
Create Date: 2026-08-12
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0022_judge2"
down_revision: Union[str, None] = "0021_council2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ix(table: str, cols: list[str]) -> None:
    for col in cols:
        op.create_index(op.f(f"ix_{table}_{col}"), table, [col], unique=False)


def upgrade() -> None:
    op.create_table(
        "judge2_judgments",
        sa.Column("website_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("client_brand", sa.String(length=255), nullable=False),
        sa.Column("decision_question", sa.Text(), nullable=False),
        sa.Column("judgment_status", sa.String(length=32), nullable=False),
        sa.Column("methodology", sa.String(length=64), nullable=False),
        sa.Column("scoring_outside_llm", sa.Boolean(), nullable=False),
        sa.Column("scoring_note", sa.Text(), nullable=False),
        sa.Column("recommended_action", sa.Text(), nullable=False),
        sa.Column("why", sa.Text(), nullable=False),
        sa.Column("expected_upside", sa.Text(), nullable=False),
        sa.Column("expected_upside_score", sa.Float(), nullable=False),
        sa.Column("risk_summary", sa.Text(), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("alternative", sa.Text(), nullable=False),
        sa.Column("what_would_change_decision", sa.Text(), nullable=False),
        sa.Column("composite_score", sa.Float(), nullable=False),
        sa.Column("action_code", sa.String(length=32), nullable=False),
        sa.Column("council2_session_id", sa.String(length=36), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_judge2_judgments_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_judge2_judgments_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["website_id"], ["websites.id"], name=op.f("fk_judge2_judgments_website_id_websites"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_judge2_judgments_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_judge2_judgments")),
    )
    _ix(
        "judge2_judgments",
        [
            "website_id",
            "client_brand",
            "judgment_status",
            "action_code",
            "council2_session_id",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "j2_signal_scores",
        sa.Column("judgment_id", sa.String(length=36), nullable=False),
        sa.Column("signal_code", sa.String(length=64), nullable=False),
        sa.Column("raw_value", sa.Float(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("inverted", sa.Boolean(), nullable=False),
        sa.Column("contribution", sa.Float(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("computed_outside_llm", sa.Boolean(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_j2_signal_scores_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["judgment_id"], ["judge2_judgments.id"], name=op.f("fk_j2_signal_scores_judgment_id_judge2_judgments"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_j2_signal_scores_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_j2_signal_scores_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_j2_signal_scores")),
        sa.UniqueConstraint("judgment_id", "signal_code", name=op.f("uq_j2_signal_scores_judgment_id")),
    )
    _ix(
        "j2_signal_scores",
        ["judgment_id", "signal_code", "organisation_id", "workspace_id", "created_by", "status"],
    )

    op.create_table(
        "j2_evidence",
        sa.Column("judgment_id", sa.String(length=36), nullable=False),
        sa.Column("evidence_type", sa.String(length=64), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("source_ref", sa.String(length=512), nullable=True),
        sa.Column("reliability", sa.Float(), nullable=False),
        sa.Column("signal_code", sa.String(length=64), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_j2_evidence_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["judgment_id"], ["judge2_judgments.id"], name=op.f("fk_j2_evidence_judgment_id_judge2_judgments"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_j2_evidence_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_j2_evidence_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_j2_evidence")),
    )
    _ix(
        "j2_evidence",
        [
            "judgment_id",
            "evidence_type",
            "signal_code",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "j2_reversal_conditions",
        sa.Column("judgment_id", sa.String(length=36), nullable=False),
        sa.Column("condition_key", sa.String(length=128), nullable=False),
        sa.Column("metric_code", sa.String(length=64), nullable=False),
        sa.Column("operator", sa.String(length=16), nullable=False),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=True),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("reevaluate_action", sa.String(length=64), nullable=False),
        sa.Column("priority", sa.Float(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_j2_reversal_conditions_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["judgment_id"], ["judge2_judgments.id"], name=op.f("fk_j2_reversal_conditions_judgment_id_judge2_judgments"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_j2_reversal_conditions_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_j2_reversal_conditions_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_j2_reversal_conditions")),
    )
    _ix(
        "j2_reversal_conditions",
        [
            "judgment_id",
            "condition_key",
            "metric_code",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )


def downgrade() -> None:
    op.drop_table("j2_reversal_conditions")
    op.drop_table("j2_evidence")
    op.drop_table("j2_signal_scores")
    op.drop_table("judge2_judgments")
