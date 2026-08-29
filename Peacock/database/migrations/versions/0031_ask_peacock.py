"""Ask Peacock 2.0 — structured NL interface over the intelligence graph

Revision ID: 0031_ask_peacock
Revises: 0030_anomaly_engine
Create Date: 2026-08-13
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0031_ask_peacock"
down_revision: Union[str, None] = "0030_anomaly_engine"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ix(table: str, cols: list[str]) -> None:
    for col in cols:
        op.create_index(op.f(f"ix_{table}_{col}"), table, [col], unique=False)


def upgrade() -> None:
    op.create_table(
        "ask_peacock_sessions",
        sa.Column("website_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("client_brand", sa.String(length=255), nullable=False),
        sa.Column("session_status", sa.String(length=32), nullable=False),
        sa.Column("methodology", sa.String(length=64), nullable=False),
        sa.Column("questions_asked", sa.Integer(), nullable=False),
        sa.Column("answers_produced", sa.Integer(), nullable=False),
        sa.Column("evidence_items", sa.Integer(), nullable=False),
        sa.Column("mean_confidence", sa.Float(), nullable=True),
        sa.Column("primary_intent", sa.String(length=64), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_ask_peacock_sessions_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_ask_peacock_sessions_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["website_id"], ["websites.id"], name=op.f("fk_ask_peacock_sessions_website_id_websites"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_ask_peacock_sessions_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ask_peacock_sessions")),
    )
    _ix(
        "ask_peacock_sessions",
        [
            "website_id",
            "client_brand",
            "session_status",
            "primary_intent",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "ap_answers",
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("question_index", sa.Integer(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("intent", sa.String(length=64), nullable=False),
        sa.Column("intent_label", sa.String(length=255), nullable=False),
        sa.Column("observed", sa.Text(), nullable=False),
        sa.Column("inferred", sa.Text(), nullable=False),
        sa.Column("recommended", sa.Text(), nullable=False),
        sa.Column("forecast", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("confidence_rationale", sa.Text(), nullable=False),
        sa.Column("graph_surfaces_used", sa.Text(), nullable=False),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_ap_answers_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_ap_answers_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["ask_peacock_sessions.id"], name=op.f("fk_ap_answers_session_id_ask_peacock_sessions"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_ap_answers_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ap_answers")),
        sa.UniqueConstraint("session_id", "question_index", name=op.f("uq_ap_answers_session_id")),
    )
    _ix(
        "ap_answers",
        [
            "session_id",
            "intent",
            "confidence",
            "answered_at",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "ap_evidence",
        sa.Column("answer_id", sa.String(length=36), nullable=False),
        sa.Column("evidence_index", sa.Integer(), nullable=False),
        sa.Column("graph_surface", sa.String(length=64), nullable=False),
        sa.Column("claim", sa.Text(), nullable=False),
        sa.Column("ref_id", sa.String(length=128), nullable=True),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("section", sa.String(length=32), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["answer_id"], ["ap_answers.id"], name=op.f("fk_ap_evidence_answer_id_ap_answers"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_ap_evidence_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_ap_evidence_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_ap_evidence_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ap_evidence")),
        sa.UniqueConstraint("answer_id", "evidence_index", name=op.f("uq_ap_evidence_answer_idx")),
    )
    _ix(
        "ap_evidence",
        [
            "answer_id",
            "graph_surface",
            "section",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )


def downgrade() -> None:
    op.drop_table("ap_evidence")
    op.drop_table("ap_answers")
    op.drop_table("ask_peacock_sessions")
