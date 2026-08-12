"""Peacock Learning Engine 2.0 — closed loop + no universal GEO strategy."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from db_models import Organisation, Website, Workspace
from db_models.base import new_uuid
from db_models.learning_engine2 import Learning2Record
from learning_engine2 import (
    INDUSTRIES,
    NOT_UNIVERSAL_GEO,
    ExecutionUpdate,
    LearningRecordSpec,
    OutcomeUpdate,
    build_record_view,
    default_industry_policies,
    learn_from_records,
)
from learning_engine2.learning import apply_execution, apply_outcome
from learning_engine2.models import Learning2CreateSpec
from learning_engine2.service import LearningEngine2Service


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


def test_industries_and_default_policies() -> None:
    assert set(INDUSTRIES) == {
        "finance",
        "healthcare",
        "saas",
        "ecommerce",
        "education",
        "travel",
        "legal",
        "consumer_goods",
        "technology",
    }
    policies = default_industry_policies()
    assert len(policies) == 9
    assert all(p.forbidden_universal_claims == NOT_UNIVERSAL_GEO for p in policies)
    assert all("universal" in p.forbidden_universal_claims.lower() for p in policies)


def test_closed_loop_fields_and_learning() -> None:
    finance = build_record_view(
        LearningRecordSpec(
            name="Finance filing cite",
            industry="finance",
            context_summary="Low citation on disclosure queries",
            recommendation_text="Add primary filing citations",
            expected_impact="Lift AI citation on disclosure intents",
            expected_impact_score=70,
            confidence=65,
            topic_key="disclosures",
            format_key="regulatory_explainer",
            source_key="primary_filing",
            writer_key="writer_a",
            intervention_key="add_primary_source",
            engine_key="perplexity",
        )
    )
    assert finance.context_summary
    assert finance.recommendation_text
    assert finance.expected_impact
    assert finance.confidence == 65
    assert finance.not_universal_geo_strategy is True

    finance = apply_execution(
        finance, ExecutionUpdate("Published filing-backed explainer")
    )
    finance = apply_outcome(
        finance, OutcomeUpdate("Citation rate improved", actual_outcome_score=82)
    )
    assert finance.execution_summary
    assert finance.actual_outcome
    assert finance.outcome_delta is not None

    saas = build_record_view(
        LearningRecordSpec(
            name="SaaS comparison",
            industry="saas",
            context_summary="Weak comparison presence",
            recommendation_text="Ship structured comparison page",
            expected_impact="Improve answer presence",
            expected_impact_score=60,
            confidence=55,
            topic_key="comparisons",
            format_key="comparison",
            source_key="docs",
            writer_key="writer_b",
            intervention_key="structured_comparison",
            engine_key="chatgpt",
        )
    )
    saas = apply_execution(saas, ExecutionUpdate("Shipped comparison"))
    saas = apply_outcome(saas, OutcomeUpdate("Modest lift", actual_outcome_score=50))

    result = learn_from_records([finance, saas])
    assert result.records_considered == 2
    assert result.not_universal_geo_strategy is True
    assert "universal" in result.summary.lower() or NOT_UNIVERSAL_GEO
    assert set(result.learning_questions) >= {
        "topics",
        "formats",
        "sources",
        "writers",
        "citation_interventions",
        "industries",
        "engines",
    }
    assert any(i.dimension == "format" for i in result.insights)
    assert any(i.dimension == "industry" for i in result.insights)
    # Industry policies remain distinct — not one universal policy
    assert len(result.industry_policies) == 9
    finance_policy = next(p for p in result.industry_policies if p.industry == "finance")
    saas_policy = next(p for p in result.industry_policies if p.industry == "saas")
    assert finance_policy.policy_code != saas_policy.policy_code
    assert finance_policy.guidance != saas_policy.guidance


@pytest.mark.skipif(not _can_connect(), reason="PostgreSQL not available")
def test_persist_learning2_loop() -> None:
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
            name=f"le2-{suffix}",
            slug=f"le2-{suffix}",
        )
        db.add(workspace)
        db.flush()
        website = Website(
            id=new_uuid(),
            organisation_id=org.id,
            workspace_id=workspace.id,
            name=f"Site {suffix}",
            primary_domain=f"le2-{suffix}.com",
            root_url=f"https://le2-{suffix}.com",
        )
        db.add(website)
        db.commit()

        svc = LearningEngine2Service(db)
        view = build_record_view(
            LearningRecordSpec(
                name=f"Rec {suffix}",
                industry="healthcare",
                context_summary="Weak evidence cues",
                recommendation_text="Add study citations",
                expected_impact="Improve citation trust",
                expected_impact_score=68,
                confidence=60,
                format_key="evidence_summary",
                intervention_key="cite_study",
                engine_key="gemini",
            )
        )
        report = svc.create_record(
            organisation_id=org.id,
            workspace_id=workspace.id,
            created_by=None,
            spec=Learning2CreateSpec(website_id=website.id, view=view),
        )
        report = svc.record_execution(
            record_id=report.record_id,
            organisation_id=org.id,
            update=ExecutionUpdate("Published evidence summary"),
        )
        report = svc.record_outcome(
            record_id=report.record_id,
            organisation_id=org.id,
            update=OutcomeUpdate("Citations up", actual_outcome_score=75),
        )
        run = svc.run_learning(
            organisation_id=org.id,
            workspace_id=workspace.id,
            name=f"Run {suffix}",
            website_id=website.id,
        )
        assert run.result.not_universal_geo_strategy is True
        assert run.result.records_considered >= 1
        row = db.scalar(
            select(Learning2Record).where(Learning2Record.id == report.record_id)
        )
        assert row is not None
        assert row.not_universal_geo_strategy is True
        assert row.record_status == "learned"
    finally:
        db.close()
