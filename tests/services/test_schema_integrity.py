from __future__ import annotations

from sqlalchemy import inspect

import db_models as models
from db_models import (
    AiProvider,
    AiProviderModel,
    AuditLog,
    AuditLogAttribute,
    BackgroundJob,
    Crawl,
    EmbeddingChunk,
    EmbeddingChunkAttribute,
    GenerativeEngine,
    LLMModel,
    LLMProvider,
    LLMRequest,
    Membership,
    Organization,
    Organisation,
    Recommendation,
    Role,
    RolePermission,
    Website,
    WebsiteProperty,
    Workspace,
    WorkspaceMembership,
)
from db_models.base import WorkspaceTenantMixin
from db_models.generative_engine_seed import GENERATIVE_ENGINE_SEEDS
from db_models.provider_seed import REQUIRED_PROVIDER_CODES, SUPPORTED_AI_PROVIDERS


REQUIRED_CORE_TABLES = {
    # Identity
    "organisations",
    "users",
    "workspaces",
    "roles",
    "permissions",
    "role_permissions",
    "memberships",
    "workspace_memberships",
    # Platform
    "ai_providers",
    "ai_provider_models",
    "background_jobs",
    "audit_logs",
    "audit_log_attributes",
    "embedding_chunks",
    "embedding_chunk_attributes",
    # Websites / crawls / audits
    "websites",
    "domains",
    "website_properties",
    "crawls",
    "crawl_pages",
    "crawl_links",
    "crawl_issues",
    "audits",
    "audit_sections",
    "audit_metrics",
    "audit_issues",
    "audit_recommendations",
    # SEO
    "seo_scores",
    "technical_seo_results",
    "onpage_seo_results",
    "internal_link_results",
    "schema_results",
    "performance_results",
    # GEO / AEO
    "generative_engines",
    "ai_queries",
    "ai_query_runs",
    "ai_response_observations",
    "brand_mentions",
    "citation_observations",
    "entity_observations",
    "aeo_observations",
    "geo_metrics",
    "ai_visibility_snapshots",
    # Competitors / content / writers / roadmaps / monitoring
    "competitors",
    "competitor_websites",
    "competitor_metrics",
    "competitor_contents",
    "competitor_gaps",
    "topics",
    "topic_clusters",
    "topic_recommendations",
    "keywords",
    "keyword_clusters",
    "content_briefs",
    "content_recommendations",
    "backlink_opportunities",
    "citation_sources",
    "writers",
    "writer_samples",
    "writer_profiles",
    "writer_skills",
    "writer_industry_expertise",
    "writer_performances",
    "writer_recommendations",
    "writer_assignments",
    "roadmaps",
    "roadmap_months",
    "roadmap_weeks",
    "roadmap_tasks",
    "roadmap_recommendations",
    "monitoring_projects",
    "metric_snapshots",
    "search_performance_snapshots",
    # LLM + learning
    "llm_requests",
    "llm_responses",
    "agent_runs",
    "agent_results",
    "council_runs",
    "decisions",
    "evidences",
    "recommendations",
    "recommendation_executions",
    "recommendation_metrics",
    "recommendation_outcomes",
    "feature_weights",
    "model_evaluations",
}


def _fk_map(model) -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    for column in inspect(model).columns:
        for fk in column.foreign_keys:
            out[column.name] = fk.ondelete
    return out


def _jsonb_columns(model) -> set[str]:
    found: set[str] = set()
    for column in inspect(model).columns:
        type_name = type(column.type).__name__.lower()
        if "json" in type_name:
            found.add(column.name)
    return found


def test_supported_providers_include_required_five() -> None:
    codes = {p.code for p in SUPPORTED_AI_PROVIDERS}
    assert codes == {"openai", "gemini", "anthropic", "perplexity", "deepseek"}
    assert REQUIRED_PROVIDER_CODES == codes
    claude = next(p for p in SUPPORTED_AI_PROVIDERS if p.code == "anthropic")
    assert claude.name == "Claude"
    for provider in SUPPORTED_AI_PROVIDERS:
        assert provider.models, f"{provider.code} must declare at least one model"
        assert sum(1 for m in provider.models if m.is_default) == 1


