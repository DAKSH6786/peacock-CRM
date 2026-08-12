"""Add organisation foreign keys for tenant isolation.

Revision ID: 0002_org_fks
Revises: 0001_initial
Create Date: 2026-08-12
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "0002_org_fks"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_foreign_key(
        op.f("fk_workspaces_organisation_id_organisations"),
        "workspaces",
        "organisations",
        ["organisation_id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_roles_organisation_id_organisations"),
        "roles",
        "organisations",
        ["organisation_id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_memberships_organisation_id_organisations"),
        "memberships",
        "organisations",
        ["organisation_id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_workspace_memberships_organisation_id_organisations"),
        "workspace_memberships",
        "organisations",
        ["organisation_id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_background_jobs_organisation_id_organisations"),
        "background_jobs",
        "organisations",
        ["organisation_id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_audit_logs_organisation_id_organisations"),
        "audit_logs",
        "organisations",
        ["organisation_id"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_embedding_chunks_organisation_id_organisations"),
        "embedding_chunks",
        "organisations",
        ["organisation_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(op.f("fk_embedding_chunks_organisation_id_organisations"), "embedding_chunks", type_="foreignkey")
    op.drop_constraint(op.f("fk_audit_logs_organisation_id_organisations"), "audit_logs", type_="foreignkey")
    op.drop_constraint(op.f("fk_background_jobs_organisation_id_organisations"), "background_jobs", type_="foreignkey")
    op.drop_constraint(op.f("fk_workspace_memberships_organisation_id_organisations"), "workspace_memberships", type_="foreignkey")
    op.drop_constraint(op.f("fk_memberships_organisation_id_organisations"), "memberships", type_="foreignkey")
    op.drop_constraint(op.f("fk_roles_organisation_id_organisations"), "roles", type_="foreignkey")
    op.drop_constraint(op.f("fk_workspaces_organisation_id_organisations"), "workspaces", type_="foreignkey")
