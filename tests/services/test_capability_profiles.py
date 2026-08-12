"""Dynamic capability profiles — no permanent provider role locks."""

from __future__ import annotations

import os
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from capability_router import (
    GATEWAY_ROLE_TASK_DEFAULTS,
    SOFT_CAPABILITY_PRIORS,
    CapabilityObservation,
    CapabilityProfileRepository,
    CapabilityRouter,
    CapabilityTaskType,
    route_completion_request,
)
from db_models import Organisation
from db_models.base import new_uuid
from llm_gateway.ports import LLMCompletionRequest, LLMProviderName
from llm_gateway.registry import LLMGateway
from llm_gateway.adapters.null_provider import NullLLMProvider


def _database_url() -> str:
    return os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://peacock:peacock@localhost:5432/peacock_one",
    )


def _can_connect() -> bool:
    try:
        engine = create_engine(_database_url())
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        return True
    except Exception:  # noqa: BLE001
        return False


def test_task_types_cover_product_contract() -> None:
    assert {t.value for t in CapabilityTaskType} == {
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


def test_soft_priors_are_not_permanent_locks() -> None:
    # Soft defaults may hint Claude/critical or Perplexity/research — never exclusive
    critical = [p for p in SOFT_CAPABILITY_PRIORS if p.task_type == "CRITICAL_ANALYSIS"]
    research = [p for p in SOFT_CAPABILITY_PRIORS if p.task_type == "RESEARCH"]
    strategy = [p for p in SOFT_CAPABILITY_PRIORS if p.task_type == "STRATEGY"]
    assert any(p.provider_code == "anthropic" for p in critical)
    assert any(p.provider_code == "perplexity" for p in research)
    assert any(p.provider_code == "openai" for p in strategy)
    # Multiple providers may hold strategy priors — not GPT-only forever
    assert len({p.provider_code for p in strategy}) >= 2
    assert GATEWAY_ROLE_TASK_DEFAULTS["VERIFY_ADVERSARIAL"] == "CRITICAL_ANALYSIS"
    assert GATEWAY_ROLE_TASK_DEFAULTS["WEB_RESEARCH"] == "RESEARCH"


def test_gateway_prefers_dynamic_provider_override() -> None:
    gateway = LLMGateway(
        providers={LLMProviderName.NULL: NullLLMProvider()},
        role_routing={"SYNTHESIS": LLMProviderName.NULL},
    )
    request = LLMCompletionRequest(
        organisation_id="org",
        role="SYNTHESIS",
        template_id="t",
        messages=[{"role": "user", "content": "x"}],
        provider="null",
        model="null-model",
        task_type="STRATEGY",
    )
    provider = gateway.provider_for_request(request)
    assert provider.name == LLMProviderName.NULL


@pytest.mark.skipif(not _can_connect(), reason="PostgreSQL not available")
def test_observed_profile_overrides_soft_prior() -> None:
    from db_models import Workspace as WorkspaceModel

    engine = create_engine(_database_url())
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = SessionLocal()
    try:
        org = db.scalar(select(Organisation).limit(1))
        if org is None:
            pytest.skip("Seed organisation required")

        # Isolated workspace so prior test runs cannot pollute routing
        suffix = new_uuid()[:8]
        workspace = WorkspaceModel(
            id=new_uuid(),
            organisation_id=org.id,
            name=f"capability-test-{suffix}",
            slug=f"capability-test-{suffix}",
        )
        db.add(workspace)
        db.commit()

        repo = CapabilityProfileRepository(db)
        repo.seed_soft_priors()

        router = CapabilityRouter(repo, min_samples_for_trust=3, prior_blend_until_samples=5)
        prior_decision = router.route(
            organisation_id=org.id,
            workspace_id=workspace.id,
            task_type="RESEARCH",
        )
        assert prior_decision.selected.provider_code == "perplexity"
        assert prior_decision.to_dict()["permanent_role_locks"] is False

        # Strong observed RESEARCH performance for openai should override soft prior
        for _ in range(8):
            repo.record_observation(
                organisation_id=org.id,
                workspace_id=workspace.id,
                observation=CapabilityObservation(
                    provider_code="openai",
                    model_code="gpt-4.1",
                    task_type="RESEARCH",
                    latency_ms=900,
                    cost_usd_micros=800,
                    succeeded=True,
                    quality_score=0.95,
                    json_compliant=True,
                    citation_accuracy=0.9,
                    historical_agreement=0.9,
                ),
            )

        decision = router.route(
            organisation_id=org.id,
            workspace_id=workspace.id,
            task_type="RESEARCH",
        )
        assert decision.selected.provider_code == "openai"
        assert decision.selected.sample_size >= 8
        assert decision.used_prior_only is False
        assert decision.to_dict()["permanent_role_locks"] is False

        request = LLMCompletionRequest(
            organisation_id=org.id,
            role="WEB_RESEARCH",
            template_id="intel.layer3.research",
            messages=[{"role": "user", "content": "research x"}],
        )
        routed, bridge_decision = route_completion_request(
            router, request, workspace_id=workspace.id
        )
        assert routed.provider == bridge_decision.selected.provider_code
        assert routed.model == bridge_decision.selected.model_code
        assert routed.task_type == "RESEARCH"
        assert routed.metadata["capability_routing"]["permanent_role_locks"] is False
    finally:
        db.close()