def test_generative_engine_seeds_cover_five_providers() -> None:
    provider_codes = {s.provider_code for s in GENERATIVE_ENGINE_SEEDS if s.provider_code}
    assert {"openai", "gemini", "anthropic", "perplexity", "deepseek"} <= provider_codes
    engine_codes = {s.code for s in GENERATIVE_ENGINE_SEEDS}
    assert {"chatgpt", "gemini", "claude", "perplexity", "deepseek"} <= engine_codes


def test_naming_aliases() -> None:
    assert Organization is Organisation
    assert LLMProvider is AiProvider
    assert LLMModel is AiProviderModel


def test_core_domain_tables_registered() -> None:
    registered = set(models.Base.metadata.tables)
    missing = REQUIRED_CORE_TABLES - registered
    assert not missing, f"Missing tables: {sorted(missing)}"
    assert len(registered) >= 86


def test_workspace_tenant_mixin_fields() -> None:
    assert issubclass(Website, WorkspaceTenantMixin)
    assert issubclass(Recommendation, WorkspaceTenantMixin)
    cols = inspect(Website).columns
    for name in ("id", "organisation_id", "workspace_id", "created_by", "status", "created_at", "updated_at"):
        assert name in cols


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

    website_fks = _fk_map(Website)
    assert website_fks["organisation_id"] == "CASCADE"
    assert website_fks["workspace_id"] == "CASCADE"
    assert website_fks["created_by"] == "SET NULL"

    assert _fk_map(GenerativeEngine)["llm_provider_id"] == "SET NULL"
    assert _fk_map(LLMRequest)["provider_id"] == "RESTRICT"
    assert _fk_map(LLMRequest)["agent_run_id"] == "SET NULL"


def test_jsonb_only_on_justified_columns() -> None:
    assert _jsonb_columns(BackgroundJob) == {"payload", "result"}
    assert _jsonb_columns(Crawl) == {"config"}
    assert _jsonb_columns(LLMRequest) == {"messages"}
    assert _jsonb_columns(Website) == {"extensions"}
    assert _jsonb_columns(AuditLog) == set()
    assert _jsonb_columns(AuditLogAttribute) == set()
    assert _jsonb_columns(EmbeddingChunk) == set()
    assert _jsonb_columns(EmbeddingChunkAttribute) == set()
    assert _jsonb_columns(AiProvider) == set()
    assert _jsonb_columns(Role) == set()
    assert _jsonb_columns(WebsiteProperty) == set()
    assert _jsonb_columns(Recommendation) == set()

    # Variable-length page extraction snapshots use JSONB with stable item shapes.
    from db_models import CrawlPage

    assert _jsonb_columns(CrawlPage) == {
        "internal_links",
        "external_links",
        "images",
        "schema_blocks",
        "redirect_chain",
    }

    allowed = {
        ("background_jobs", "payload"),
        ("background_jobs", "result"),
        ("crawls", "config"),
        ("llm_requests", "messages"),
        ("websites", "extensions"),
        ("crawl_pages", "internal_links"),
        ("crawl_pages", "external_links"),
        ("crawl_pages", "images"),
        ("crawl_pages", "schema_blocks"),
        ("crawl_pages", "redirect_chain"),
    }
    found: set[tuple[str, str]] = set()
    for table in models.Base.metadata.tables.values():
        for column in table.columns:
            type_name = type(column.type).__name__.lower()
            if "json" in type_name:
                found.add((table.name, column.name))
    assert found == allowed


def test_role_permission_and_provider_tables_are_relational() -> None:
    assert RolePermission.__tablename__ == "role_permissions"
    assert AiProvider.__tablename__ == "ai_providers"
    assert AiProviderModel.__tablename__ == "ai_provider_models"
    assert "role_id" in inspect(WorkspaceMembership).columns
    assert "role_code" not in inspect(WorkspaceMembership).columns


def test_single_ai_visibility_snapshot_table() -> None:
    assert models.AIVisibilitySnapshot.__tablename__ == "ai_visibility_snapshots"
    # Monitoring reuses the GEO/AEO snapshot model — no duplicate table
    assert "ai_visibility_snapshots" in models.Base.metadata.tables
    duplicates = [name for name in models.Base.metadata.tables if "ai_visibility" in name]
    assert duplicates == ["ai_visibility_snapshots"]
