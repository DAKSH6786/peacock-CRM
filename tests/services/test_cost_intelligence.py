"""Peacock Cost Intelligence — Intelligence Budget Engine."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from db_models import Organisation, Website, Workspace
from db_models.base import new_uuid
from db_models.cost_intelligence import (
    METHOD_KINDS,
    IntelligenceBudgetEstimate,
)
from cost_intelligence import (
    BudgetEstimateSpec,
    CostIntelligenceCreateSpec,
    CostIntelligenceService,
    catalog,
    estimate_budget,
)


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


def test_catalog_policy() -> None:
    c = catalog()
    assert c["method_kinds"] == list(METHOD_KINDS)
    assert "deterministic" in c["method_ladder"]
    assert c["value_method_ceiling"]["trivial"] == "deterministic"
    assert "five LLMs" in c["policy_note"] or "five LLMs" in " ".join(c["examples"])
    assert "Council" in " ".join(c["examples"]) or "council" in c["policy_note"].lower()


def test_page_title_uses_deterministic_not_council() -> None:
    result = estimate_budget(
        BudgetEstimateSpec(
            client_brand="Acme",
            workflow_intent="page_title_recommendation",
            question="Recommend a better title for /pricing",
            decision_value="trivial",
        )
    )
    assert result.selected_method_kind == "deterministic"
    assert result.expected_calls == 0
    assert result.expected_tokens == 0
    assert result.expected_cost_usd_micros < 1_000
    assert result.rejected_expensive is True
    council = next(c for c in result.candidates if c.method_kind == "council")
    assert council.selected is False
    assert council.allowed_for_value is False
    assert "Council" in result.selection_rationale or "page-title" in result.selection_rationale.lower()


def test_soa_lookup_prefers_deterministic() -> None:
    result = estimate_budget(
        BudgetEstimateSpec(
            client_brand="Acme",
            workflow_intent="share_of_answer_lookup",
            question="What is our Share of Answer for CRM prompts?",
        )
    )
    assert result.selected_method_kind == "deterministic"
    assert result.expected_searches == 0


def test_council_strategy_allows_council() -> None:
    result = estimate_budget(
        BudgetEstimateSpec(
            client_brand="Acme",
            workflow_intent="council_strategy",
            question="Should we pivot GEO strategy against CompetitorX?",
            decision_value="critical",
        )
    )
    assert result.selected_method_kind == "council"
    assert result.expected_calls >= 10
    assert result.expected_tokens >= 10_000
    assert result.expected_cost_usd_micros >= 50_000
    assert result.selected_peacock_mode == "peacock_council"


def test_estimates_include_all_five_dimensions() -> None:
    result = estimate_budget(
        BudgetEstimateSpec(
            client_brand="Acme",
            workflow_intent="content_brief",
            question="Draft a brief for enterprise reliability",
        )
    )
    assert result.expected_calls >= 0
    assert result.expected_tokens >= 0
    assert result.expected_searches >= 0
    assert result.expected_runtime_seconds > 0
    assert result.expected_cost_usd_micros >= 0
    assert result.selected_method_kind in ("deterministic", "single_llm", "web_search")
    assert result.selected_method_kind != "council"


def test_empty_question_rejected() -> None:
    with pytest.raises(ValueError, match="question"):
        estimate_budget(
            BudgetEstimateSpec(client_brand="Acme", question="  ", workflow_intent="custom")
        )


@pytest.mark.skipif(not _can_connect(), reason="PostgreSQL not available")
def test_persist_budget_estimate() -> None:
    engine = create_engine(_database_url())
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = SessionLocal()
    try:
        org = db.scalar(select(Organisation).limit(1))
        if org is None:
            pytest.skip("Seed organisation required")
        suffix = new_uuid()[:8]
        workspace = Workspace(
            id=new_uuid(),
            organisation_id=org.id,
            name=f"cost-{suffix}",
            slug=f"cost-{suffix}",
        )
        db.add(workspace)
        db.flush()
        website = Website(
            id=new_uuid(),
            organisation_id=org.id,
            workspace_id=workspace.id,
            name=f"Site {suffix}",
            primary_domain=f"cost-{suffix}.com",
            root_url=f"https://cost-{suffix}.com",
        )
        db.add(website)
        db.commit()

        report = CostIntelligenceService(db).estimate(
            organisation_id=org.id,
            workspace_id=workspace.id,
            created_by=None,
            spec=CostIntelligenceCreateSpec(
                website_id=website.id,
                name=f"Cost {suffix}",
                estimate=BudgetEstimateSpec(
                    client_brand="Acme",
                    workflow_intent="page_title_recommendation",
                    question="Recommend a better title for /pricing",
                ),
            ),
        )
        assert report.result.selected_method_kind == "deterministic"
        row = db.scalar(
            select(IntelligenceBudgetEstimate).where(
                IntelligenceBudgetEstimate.id == report.estimate_id
            )
        )
        assert row is not None
        assert row.expected_calls == 0

        loaded = CostIntelligenceService(db).get_estimate(
            estimate_id=report.estimate_id, organisation_id=org.id
        )
        assert loaded is not None
        assert loaded.result.selected_method_kind == "deterministic"
        assert len(loaded.result.candidates) == len(METHOD_KINDS)
    finally:
        db.close()
