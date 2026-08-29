"""Relational hardening: cascades, AI providers, replace JSONB bags.

Revision ID: 0003_relational_hardening
Revises: 0002_org_fks
Create Date: 2026-08-12
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_relational_hardening"
down_revision: Union[str, None] = "0002_org_fks"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Cascade policy on existing organisation FKs ──────────────────────────
    _recreate_fk(
        "workspaces",
        "fk_workspaces_organisation_id_organisations",
        "organisations",
        ["organisation_id"],
        ["id"],
        ondelete="CASCADE",
    )
    _recreate_fk(
        "roles",
        "fk_roles_organisation_id_organisations",
        "organisations",
        ["organisation_id"],
        ["id"],
        ondelete="CASCADE",
    )
    _recreate_fk(
        "memberships",
        "fk_memberships_organisation_id_organisations",
        "organisations",
        ["organisation_id"],
        ["id"],
        ondelete="CASCADE",
    )
    _recreate_fk(
        "memberships",
        "fk_memberships_user_id_users",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    _recreate_fk(
        "memberships",
        "fk_memberships_role_id_roles",
        "roles",
        ["role_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    _recreate_fk(
        "workspace_memberships",
        "fk_workspace_memberships_organisation_id_organisations",
        "organisations",
        ["organisation_id"],
        ["id"],
        ondelete="CASCADE",
    )
    _recreate_fk(
        "workspace_memberships",
        "fk_workspace_memberships_workspace_id_workspaces",
        "workspaces",
        ["workspace_id"],
        ["id"],
        ondelete="CASCADE",
    )
    _recreate_fk(
        "workspace_memberships",
        "fk_workspace_memberships_user_id_users",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    _recreate_fk(
        "background_jobs",
        "fk_background_jobs_organisation_id_organisations",
        "organisations",
        ["organisation_id"],
        ["id"],
        ondelete="CASCADE",
    )
    _recreate_fk(
        "audit_logs",
        "fk_audit_logs_organisation_id_organisations",
        "organisations",
        ["organisation_id"],
        ["id"],
        ondelete="CASCADE",
    )
    _recreate_fk(
        "embedding_chunks",
        "fk_embedding_chunks_organisation_id_organisations",
        "organisations",
        ["organisation_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # ── Workspace membership: role_code → role_id ────────────────────────────
    op.add_column(
        "workspace_memberships",
        sa.Column("role_id", sa.String(length=36), nullable=True),
    )
    op.execute(
        """
        UPDATE workspace_memberships wm
        SET role_id = (
            SELECT r.id FROM roles r
            WHERE r.organisation_id = wm.organisation_id
              AND r.code = wm.role_code
            LIMIT 1
        )
        """
    )
    op.execute(
        """
        UPDATE workspace_memberships wm
        SET role_id = (
            SELECT r.id FROM roles r
            WHERE r.organisation_id = wm.organisation_id
            ORDER BY CASE WHEN r.code = 'owner' THEN 0 ELSE 1 END, r.created_at
            LIMIT 1
        )
        WHERE role_id IS NULL
        """
    )
    op.alter_column("workspace_memberships", "role_id", nullable=False)
    op.create_index(
        op.f("ix_workspace_memberships_role_id"),
        "workspace_memberships",
        ["role_id"],
    )
    op.create_foreign_key(
        op.f("fk_workspace_memberships_role_id_roles"),
        "workspace_memberships",
        "roles",
        ["role_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.drop_column("workspace_memberships", "role_code")

    # ── Background jobs: workspace + creator FKs ─────────────────────────────
    op.add_column(
        "background_jobs",
        sa.Column("created_by_user_id", sa.String(length=36), nullable=True),
    )
    op.create_index(
        op.f("ix_background_jobs_created_by_user_id"),
        "background_jobs",
        ["created_by_user_id"],
    )
    op.create_foreign_key(
        op.f("fk_background_jobs_workspace_id_workspaces"),
        "background_jobs",
        "workspaces",
        ["workspace_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        op.f("fk_background_jobs_created_by_user_id_users"),
        "background_jobs",
        "users",
        ["created_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # ── Audit logs: actor/workspace FKs; replace metadata JSONB ──────────────
    op.create_foreign_key(
        op.f("fk_audit_logs_actor_user_id_users"),
        "audit_logs",
        "users",
        ["actor_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        op.f("fk_audit_logs_workspace_id_workspaces"),
        "audit_logs",
        "workspaces",
        ["workspace_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_audit_logs_resource_id"), "audit_logs", ["resource_id"])

    op.create_table(
        "audit_log_attributes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("audit_log_id", sa.String(length=36), nullable=False),
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("value", sa.String(length=2000), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["audit_log_id"],
            ["audit_logs.id"],
            name=op.f("fk_audit_log_attributes_audit_log_id_audit_logs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_log_attributes")),
        sa.UniqueConstraint("audit_log_id", "key", name=op.f("uq_audit_log_attributes_audit_log_id")),
    )
    op.create_index(
        op.f("ix_audit_log_attributes_audit_log_id"),
        "audit_log_attributes",
        ["audit_log_id"],
    )
    # Migrate existing JSONB metadata keys into attributes when present
    op.execute(
        """
        INSERT INTO audit_log_attributes (id, audit_log_id, key, value, created_at, updated_at)
        SELECT gen_random_uuid()::text,
               a.id,
               kv.key,
               left(kv.value #>> '{}', 2000),
               NOW(),
               NOW()
        FROM audit_logs a
        CROSS JOIN LATERAL jsonb_each(COALESCE(a.metadata, '{}'::jsonb)) AS kv(key, value)
        WHERE jsonb_typeof(COALESCE(a.metadata, '{}'::jsonb)) = 'object'
        """
    )
    op.drop_column("audit_logs", "metadata")

    # ── Embedding chunks: workspace FK + structured columns; drop metadata ───
    op.add_column(
        "embedding_chunks",
        sa.Column("content_hash", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "embedding_chunks",
        sa.Column("embedding_model", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "embedding_chunks",
        sa.Column("token_count", sa.Integer(), nullable=True),
    )
    op.create_index(op.f("ix_embedding_chunks_content_hash"), "embedding_chunks", ["content_hash"])
    op.create_index(op.f("ix_embedding_chunks_source_type"), "embedding_chunks", ["source_type"])
    op.create_foreign_key(
        op.f("fk_embedding_chunks_workspace_id_workspaces"),
        "embedding_chunks",
        "workspaces",
        ["workspace_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "embedding_chunk_attributes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("chunk_id", sa.String(length=36), nullable=False),
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("value", sa.String(length=2000), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["chunk_id"],
            ["embedding_chunks.id"],
            name=op.f("fk_embedding_chunk_attributes_chunk_id_embedding_chunks"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_embedding_chunk_attributes")),
        sa.UniqueConstraint("chunk_id", "key", name=op.f("uq_embedding_chunk_attributes_chunk_id")),
    )
    op.create_index(
        op.f("ix_embedding_chunk_attributes_chunk_id"),
        "embedding_chunk_attributes",
        ["chunk_id"],
    )
    op.execute(
        """
        INSERT INTO embedding_chunk_attributes (id, chunk_id, key, value, created_at, updated_at)
        SELECT gen_random_uuid()::text,
               c.id,
               kv.key,
               left(kv.value #>> '{}', 2000),
               NOW(),
               NOW()
        FROM embedding_chunks c
        CROSS JOIN LATERAL jsonb_each(COALESCE(c.metadata, '{}'::jsonb)) AS kv(key, value)
        WHERE jsonb_typeof(COALESCE(c.metadata, '{}'::jsonb)) = 'object'
        """
    )
    op.drop_column("embedding_chunks", "metadata")

    # ── Role ↔ permission join ───────────────────────────────────────────────
    op.create_table(
        "role_permissions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("role_id", sa.String(length=36), nullable=False),
        sa.Column("permission_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permissions.id"],
            name=op.f("fk_role_permissions_permission_id_permissions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
            name=op.f("fk_role_permissions_role_id_roles"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_role_permissions")),
        sa.UniqueConstraint("role_id", "permission_id", name=op.f("uq_role_permissions_role_id")),
    )
    op.create_index(op.f("ix_role_permissions_role_id"), "role_permissions", ["role_id"])
    op.create_index(
        op.f("ix_role_permissions_permission_id"), "role_permissions", ["permission_id"]
    )

    # ── AI provider catalog ──────────────────────────────────────────────────
    op.create_table(
        "ai_providers",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("vendor", sa.String(length=128), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("supports_chat", sa.Boolean(), nullable=False),
        sa.Column("supports_embeddings", sa.Boolean(), nullable=False),
        sa.Column("supports_web_grounding", sa.Boolean(), nullable=False),
        sa.Column("documentation_url", sa.String(length=512), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_providers")),
        sa.UniqueConstraint("code", name=op.f("uq_ai_providers_code")),
    )

    op.create_table(
        "ai_provider_models",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("provider_id", sa.String(length=36), nullable=False),
        sa.Column("model_code", sa.String(length=128), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("context_window_tokens", sa.Integer(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["provider_id"],
            ["ai_providers.id"],
            name=op.f("fk_ai_provider_models_provider_id_ai_providers"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_provider_models")),
        sa.UniqueConstraint(
            "provider_id", "model_code", name=op.f("uq_ai_provider_models_provider_id")
        ),
    )
    op.create_index(
        op.f("ix_ai_provider_models_provider_id"), "ai_provider_models", ["provider_id"]
    )


def downgrade() -> None:
    op.drop_table("ai_provider_models")
    op.drop_table("ai_providers")
    op.drop_table("role_permissions")

    op.add_column(
        "embedding_chunks",
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.execute("UPDATE embedding_chunks SET metadata = '{}'::jsonb")
    op.alter_column("embedding_chunks", "metadata", nullable=False)
    op.drop_table("embedding_chunk_attributes")
    op.drop_constraint(
        op.f("fk_embedding_chunks_workspace_id_workspaces"),
        "embedding_chunks",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_embedding_chunks_source_type"), table_name="embedding_chunks")
    op.drop_index(op.f("ix_embedding_chunks_content_hash"), table_name="embedding_chunks")
    op.drop_column("embedding_chunks", "token_count")
    op.drop_column("embedding_chunks", "embedding_model")
    op.drop_column("embedding_chunks", "content_hash")

    op.add_column(
        "audit_logs",
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.execute("UPDATE audit_logs SET metadata = '{}'::jsonb")
    op.alter_column("audit_logs", "metadata", nullable=False)
    op.drop_table("audit_log_attributes")
    op.drop_index(op.f("ix_audit_logs_resource_id"), table_name="audit_logs")
    op.drop_constraint(op.f("fk_audit_logs_workspace_id_workspaces"), "audit_logs", type_="foreignkey")
    op.drop_constraint(op.f("fk_audit_logs_actor_user_id_users"), "audit_logs", type_="foreignkey")

    op.drop_constraint(
        op.f("fk_background_jobs_created_by_user_id_users"),
        "background_jobs",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_background_jobs_workspace_id_workspaces"),
        "background_jobs",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_background_jobs_created_by_user_id"), table_name="background_jobs")
    op.drop_column("background_jobs", "created_by_user_id")

    op.add_column(
        "workspace_memberships",
        sa.Column("role_code", sa.String(length=64), nullable=True),
    )
    op.execute(
        """
        UPDATE workspace_memberships wm
        SET role_code = COALESCE(
            (SELECT r.code FROM roles r WHERE r.id = wm.role_id),
            'member'
        )
        """
    )
    op.alter_column("workspace_memberships", "role_code", nullable=False)
    op.drop_constraint(
        op.f("fk_workspace_memberships_role_id_roles"),
        "workspace_memberships",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_workspace_memberships_role_id"), table_name="workspace_memberships")
    op.drop_column("workspace_memberships", "role_id")


def _recreate_fk(
    table: str,
    name: str,
    referent: str,
    local_cols: list[str],
    remote_cols: list[str],
    *,
    ondelete: str,
) -> None:
    op.drop_constraint(name, table, type_="foreignkey")
    op.create_foreign_key(
        name,
        table,
        referent,
        local_cols,
        remote_cols,
        ondelete=ondelete,
    )
