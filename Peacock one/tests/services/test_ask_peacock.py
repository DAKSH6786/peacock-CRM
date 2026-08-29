"""Ask Peacock 2.0 — structured NL answers over the intelligence graph."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from ask_peacock import (
    ANSWER_SECTIONS,
    EXAMPLE_QUESTIONS,
    QUERY_INTENTS,
    AskSessionSpec,
    answer_ask_session,
    detect_intent,
)
from ask_peacock.models import AskPeacockSpec
from ask_peacock.service import AskPeacockService
from db_models import Organisation, Website, Workspace
from db_models.ask_peacock import AskPeacockSession
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


def test_answer_sections_contract() -> None:
    assert ANSWER_SECTIONS == (
        "OBSERVED",
        "INFERRED",
        "RECOMMENDED",
        "FORECAST",
        "CONFIDENCE",
    )


def test_intent_routing_for_examples() -> None:
    assert detect_intent("Why is Competitor A beating us?") == "competitor_beating_us"
    assert (
        detect_intent("What should we do with ₹10 lakh over the next 90 days?")
        == "budget_allocation_90d"
    )
    assert (
        detect_intent("Which ten pages could generate the highest GEO improvement?")
        == "top_geo_pages"
    )
    assert detect_intent("Which writer should write Topic X?") == "writer_for_topic"
    assert (
        detect_intent("Where is our weakest generative engine?")
        == "weakest_generative_engine"
    )
    assert (
        detect_intent("What external sources are influencing AI opinions about us?")
        == "external_sources_influencing"
    )
    assert detect_intent("What changed this week?") == "what_changed_week"
    assert detect_intent("What should the CEO know?") == "ceo_brief"
    assert "custom" in QUERY_INTENTS


def test_demo_session_structured_with_evidence() -> None:
    result = answer_ask_session(
        AskSessionSpec(client_brand="Acme", questions=list(EXAMPLE_QUESTIONS))
    )
    assert result.answers_produced == len(EXAMPLE_QUESTIONS)
    assert result.evidence_items >= len(EXAMPLE_QUESTIONS)
    assert result.mean_confidence is not None
    for a in result.answers:
        d = a.to_dict()
        assert set(d["sections"]) == {
            "OBSERVED",
            "INFERRED",
            "RECOMMENDED",
            "FORECAST",
            "CONFIDENCE",
        }
        assert a.observed.startswith("OBSERVED")
        assert a.inferred.startswith("INFERRED")
        assert a.recommended.startswith("RECOMMENDED")
        assert a.forecast.startswith("FORECAST")
        assert 0.0 <= a.confidence <= 1.0
        assert a.evidence
        assert a.graph_surfaces_used
        assert all(e.section in ANSWER_SECTIONS for e in a.evidence)


def test_single_budget_question() -> None:
    result = answer_ask_session(
        AskSessionSpec(
            client_brand="Acme",
            questions=["What should we do with ₹10 lakh over the next 90 days?"],
        )
    )
    assert result.answers_produced == 1
    assert result.answers[0].intent == "budget_allocation_90d"
    assert "₹10 lakh" in result.answers[0].recommended or "lakh" in result.answers[0].observed


@pytest.mark.skipif(not _can_connect(), reason="PostgreSQL not available")
def test_persist_ask_session() -> None:
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
            name=f"ap-{suffix}",
            slug=f"ap-{suffix}",
        )
        db.add(workspace)
        db.flush()
        website = Website(
            id=new_uuid(),
            organisation_id=org.id,
            workspace_id=workspace.id,
            name=f"Site {suffix}",
            primary_domain=f"ap-{suffix}.com",
            root_url=f"https://ap-{suffix}.com",
        )
        db.add(website)
        db.commit()

        report = AskPeacockService(db).ask(
            organisation_id=org.id,
            workspace_id=workspace.id,
            created_by=None,
            spec=AskPeacockSpec(
                website_id=website.id,
                name=f"Ask {suffix}",
                session=AskSessionSpec(
                    client_brand="Acme",
                    questions=["What changed this week?", "What should the CEO know?"],
                ),
            ),
        )
        assert report.session_id
        assert report.result.answers_produced == 2
        row = db.scalar(
            select(AskPeacockSession).where(AskPeacockSession.id == report.session_id)
        )
        assert row is not None
        assert row.evidence_items >= 2
    finally:
        db.close()
