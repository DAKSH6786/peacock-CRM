"""Content Digital Twin — pre-publish simulation and plan rerun."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from content_digital_twin import (
    FINDING_CATEGORIES,
    SIMULATION_SURFACES,
    AiAnswerScenario,
    ArticlePlan,
    BrandGuidelines,
    CompetitorPageRef,
    ContentDigitalTwinService,
    PersonaRef,
    SimulationContext,
    TwinSpec,
    simulate_article_plan,
)
from db_models import Organisation, Website, Workspace
from db_models.base import new_uuid
from db_models.content_digital_twin import CdtEvaluation, ContentDigitalTwin


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


def _weak_plan() -> ArticlePlan:
    return ArticlePlan(
        title="What is CRM",
        slug="what-is-crm",
        outline_sections=["Introduction", "Definition", "Conclusion"],
        target_keywords=["crm"],
        covered_entities=[],
        evidence_claims=[],
        questions_answered=[],
        differentiation_angles=[],
        planned_citations=[],
        structured_elements=[],
        body_summary="A short definition of CRM.",
    )


def _strong_plan() -> ArticlePlan:
    return ArticlePlan(
        title="CRM Benchmark 2026: Pipeline Conversion Study",
        slug="crm-benchmark-2026",
        outline_sections=[
            "Executive summary with direct answer",
            "Methodology and original survey",
            "Comparison table vs competitors",
            "FAQ: how to improve conversion",
            "Entity glossary",
        ],
        target_keywords=["crm benchmark", "pipeline conversion", "sales velocity"],
        covered_entities=["Peacock CRM", "Salesforce", "HubSpot", "pipeline conversion"],
        evidence_claims=[
            "n=1200 survey fresh statistics",
            "original experiment on cadence",
        ],
        questions_answered=[
            "What improves CRM pipeline conversion?",
            "How does Peacock CRM compare to HubSpot?",
            "What is sales velocity?",
        ],
        differentiation_angles=["proprietary benchmark study", "first-party cohort data"],
        planned_citations=["internal survey 2026", "Gartner CRM Magic Quadrant"],
        structured_elements=["faq", "table", "definition", "comparison"],
        brand_voice_notes="confident precise expert tone",
        body_summary=(
            "Original dataset comparing Peacock CRM, Salesforce, and HubSpot on "
            "pipeline conversion with fresh statistics and source attribution."
        ),
    )


def _rich_context() -> SimulationContext:
    return SimulationContext(
        seo_requirements=["crm benchmark", "pipeline conversion", "meta description"],
        aeo_requirements=["direct answer", "faq", "definition"],
        geo_requirements=["entity clarity", "source attribution", "fresh statistics"],
        competitor_pages=[
            CompetitorPageRef(
                url="https://rival.example/crm-guide",
                title="Rival CRM Guide",
                strengths=["original survey", "comparison table"],
                entities=["HubSpot", "sales velocity"],
                questions_covered=["What improves CRM pipeline conversion?"],
                evidence_types=["survey", "table"],
            )
        ],
        target_entities=["Peacock CRM", "Salesforce", "HubSpot", "pipeline conversion"],
        user_personas=[
            PersonaRef(
                name="RevOps lead",
                intents=["improve conversion"],
                questions=["What improves CRM pipeline conversion?"],
            )
        ],
        ai_answer_scenarios=[
            AiAnswerScenario(
                prompt="best CRM for pipeline conversion 2026",
                must_include_entities=["Peacock CRM"],
                must_answer_points=["pipeline conversion"],
            )
        ],
        citation_requirements=["primary survey source", "analyst report"],
        brand_guidelines=BrandGuidelines(
            tone_keywords=["precise", "expert"],
            required_mentions=["Peacock CRM"],
            forbidden_claims=["guaranteed #1 ranking"],
        ),
    )


def test_simulation_surfaces_and_findings_catalog() -> None:
    assert set(SIMULATION_SURFACES) == {
        "seo_requirements",
        "aeo_requirements",
        "geo_requirements",
        "competitor_pages",
        "target_entities",
        "user_personas",
        "ai_answer_scenarios",
        "citation_requirements",
        "brand_guidelines",
    }
    assert set(FINDING_CATEGORIES) == {
        "predicted_strength",
        "potential_weakness",
        "missing_entity",
        "missing_evidence",
        "missing_question",
        "competitor_advantage",
        "citation_opportunity",
        "differentiation_opportunity",
    }


def test_weak_plan_flags_gaps() -> None:
    result = simulate_article_plan(_weak_plan(), _rich_context())
    assert 0 <= result.predicted_strength_score <= 100
    assert result.readiness_score <= result.predicted_strength_score + 1
    surfaces = {s.surface for s in result.requirement_scores}
    assert surfaces == set(SIMULATION_SURFACES)
    cats = {f.category for f in result.findings}
    assert "missing_entity" in cats
    assert "missing_question" in cats or "potential_weakness" in cats
    assert "competitor_advantage" in cats or "differentiation_opportunity" in cats
    assert "citation_opportunity" in cats or "missing_evidence" in cats


def test_strong_plan_outperforms_weak() -> None:
    weak = simulate_article_plan(_weak_plan(), _rich_context())
    strong = simulate_article_plan(_strong_plan(), _rich_context())
    assert strong.predicted_strength_score > weak.predicted_strength_score
    assert strong.readiness_score > weak.readiness_score
    assert any(f.category == "predicted_strength" for f in strong.findings)
    # Strong plan should cover Peacock CRM entity
    entity_score = next(
        s for s in strong.requirement_scores if s.surface == "target_entities"
    )
    assert entity_score.coverage_score >= 70


def test_plan_improvement_lifts_score() -> None:
    ctx = _rich_context()
    before = simulate_article_plan(_weak_plan(), ctx)
    improved = ArticlePlan(
        title="What is CRM — Peacock CRM Buyer Guide",
        slug="what-is-crm-guide",
        outline_sections=["Direct answer definition", "FAQ", "Comparison table"],
        target_keywords=["crm benchmark", "pipeline conversion"],
        covered_entities=["Peacock CRM", "Salesforce", "HubSpot", "pipeline conversion"],
        evidence_claims=["n=400 cohort"],
        questions_answered=["What improves CRM pipeline conversion?"],
        differentiation_angles=["first-party cohort"],
        planned_citations=["primary survey source", "analyst report"],
        structured_elements=["faq", "definition", "table"],
        brand_voice_notes="precise expert",
        body_summary="Peacock CRM definition with FAQ and comparison vs HubSpot.",
    )
    after = simulate_article_plan(improved, ctx)
    assert after.predicted_strength_score > before.predicted_strength_score


@pytest.mark.skipif(not _can_connect(), reason="PostgreSQL not available")
def test_twin_create_update_rerun_persists() -> None:
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
            name=f"cdt-{suffix}",
            slug=f"cdt-{suffix}",
        )
        db.add(workspace)
        db.flush()
        website = Website(
            id=new_uuid(),
            organisation_id=org.id,
            workspace_id=workspace.id,
            name=f"Site {suffix}",
            primary_domain=f"cdt-{suffix}.com",
            root_url=f"https://cdt-{suffix}.com",
        )
        db.add(website)
        db.commit()

        svc = ContentDigitalTwinService(db)
        report = svc.create_twin(
            organisation_id=org.id,
            workspace_id=workspace.id,
            spec=TwinSpec(
                website_id=website.id,
                name=f"Twin {suffix}",
                client_brand="Peacock CRM",
                article_plan=_weak_plan(),
                simulation_context=_rich_context(),
            ),
        )
        assert report.evaluation_count == 1
        assert report.latest_evaluation is not None
        first_score = report.latest_evaluation.predicted_strength_score

        updated = svc.update_plan(
            twin_id=report.twin_id,
            organisation_id=org.id,
            article_plan=_strong_plan(),
            rerun=True,
        )
        assert updated.plan_revision == 2
        assert updated.evaluation_count == 2
        assert updated.latest_evaluation is not None
        assert (
            updated.latest_evaluation.predicted_strength_score >= first_score
        )

        rerun = svc.rerun_evaluation(
            twin_id=report.twin_id,
            organisation_id=org.id,
        )
        assert rerun.evaluation_count == 3

        rows = list(
            db.scalars(
                select(CdtEvaluation).where(
                    CdtEvaluation.twin_id == report.twin_id
                )
            ).all()
        )
        assert len(rows) == 3
        twin_row = db.scalar(
            select(ContentDigitalTwin).where(
                ContentDigitalTwin.id == report.twin_id
            )
        )
        assert twin_row is not None
        assert twin_row.plan_revision == 2
    finally:
        db.close()
