"""Peacock Security for AI Connectors — untrusted LLM I/O controls

Revision ID: 0039_ai_connector_security
Revises: 0038_enterprise_reliability
Create Date: 2026-08-13
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0039_ai_connector_security"
down_revision: Union[str, None] = "0038_enterprise_reliability"
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
        "ai_connector_security_scans",
        sa.Column("website_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("client_brand", sa.String(length=255), nullable=False),
        sa.Column("connector_kind", sa.String(length=64), nullable=False),
        sa.Column("risk_level", sa.String(length=32), nullable=False),
        sa.Column("verdict", sa.String(length=32), nullable=False),
        sa.Column("injection_findings_count", sa.Integer(), nullable=False),
        sa.Column("pii_findings_count", sa.Integer(), nullable=False),
        sa.Column("url_blocks_count", sa.Integer(), nullable=False),
        sa.Column("permission_denials_count", sa.Integer(), nullable=False),
        sa.Column("output_validation_passed", sa.Boolean(), nullable=False),
        sa.Column("tenant_boundary_ok", sa.Boolean(), nullable=False),
        sa.Column("crawler_treated_as_data", sa.Boolean(), nullable=False),
        sa.Column("secrets_exposure_blocked", sa.Boolean(), nullable=False),
        sa.Column("system_behaviour_change_blocked", sa.Boolean(), nullable=False),
        sa.Column("controls_active_count", sa.Integer(), nullable=False),
        sa.Column("methodology", sa.String(length=64), nullable=False),
        sa.Column("security_positioning", sa.Text(), nullable=False),
        sa.Column("crawler_as_data_policy", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("analysed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        *_tenant_cols(),
        sa.ForeignKeyConstraint(
            ["website_id"],
            ["websites.id"],
            name=op.f("fk_ai_connector_security_scans_website_id_websites"),
            ondelete="CASCADE",
        ),
        *_tenant_fks("ai_connector_security_scans"),
    )
    _ix(
        "ai_connector_security_scans",
        [
            "website_id",
            "client_brand",
            "connector_kind",
            "risk_level",
            "verdict",
            "analysed_at",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "acs_content_segments",
        sa.Column("scan_id", sa.String(length=36), nullable=False),
        sa.Column("segment_key", sa.String(length=128), nullable=False),
        sa.Column("source_kind", sa.String(length=64), nullable=False),
        sa.Column("trust_tier", sa.String(length=32), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column("isolated", sa.Boolean(), nullable=False),
        sa.Column("treated_as_instructions", sa.Boolean(), nullable=False),
        sa.Column("rank_order", sa.Integer(), nullable=False),
        *_tenant_cols(),
        sa.ForeignKeyConstraint(
            ["scan_id"],
            ["ai_connector_security_scans.id"],
            name=op.f("fk_acs_content_segments_scan_id_ai_connector_security_scans"),
            ondelete="CASCADE",
        ),
        *_tenant_fks("acs_content_segments"),
        sa.UniqueConstraint(
            "scan_id", "segment_key", name=op.f("uq_acs_content_segments_scan_id")
        ),
    )
    _ix(
        "acs_content_segments",
        [
            "scan_id",
            "segment_key",
            "source_kind",
            "trust_tier",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "acs_injection_findings",
        sa.Column("scan_id", sa.String(length=36), nullable=False),
        sa.Column("segment_key", sa.String(length=128), nullable=False),
        sa.Column("pattern_key", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("matched_excerpt", sa.Text(), nullable=False),
        sa.Column("blocked", sa.Boolean(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        *_tenant_cols(),
        sa.ForeignKeyConstraint(
            ["scan_id"],
            ["ai_connector_security_scans.id"],
            name=op.f("fk_acs_injection_findings_scan_id_ai_connector_security_scans"),
            ondelete="CASCADE",
        ),
        *_tenant_fks("acs_injection_findings"),
    )
    _ix(
        "acs_injection_findings",
        [
            "scan_id",
            "segment_key",
            "pattern_key",
            "severity",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "acs_permission_checks",
        sa.Column("scan_id", sa.String(length=36), nullable=False),
        sa.Column("permission_kind", sa.String(length=32), nullable=False),
        sa.Column("scope_or_connector", sa.String(length=128), nullable=False),
        sa.Column("allowed", sa.Boolean(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("rank_order", sa.Integer(), nullable=False),
        *_tenant_cols(),
        sa.ForeignKeyConstraint(
            ["scan_id"],
            ["ai_connector_security_scans.id"],
            name=op.f("fk_acs_permission_checks_scan_id_ai_connector_security_scans"),
            ondelete="CASCADE",
        ),
        *_tenant_fks("acs_permission_checks"),
        sa.UniqueConstraint(
            "scan_id",
            "permission_kind",
            "scope_or_connector",
            name=op.f("uq_acs_permission_checks_scan_id"),
        ),
    )
    _ix(
        "acs_permission_checks",
        [
            "scan_id",
            "permission_kind",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "acs_url_safety_checks",
        sa.Column("scan_id", sa.String(length=36), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("scheme", sa.String(length=16), nullable=False),
        sa.Column("host", sa.String(length=255), nullable=False),
        sa.Column("is_private_or_local", sa.Boolean(), nullable=False),
        sa.Column("decision", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        *_tenant_cols(),
        sa.ForeignKeyConstraint(
            ["scan_id"],
            ["ai_connector_security_scans.id"],
            name=op.f("fk_acs_url_safety_checks_scan_id_ai_connector_security_scans"),
            ondelete="CASCADE",
        ),
        *_tenant_fks("acs_url_safety_checks"),
    )
    _ix(
        "acs_url_safety_checks",
        [
            "scan_id",
            "host",
            "decision",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "acs_pii_findings",
        sa.Column("scan_id", sa.String(length=36), nullable=False),
        sa.Column("segment_key", sa.String(length=128), nullable=False),
        sa.Column("pii_type", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("redacted_excerpt", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        *_tenant_cols(),
        sa.ForeignKeyConstraint(
            ["scan_id"],
            ["ai_connector_security_scans.id"],
            name=op.f("fk_acs_pii_findings_scan_id_ai_connector_security_scans"),
            ondelete="CASCADE",
        ),
        *_tenant_fks("acs_pii_findings"),
    )
    _ix(
        "acs_pii_findings",
        [
            "scan_id",
            "segment_key",
            "pii_type",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "acs_output_validations",
        sa.Column("scan_id", sa.String(length=36), nullable=False),
        sa.Column("check_key", sa.String(length=64), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        *_tenant_cols(),
        sa.ForeignKeyConstraint(
            ["scan_id"],
            ["ai_connector_security_scans.id"],
            name=op.f("fk_acs_output_validations_scan_id_ai_connector_security_scans"),
            ondelete="CASCADE",
        ),
        *_tenant_fks("acs_output_validations"),
        sa.UniqueConstraint(
            "scan_id", "check_key", name=op.f("uq_acs_output_validations_scan_id")
        ),
    )
    _ix(
        "acs_output_validations",
        [
            "scan_id",
            "check_key",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )

    op.create_table(
        "acs_control_activations",
        sa.Column("scan_id", sa.String(length=36), nullable=False),
        sa.Column("control_kind", sa.String(length=64), nullable=False),
        sa.Column("control_label", sa.String(length=255), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("rank_order", sa.Integer(), nullable=False),
        *_tenant_cols(),
        sa.ForeignKeyConstraint(
            ["scan_id"],
            ["ai_connector_security_scans.id"],
            name=op.f("fk_acs_control_activations_scan_id_ai_connector_security_scans"),
            ondelete="CASCADE",
        ),
        *_tenant_fks("acs_control_activations"),
        sa.UniqueConstraint(
            "scan_id", "control_kind", name=op.f("uq_acs_control_activations_scan_id")
        ),
    )
    _ix(
        "acs_control_activations",
        [
            "scan_id",
            "control_kind",
            "organisation_id",
            "workspace_id",
            "created_by",
            "status",
        ],
    )


def downgrade() -> None:
    op.drop_table("acs_control_activations")
    op.drop_table("acs_output_validations")
    op.drop_table("acs_pii_findings")
    op.drop_table("acs_url_safety_checks")
    op.drop_table("acs_permission_checks")
    op.drop_table("acs_injection_findings")
    op.drop_table("acs_content_segments")
    op.drop_table("ai_connector_security_scans")
