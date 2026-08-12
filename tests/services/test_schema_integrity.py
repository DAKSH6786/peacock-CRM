from __future__ import annotations

from sqlalchemy import inspect

from db_models import (
    AiProvider,
    AiProviderModel,
    AuditLog,
    AuditLogAttribute,
    BackgroundJob,
    EmbeddingChunk,
    EmbeddingChunkAttribute,
    Membership,
    Role,
    RolePermission,
    Workspace,
    WorkspaceMembership,
)
from db_models.provider_seed import REQUIRED_PROVIDER_CODES, SUPPORTED_AI_PROVIDERS


def _fk_map(model) -> dict[str, str | None]:
    """local_col -> ondelete"""
    out: dict[str, str | None] = {}
    for column in inspect(model).columns:
        for fk in column.foreign_keys:
            out[column.name] = fk.ondelete
    return out


def test_supported_providers_include_required_five() -> None:
    codes = {p.code for p in SUPPORTED_AI_PROVIDERS}
    assert codes == {"openai", "gemini", "anthropic", "perplexity", "deepseek"}
    assert REQUIRED_PROVIDER_CODES == codes
    # Human-facing Claude name maps to anthropic code
    claude = next(p for p in SUPPORTED_AI_PROVIDERS if p.code == "anthropic")
    assert claude.name == "Claude"
    for provider in SUPPORTED_AI_PROVIDERS:
        assert provider.models, f"{provider.code} must declare at least one model"
        assert sum(1 for m in provider.models if m.is_default) == 1


def test_tenant_foreign_keys_use_careful_cascades() -> None:
    workspace_fks = _fk_map(Workspace)
    assert workspace_fks["organisation_id"] == "CASCADE"

    membership_fks = _fk_map(Membership)
    assert membership_fks["organisation_id"] == "CASCADE"
    assert membership_fks["user_id"] == "CASCADE"
    assert membership_fks["role_id"] == "RESTRICT"

    ws_membership_fks = _fk_map(WorkspaceMembership)
    assert ws_membership_fks["workspace_id"] == "CASCADE"
    assert ws_membership_fks["role_id"] == "RESTRICT"

    job_fks = _fk_map(BackgroundJob)
    assert job_fks["organisation_id"] == "CASCADE"
    assert job_fks["workspace_id"] == "SET NULL"
    assert job_fks["created_by_user_id"] == "SET NULL"

    audit_fks = _fk_map(AuditLog)
    assert audit_fks["organisation_id"] == "CASCADE"
    assert audit_fks["actor_user_id"] == "SET NULL"
    assert audit_fks["workspace_id"] == "SET NULL"

    embed_fks = _fk_map(EmbeddingChunk)
    assert embed_fks["organisation_id"] == "CASCADE"
    assert embed_fks["workspace_id"] == "SET NULL"

    assert _fk_map(RolePermission)["role_id"] == "CASCADE"
    assert _fk_map(RolePermission)["permission_id"] == "CASCADE"
    assert _fk_map(AuditLogAttribute)["audit_log_id"] == "CASCADE"
    assert _fk_map(EmbeddingChunkAttribute)["chunk_id"] == "CASCADE"
    assert _fk_map(AiProviderModel)["provider_id"] == "CASCADE"


def test_jsonb_only_on_heterogeneous_job_contracts() -> None:
    """JSONB is reserved for job payload/result — not identity/audit/embeddings."""

    def jsonb_columns(model) -> set[str]:
        found: set[str] = set()
        for column in inspect(model).columns:
            type_name = type(column.type).__name__.lower()
            if "json" in type_name:
                found.add(column.name)
        return found

    assert jsonb_columns(BackgroundJob) == {"payload", "result"}
    assert jsonb_columns(AuditLog) == set()
    assert jsonb_columns(AuditLogAttribute) == set()
    assert jsonb_columns(EmbeddingChunk) == set()
    assert jsonb_columns(EmbeddingChunkAttribute) == set()
    assert jsonb_columns(AiProvider) == set()
    assert jsonb_columns(Role) == set()


def test_role_permission_and_provider_tables_are_relational() -> None:
    assert RolePermission.__tablename__ == "role_permissions"
    assert AiProvider.__tablename__ == "ai_providers"
    assert AiProviderModel.__tablename__ == "ai_provider_models"
    # Workspace membership uses role_id FK, not a free-text role_code
    assert "role_id" in inspect(WorkspaceMembership).columns
    assert "role_code" not in inspect(WorkspaceMembership).columns
