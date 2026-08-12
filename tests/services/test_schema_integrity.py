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
    # PINE IntelligenceCase (relational aggregate — no monolithic JSON)
    "intelligence_cases",
    "intelligence_case_context_items",
    "intelligence_case_observations",
    "intelligence_case_evidence",
    "intelligence_case_evidence_urls",
    "intelligence_case_hypotheses",
    "intelligence_case_agent_findings",
    "intelligence_case_agent_claims",
    "intelligence_case_contradictions",
    "intelligence_case_unknowns",
    "intelligence_case_assumptions",
    "intelligence_case_risks",
    "intelligence_case_opportunities",
    "intelligence_case_recommendations",
    "intelligence_case_recommendation_evidence",
    "intelligence_case_models_used",
    "intelligence_case_tools_used",
    # Evidence Ledger graph
    "ledger_evidences",
    "ledger_findings",
    "ledger_recommendations",
    "ledger_actions",
    "ledger_outcomes",
    "ledger_evidence_finding_links",
    "ledger_finding_recommendation_links",
    "ledger_recommendation_action_links",
    "ledger_action_outcome_links",
    "ledger_claim_evidence_links",
    # Dynamic model capability profiles
    "model_capability_priors",
    "model_capability_profiles",
    "model_capability_observations",
    # Probabilistic AI Visibility
    "visibility_campaigns",
    "visibility_probe_cells",
    "visibility_probe_observations",
    "visibility_distributions",
    "visibility_score_cards",
    # Prompt Universe Intelligence
    "prompt_universes",
    "synthetic_personas",
    "prompt_source_signals",
    "prompt_families",
    "universe_prompts",
    "prompt_generation_runs",
    # Share of Answer
    "share_of_answer_analyses",
    "soa_answer_observations",
    "soa_entity_indicators",
    "soa_brand_scores",
    # Citation Graph
    "citation_graph_analyses",
    "cg_observations",
    "cg_citations",
    "cg_entity_mentions",
    "cg_pathways",
    "cg_domain_scores",
    "cg_source_opportunities",
    # Retrieval Pathway Intelligence
    "retrieval_pathway_analyses",
    "rpi_evidence",
    "rpi_cause_classifications",
    "rpi_bottleneck_diagnoses",
    # Entity Intelligence
    "entity_intelligence_analyses",
    "ei_entities",
    "ei_associations",
    "ei_entity_gaps",
    "ei_strategies",
    # Deep Competitor Intelligence
    "deep_competitor_analyses",
    "dc_competitor_profiles",
    "dc_competitive_deltas",
    "dc_content_diffs",
    "dc_differentiated_strategies",
    # Content Lab
    "content_lab_analyses",
    "cl_content_proposals",
    "cl_info_gain_signals",
    "cl_citability_components",
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
    assert len(registered) >= 118


def test_intelligence_case_is_relational_not_json_blob() -> None:
    from db_models import (
        IntelligenceCaseAgentFinding,
        IntelligenceCaseEvidence,
        IntelligenceCaseRecord,
        IntelligenceCaseRecommendation,
    )

    assert issubclass(IntelligenceCaseRecord, WorkspaceTenantMixin)
    assert _jsonb_columns(IntelligenceCaseRecord) == set()
    assert _jsonb_columns(IntelligenceCaseEvidence) == set()
    assert _jsonb_columns(IntelligenceCaseAgentFinding) == set()
    assert _jsonb_columns(IntelligenceCaseRecommendation) == set()

    case_fks = _fk_map(IntelligenceCaseRecord)
    assert case_fks["organisation_id"] == "CASCADE"
    assert case_fks["workspace_id"] == "CASCADE"
    assert case_fks["website_id"] == "SET NULL"

    evidence_fks = _fk_map(IntelligenceCaseEvidence)
    assert evidence_fks["case_id"] == "CASCADE"

    # Evidence stores typed scalars, not a value JSON bag
    evidence_cols = {c.name for c in inspect(IntelligenceCaseEvidence).columns}
    assert {"value_text", "value_number", "value_bool", "kind"} <= evidence_cols
    assert "value" not in evidence_cols
    assert "payload" not in evidence_cols


