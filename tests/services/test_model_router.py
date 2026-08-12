"""ModelRouter — primary / secondary / fallback selection under constraints."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from capability_router import (
    CapabilityProfileRepository,
    CapabilityRouter,
    FreshnessRequirement,
    ModelRouter,
    ModelRouterRequest,
    OrganisationPolicy,
    TaskComplexity,
)
from db_models import Organisation
from db_models.base import new_uuid


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


def test_model_router_request_contract() -> None:
    req = ModelRouterRequest(
        task_type="RESEARCH",
        complexity=TaskComplexity.HIGH,
        freshness_requirement=FreshnessRequirement.HIGH,
        required_capabilities=["WEB_GROUNDING", "CITATION_EXTRACTION"],
        expected_context_size=32_000,
        accuracy_requirement=0.8,
        latency_target=4000,
        budget=20_000,
        organisation_policy=OrganisationPolicy(denied_providers=["deepseek"]),
    )
    payload = req.to_dict()
    assert payload["task_type"] == "RESEARCH"
    assert payload["complexity"] == "high"
    assert payload["freshness_requirement"] == "high"
    assert "WEB_GROUNDING" in payload["required_capabilities"]
    assert payload["organisation_policy"]["denied_providers"] == ["deepseek"]


@pytest.mark.skipif(not _can_connect(), reason="PostgreSQL not available")
def test_model_router_returns_primary_secondary_fallback() -> None:
    from db_models import Workspace as WorkspaceModel

    engine = create_engine(_database_url())
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = SessionLocal()
    try:
        org = db.scalar(select(Organisation).limit(1))
        if org is None:
            pytest.skip("Seed organisation required")

        suffix = new_uuid()[:8]
        workspace = WorkspaceModel(
            id=new_uuid(),
            organisation_id=org.id,
            name=f"model-router-{suffix}",
            slug=f"model-router-{suffix}",
        )
        db.add(workspace)
        db.commit()

        repo = CapabilityProfileRepository(db)
        repo.seed_soft_priors()
        router = ModelRouter(CapabilityRouter(repo), session=db)

        result = router.route(
            ModelRouterRequest(
                task_type="RESEARCH",
                complexity=TaskComplexity.HIGH,
                freshness_requirement=FreshnessRequirement.HIGH,
                required_capabilities=["WEB_GROUNDING"],
                expected_context_size=16_000,
                accuracy_requirement=0.6,
                latency_target=5000,
                budget=50_000,
                organisation_policy=OrganisationPolicy(prefer_observed=True),
                organisation_id=org.id,
                workspace_id=workspace.id,
            )
        )
        assert result.primary_model.provider_code == "perplexity"
        assert result.primary_model.key
        assert result.secondary_model is not None
        assert result.fallback_model is not None
        assert result.secondary_model.key != result.primary_model.key
        assert "permanent" in result.reason.lower() or "dynamic" in result.reason.lower()
        assert result.permanent_role_locks is False
        payload = result.to_dict()
        assert payload["primary_model"]["provider_code"] == "perplexity"
        assert payload["reason"]
        assert payload["permanent_role_locks"] is False

        # Policy can deny the soft research prior — routing must still succeed elsewhere
        denied = router.route(
            ModelRouterRequest(
                task_type="STRATEGY",
                complexity=TaskComplexity.MEDIUM,
                freshness_requirement=FreshnessRequirement.NONE,
                required_capabilities=["STRUCTURED_OUTPUT"],
                expected_context_size=8_000,
                accuracy_requirement=0.5,
                latency_target=6000,
                budget=40_000,
                organisation_policy=OrganisationPolicy(denied_providers=["perplexity"]),
                organisation_id=org.id,
                workspace_id=workspace.id,
            )
        )
        assert denied.primary_model.provider_code != "perplexity"
        assert denied.primary_model.provider_code in {"openai", "anthropic", "gemini", "deepseek"}
    finally:
        db.close()
