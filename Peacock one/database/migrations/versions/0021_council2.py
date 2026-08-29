"""Peacock Council 2.0 — opposing-role debate protocol

Revision ID: 0021_council2
Revises: 0020_opportunity_engine
Create Date: 2026-08-12
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0021_council2"
down_revision: Union[str, None] = "0020_opportunity_engine"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ix(table: str, cols: list[str]) -> None:
    for col in cols:
        op.create_index(op.f(f"ix_{table}_{col}"), table, [col], unique=False)


def upgrade() -> None:
    op.create_table(
        "council2_sessions",
        sa.Column("website_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("client_brand", sa.String(length=255), nullable=False),
        sa.Column("decision_question", sa.Text(), nullable=False),
        sa.Column("context_summary", sa.Text(), nullable=True),
        sa.Column("session_status", sa.String(length=32), nullable=False),
        sa.Column("methodology", sa.String(length=64), nullable=False),
        sa.Column("open_opinion_prompts_rejected", sa.Boolean(), nullable=False),
        sa.Column("chain_of_thought_not_stored", sa.Boolean(), nullable=False),
        sa.Column("stored_artifact_kinds", sa.Text(), nullable=False),
        sa.Column("round_count", sa.Integer(), nullable=False),
        sa.Column("final_decision_text", sa.Text(), nullable=True),
        sa.Column("final_confidence", sa.Float(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_council2_sessions_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_council2_sessions_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["website_id"], ["websites.id"], name=op.f("fk_council2_sessions_website_id_websites"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_council2_sessions_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_council2_sessions")),
    )
    _ix("council2_sessions", ["website_id", "client_brand", "session_status", "organisation_id", "workspace_id", "created_by", "status"])

    op.create_table(
        "c2_agents",
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("role_code", sa.String(length=64), nullable=False),
        sa.Column("role_mandate", sa.Text(), nullable=False),
        sa.Column("model_label", sa.String(length=128), nullable=False),
        sa.Column("open_opinion_prompt_rejected", sa.Boolean(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_c2_agents_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_c2_agents_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["council2_sessions.id"], name=op.f("fk_c2_agents_session_id_council2_sessions"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_c2_agents_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_c2_agents")),
        sa.UniqueConstraint("session_id", "role_code", name=op.f("uq_c2_agents_session_id")),
    )
    _ix("c2_agents", ["session_id", "role_code", "organisation_id", "workspace_id", "created_by", "status"])

    op.create_table(
        "c2_round_records",
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("round_number", sa.Integer(), nullable=False),
        sa.Column("round_code", sa.String(length=64), nullable=False),
        sa.Column("round_label", sa.String(length=255), nullable=False),
        sa.Column("structured_summary", sa.Text(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_c2_round_records_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_c2_round_records_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["council2_sessions.id"], name=op.f("fk_c2_round_records_session_id_council2_sessions"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_c2_round_records_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_c2_round_records")),
        sa.UniqueConstraint("session_id", "round_number", name=op.f("uq_c2_round_records_session_id")),
    )
    _ix("c2_round_records", ["session_id", "round_code", "organisation_id", "workspace_id", "created_by", "status"])

    op.create_table(
        "c2_claims",
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("claim_key", sa.String(length=128), nullable=False),
        sa.Column("role_code", sa.String(length=64), nullable=False),
        sa.Column("round_number", sa.Integer(), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("stance", sa.String(length=32), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_c2_claims_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_c2_claims_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["council2_sessions.id"], name=op.f("fk_c2_claims_session_id_council2_sessions"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_c2_claims_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_c2_claims")),
    )
    _ix("c2_claims", ["session_id", "claim_key", "role_code", "round_number", "organisation_id", "workspace_id", "created_by", "status"])

    op.create_table(
        "c2_evidence",
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("claim_key", sa.String(length=128), nullable=False),
        sa.Column("role_code", sa.String(length=64), nullable=False),
        sa.Column("round_number", sa.Integer(), nullable=False),
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
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_c2_evidence_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_c2_evidence_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["council2_sessions.id"], name=op.f("fk_c2_evidence_session_id_council2_sessions"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_c2_evidence_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_c2_evidence")),
    )
    _ix("c2_evidence", ["session_id", "claim_key", "role_code", "round_number", "organisation_id", "workspace_id", "created_by", "status"])

    op.create_table(
        "c2_counterarguments",
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("claim_key", sa.String(length=128), nullable=False),
        sa.Column("role_code", sa.String(length=64), nullable=False),
        sa.Column("round_number", sa.Integer(), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_c2_counterarguments_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_c2_counterarguments_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["council2_sessions.id"], name=op.f("fk_c2_counterarguments_session_id_council2_sessions"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_c2_counterarguments_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_c2_counterarguments")),
    )
    _ix("c2_counterarguments", ["session_id", "claim_key", "role_code", "round_number", "organisation_id", "workspace_id", "created_by", "status"])

    op.create_table(
        "c2_disagreements",
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("claim_key", sa.String(length=128), nullable=False),
        sa.Column("role_a", sa.String(length=64), nullable=False),
        sa.Column("role_b", sa.String(length=64), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("severity", sa.Float(), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_c2_disagreements_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_c2_disagreements_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["council2_sessions.id"], name=op.f("fk_c2_disagreements_session_id_council2_sessions"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_c2_disagreements_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_c2_disagreements")),
    )
    _ix("c2_disagreements", ["session_id", "claim_key", "organisation_id", "workspace_id", "created_by", "status"])

    op.create_table(
        "c2_evidence_requests",
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("claim_key", sa.String(length=128), nullable=False),
        sa.Column("requested_by_role", sa.String(length=64), nullable=False),
        sa.Column("request_statement", sa.Text(), nullable=False),
        sa.Column("fulfilled", sa.Boolean(), nullable=False),
        sa.Column("fulfillment_evidence", sa.Text(), nullable=True),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_c2_evidence_requests_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_c2_evidence_requests_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["council2_sessions.id"], name=op.f("fk_c2_evidence_requests_session_id_council2_sessions"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_c2_evidence_requests_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_c2_evidence_requests")),
    )
    _ix("c2_evidence_requests", ["session_id", "claim_key", "organisation_id", "workspace_id", "created_by", "status"])

    op.create_table(
        "c2_decisions",
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("decision", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("supporting_claim_keys", sa.Text(), nullable=False),
        sa.Column("rejected_claim_keys", sa.Text(), nullable=False),
        sa.Column("judge_role", sa.String(length=64), nullable=False),
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], name=op.f("fk_c2_decisions_created_by_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"], name=op.f("fk_c2_decisions_organisation_id_organisations"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["council2_sessions.id"], name=op.f("fk_c2_decisions_session_id_council2_sessions"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], name=op.f("fk_c2_decisions_workspace_id_workspaces"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_c2_decisions")),
    )
    _ix("c2_decisions", ["session_id", "organisation_id", "workspace_id", "created_by", "status"])


def downgrade() -> None:
    for table in (
        "c2_decisions",
        "c2_evidence_requests",
        "c2_disagreements",
        "c2_counterarguments",
        "c2_evidence",
        "c2_claims",
        "c2_round_records",
        "c2_agents",
        "council2_sessions",
    ):
        op.drop_table(table)