def test_evidence_ledger_is_relational_graph() -> None:
    from db_models import (
        EVIDENCE_TYPES,
        LedgerAction,
        LedgerEvidence,
        LedgerEvidenceFindingLink,
        LedgerFinding,
        LedgerOutcome,
        LedgerRecommendation,
    )

    assert issubclass(LedgerEvidence, WorkspaceTenantMixin)
    assert issubclass(LedgerFinding, WorkspaceTenantMixin)
    assert issubclass(LedgerRecommendation, WorkspaceTenantMixin)
    assert issubclass(LedgerAction, WorkspaceTenantMixin)
    assert issubclass(LedgerOutcome, WorkspaceTenantMixin)

    for model in (LedgerEvidence, LedgerFinding, LedgerRecommendation, LedgerAction, LedgerOutcome):
        assert _jsonb_columns(model) == set()

    required_types = {
        "CRAWL",
        "SERP",
        "ANALYTICS",
        "SEARCH_CONSOLE",
        "BACKLINK",
        "AI_RESPONSE",
        "COMPETITOR_PAGE",
        "USER_DATA",
        "MODEL_INFERENCE",
        "EXTERNAL_SOURCE",
        "HISTORICAL_OUTCOME",
        "EXPERIMENT",
    }
    assert set(EVIDENCE_TYPES) == required_types

    evidence_cols = {c.name for c in inspect(LedgerEvidence).columns}
    assert {
        "source",
        "observed_at",
        "freshness_hours",
        "freshness_score",
        "confidence",
        "scope_kind",
        "scope_ref",
        "value_text",
        "value_number",
        "value_bool",
        "evidence_type",
    } <= evidence_cols

    assert _fk_map(LedgerEvidence)["organisation_id"] == "CASCADE"
    assert _fk_map(LedgerEvidenceFindingLink)["evidence_id"] == "CASCADE"
    assert _fk_map(LedgerEvidenceFindingLink)["finding_id"] == "CASCADE"


def test_capability_profiles_track_required_metrics() -> None:
    from db_models import (
        CAPABILITY_TASK_TYPES,
        ModelCapabilityObservation,
        ModelCapabilityPrior,
        ModelCapabilityProfile,
    )

    required_tasks = {
        "RESEARCH",
        "SEO_REASONING",
        "GEO_REASONING",
        "ENTITY_EXTRACTION",
        "CITATION_EXTRACTION",
        "STRUCTURED_OUTPUT",
        "CRITICAL_ANALYSIS",
        "SUMMARISATION",
        "STRATEGY",
        "CONTENT_ANALYSIS",
        "COMPETITOR_ANALYSIS",
        "FACT_VERIFICATION",
        "LONG_CONTEXT_ANALYSIS",
    }
    assert set(CAPABILITY_TASK_TYPES) == required_tasks

    assert issubclass(ModelCapabilityProfile, WorkspaceTenantMixin)
    assert _jsonb_columns(ModelCapabilityPrior) == set()
    assert _jsonb_columns(ModelCapabilityProfile) == set()
    assert _jsonb_columns(ModelCapabilityObservation) == set()

    profile_cols = {c.name for c in inspect(ModelCapabilityProfile).columns}
    assert {
        "provider_code",
        "model_code",
        "task_type",
        "quality_score",
        "latency_ms_avg",
        "cost_usd_micros_avg",
        "failure_rate",
        "json_compliance_rate",
        "citation_accuracy",
        "historical_agreement",
        "sample_size",
    } <= profile_cols

    assert _fk_map(ModelCapabilityObservation)["profile_id"] == "CASCADE"


def test_probabilistic_visibility_tables_are_relational() -> None:
    from db_models import (
        VisibilityCampaign,
        VisibilityDistribution,
        VisibilityProbeObservation,
        VisibilityScoreCard,
    )

    assert issubclass(VisibilityCampaign, WorkspaceTenantMixin)
    assert _jsonb_columns(VisibilityCampaign) == set()
    assert _jsonb_columns(VisibilityDistribution) == set()
    assert _jsonb_columns(VisibilityScoreCard) == set()

    campaign_cols = {c.name for c in inspect(VisibilityCampaign).columns}
    assert {
        "target_repetitions",
        "max_repetitions",
        "max_calls_per_minute",
        "max_concurrent",
        "max_total_calls",
        "min_interval_ms",
    } <= campaign_cols

    dist_cols = {c.name for c in inspect(VisibilityDistribution).columns}
    assert {
        "probability",
        "variance",
        "ci_low",
        "ci_high",
        "sample_size",
        "engine_disagreement",
        "temporal_volatility",
    } <= dist_cols

    score_cols = {c.name for c in inspect(VisibilityScoreCard).columns}
    assert {
        "ai_visibility_score",
        "measurement_confidence",
        "peacock_visibility_confidence",
        "observation_count",
        "engine_count",
        "prompt_count",
        "period_count",
    } <= score_cols

    assert _fk_map(VisibilityProbeObservation)["campaign_id"] == "CASCADE"
    assert _fk_map(VisibilityDistribution)["campaign_id"] == "CASCADE"

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
