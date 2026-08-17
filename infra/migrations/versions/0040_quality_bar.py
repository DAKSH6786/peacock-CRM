"""Peacock One Quality Bar — module completeness shipping checklist

Revision ID: 0040_quality_bar
Revises: 0039_ai_connector_security
Create Date: 2026-08-13
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0040_quality_bar"
down_revision: Union[str, None] = "0039_ai_connector_security"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ix(table: str, cols: list[str]) -> None:
    for col in cols:
        op.create_index(op.f(f"ix_{table}_{col}"), table, [col], unique=False)


def _tenant_cols() -> list:
    return [
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("organisation_id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def _tenant_fks(table: str) -> list:
    return [
        sa.ForeignKeyConstraint(
            ["created_by"], ["users.id"], name=op.f(f"fk_{table}_created_by_users"), ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["organisation_id"],
            ["organisations.id"],
            name=op.f(f"fk_{table}_organisation_id_organisations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name=op.f(f"fk_{table}_workspace_id_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f(f"pk_{table}")),
    ]


def upgrade() -> None:
    op.create_table(
        "quality_bar_assessments",
        sa.Column("website_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("client_brand", sa.String(length=255), nullable=False),
        sa.Column("module_key", sa.String(length=128), nullable=False),
        sa.Column("module_label", sa.String(length=255), nullable=False),
        sa.Column("completeness_verdict", sa.String(length=32), nullable=False),
        sa.Column("gates_total", sa.Integer(), nullable=False),
        sa.Column("gates_passed", sa.Integer(), nullable=False),
        sa.Column("gates_failed", sa.Integer(), nullable=False),
        sa.Column("completeness_score", sa.Float(), nullable=False),
        sa.Column("blocked_by", sa.Text(), nullable=True),
        sa.Column("improvement_summary", sa.Text(), nullable=False),
        sa.Column("methodology", sa.String(length=64), nullable=False),
        sa.Column("quality_positioning", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("analysed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        *_tenant_cols(),
        sa.ForeignKeyConstraint(
            ["website_id"],
            ["websites.id"],
            name=op.f("fk_quality_bar_assessments_website_id_websites"),
            ondelete="CASCADE",
        ),
        *_tenant_fks("quality_bar_assessments"),
    )
    _ix(
        "quality_bar_assessments",
        [
            "website_id",
            "client_brand",
            "module_key",
            "completeness_verdict",
            "analysed_at",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "qb_gate_results",
        sa.Column("assessment_id", sa.String(length=36), nullable=False),
        sa.Column("gate_key", sa.String(length=64), nullable=False),
        sa.Column("gate_label", sa.String(length=255), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("improvement_if_fail", sa.Text(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("answer_yes_problem", sa.Boolean(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("evidence_note", sa.Text(), nullable=True),
        sa.Column("rank_order", sa.Integer(), nullable=False),
        *_tenant_cols(),
        sa.ForeignKeyConstraint(
            ["assessment_id"],
            ["quality_bar_assessments.id"],
            name=op.f("fk_qb_gate_results_assessment_id_quality_bar_assessments"),
            ondelete="CASCADE",
        ),
        *_tenant_fks("qb_gate_results"),
        sa.UniqueConstraint(
            "assessment_id", "gate_key", name=op.f("uq_qb_gate_results_assessment_id")
        ),
    )
    _ix(
        "qb_gate_results",
        [
            "assessment_id",
            "gate_key",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "qb_remediation_actions",
        sa.Column("assessment_id", sa.String(length=36), nullable=False),
        sa.Column("gate_key", sa.String(length=64), nullable=False),
        sa.Column("action_key", sa.String(length=64), nullable=False),
        sa.Column("action_label", sa.String(length=255), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("links_to_learning", sa.Boolean(), nullable=False),
        sa.Column("rank_order", sa.Integer(), nullable=False),
        *_tenant_cols(),
        sa.ForeignKeyConstraint(
            ["assessment_id"],
            ["quality_bar_assessments.id"],
            name=op.f("fk_qb_remediation_actions_assessment_id_quality_bar_assessments"),
            ondelete="CASCADE",
        ),
        *_tenant_fks("qb_remediation_actions"),
        sa.UniqueConstraint(
            "assessment_id",
            "gate_key",
            "action_key",
            name=op.f("uq_qb_remediation_actions_assessment_id"),
        ),
    )
    _ix(
        "qb_remediation_actions",
        [
            "assessment_id",
            "gate_key",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )


def downgrade() -> None:
    op.drop_table("qb_remediation_actions")
    op.drop_table("qb_gate_results")
    op.drop_table("quality_bar_assessments")
