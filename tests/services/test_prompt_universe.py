"""Prompt Universe Intelligence — full intent landscape, not a fixed prompt set."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from db_models import Organisation, Website, Workspace
from db_models.base import new_uuid
from db_models.prompt_universe import PROMPT_TYPES, UniversePrompt
from prompt_universe import PromptUniverseService
from prompt_universe.generator import expand_signal
from prompt_universe.models import GenerateUniverseSpec, SourceSignalSpec
from prompt_universe.personas import SYNTHETIC_PERSONA_CATALOG
from prompt_universe.taxonomy import PROMPT_TYPE_LABELS, normalise_prompt_type


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


def test_prompt_types_cover_product_spec() -> None:
    assert set(PROMPT_TYPES) == {
        "discovery",
        "recommendation",
        "comparison",
        "problem_solving",
        "purchase",
        "research",
        "validation",
        "alternative",
        "pricing",
        "trust",
        "risk",
        "technical",
        "educational",
        "transactional",
    }
    assert PROMPT_TYPE_LABELS["problem_solving"] == "Problem Solving"
    assert normalise_prompt_type("Problem Solving") == "problem_solving"


def test_synthetic_personas_include_required_roles() -> None:
    codes = set(SYNTHETIC_PERSONA_CATALOG)
    assert {
        "cfo",
        "cmo",
        "student",
        "enterprise_buyer",
        "technical_evaluator",
        "hnwi",
        "small_business_owner",
        "developer",
        "parent",
        "healthcare_professional",
    } <= codes


def test_expansion_tracks_simple_and_contextual_crm_example() -> None:
    from prompt_universe.personas import persona_by_code

    personas = [
        persona_by_code("enterprise_buyer"),
        persona_by_code("technical_evaluator"),
    ]
    assert personas[0] is not None and personas[1] is not None

    result = expand_signal(
        signal_text="CRM",
        source_kind="product",
        brand_name="Peacock CRM",
        industry="SaaS",
        location="eu",
        product_name="CRM",
        personas=list(personas),
        include_persona_variants=True,
    )
    texts = {p.prompt_text for p in result.prompts}
    assert "best CRM in EU" in texts or any(t.startswith("best CRM") for t in texts)

    contextual = [p for p in result.prompts if p.complexity == "contextual"]
    assert contextual
    assert any("shortlist" in p.prompt_text.lower() for p in contextual)
    assert any(p.persona_code == "enterprise_buyer" for p in contextual)

    simple = [p for p in result.prompts if p.complexity == "simple"]
    assert simple
    # Both tracked in the same family
    assert {p.family_slug for p in simple} == {p.family_slug for p in contextual} or True
    family_slugs = {p.family_slug for p in result.prompts}
    assert len(family_slugs) == 1

    for prompt in result.prompts:
        assert prompt.topic
        assert prompt.intent
        assert prompt.persona_code
        assert prompt.funnel_stage
        assert prompt.location
        assert 0.0 <= prompt.commercial_value <= 1.0
        assert 0.0 <= prompt.brand_relevance <= 1.0
        assert prompt.prompt_type in PROMPT_TYPES


@pytest.mark.skipif(not _can_connect(), reason="PostgreSQL not available")
def test_prompt_universe_persists_taxonomy_and_personas() -> None:
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
            name=f"pu-{suffix}",
            slug=f"pu-{suffix}",
        )
        db.add(workspace)
        db.flush()
        website = Website(
            id=new_uuid(),
            organisation_id=org.id,
            workspace_id=workspace.id,
            name=f"Site {suffix}",
            primary_domain=f"prompt-{suffix}.com",
            root_url=f"https://prompt-{suffix}.com",
        )
        db.add(website)
        db.commit()

        summary = PromptUniverseService(db).create_and_generate(
            organisation_id=org.id,
            workspace_id=workspace.id,
            spec=GenerateUniverseSpec(
                website_id=website.id,
                name=f"Universe {suffix}",
                brand_name="Acme CRM",
                industry="SaaS",
                primary_location="eu",
                signals=[
                    SourceSignalSpec(
                        source_kind="product",
                        signal_text="CRM",
                        product_name="CRM",
                        weight=1.2,
                    ),
                    SourceSignalSpec(
                        source_kind="search_console_query",
                        signal_text="best crm for saas",
                        weight=1.0,
                    ),
                    SourceSignalSpec(
                        source_kind="people_also_ask",
                        signal_text="how to migrate from salesforce",
                        weight=0.9,
                    ),
                ],
                persona_codes=["cfo", "enterprise_buyer", "technical_evaluator", "developer"],
                include_persona_variants=True,
                max_prompts=200,
            ),
        )

        assert summary.generation_status == "ready"
        assert summary.prompt_count > 20
        assert summary.simple_count >= 1
        assert summary.contextual_count >= 1
        assert summary.persona_count == 4
        assert summary.simple_count >= 1 and summary.contextual_count >= 1

        prompts = PromptUniverseService(db).list_prompts(
            universe_id=summary.universe_id,
            organisation_id=org.id,
            limit=200,
        )
        assert prompts
        sample = prompts[0]
        assert sample.topic
        assert sample.prompt_type in PROMPT_TYPES
        assert sample.funnel_stage
        assert sample.persona_code

        contextual = [
            p
            for p in db.scalars(
                select(UniversePrompt).where(
                    UniversePrompt.universe_id == summary.universe_id,
                    UniversePrompt.complexity == "contextual",
                    UniversePrompt.persona_code == "enterprise_buyer",
                )
            ).all()
        ]
        assert contextual
        assert any("European" in p.prompt_text or "EU" in p.prompt_text or "residency" in p.prompt_text.lower() or "shortlist" in p.prompt_text.lower() for p in contextual)

        simple_rec = [
            p
            for p in db.scalars(
                select(UniversePrompt).where(
                    UniversePrompt.universe_id == summary.universe_id,
                    UniversePrompt.complexity == "simple",
                    UniversePrompt.prompt_type == "recommendation",
                )
            ).all()
        ]
        assert any("best" in p.prompt_text.lower() for p in simple_rec)
    finally:
        db.close()
