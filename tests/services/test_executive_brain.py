"""Peacock Executive Brain — executive Q&A + CEO/CMO summaries."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from db_models import Organisation, Website, Workspace
from db_models.base import new_uuid
from db_models.executive_brain import EXECUTIVE_QUESTIONS, ExecutiveBrainBrief
from executive_brain import (
    ExecutiveBrainSpec,
    catalog,
    synthesise_executive_brain,
)
from executive_brain.models import ExecutiveBrainCreateSpec
from executive_brain.service import ExecutiveBrainService


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


def test_catalog_questions() -> None:
    c = catalog()
    assert c["executive_questions"] == list(EXECUTIVE_QUESTIONS)
    assert "ceo" in c["summary_roles"] and "cmo" in c["summary_roles"]
    assert "SEO complexity" in c["product_note"]


def test_synthesis_answers_all_executive_questions() -> None:
    result = synthesise_executive_brain(
        ExecutiveBrainSpec(client_brand="Acme", budget_label="₹10 lakh")
    )
    keys = [a.question_key for a in result.answers]
    assert keys == list(EXECUTIVE_QUESTIONS)
    assert all(a.answer for a in result.answers)
    assert all(0.0 <= a.confidence <= 1.0 for a in result.answers)
    roles = {r.role for r in result.role_summaries}
    assert roles == {"ceo", "cmo"}
    ceo = next(r for r in result.role_summaries if r.role == "ceo")
    assert ceo.call_to_action
    assert "18%" in ceo.body or "citation" in ceo.body.lower()
    assert "₹10 lakh" in result.budget_label
    losing = next(a for a in result.answers if a.question_key == "where_losing")
    assert "31%" in losing.answer or "citation" in losing.answer.lower()


@pytest.mark.skipif(not _can_connect(), reason="PostgreSQL not available")
def test_persist_executive_brief() -> None:
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
            name=f"eb-{suffix}",
            slug=f"eb-{suffix}",
        )
        db.add(workspace)
        db.flush()
        website = Website(
            id=new_uuid(),
            organisation_id=org.id,
            workspace_id=workspace.id,
            name=f"Site {suffix}",
            primary_domain=f"eb-{suffix}.com",
            root_url=f"https://eb-{suffix}.com",
        )
        db.add(website)
        db.commit()

        report = ExecutiveBrainService(db).create_brief(
            organisation_id=org.id,
            workspace_id=workspace.id,
            created_by=None,
            spec=ExecutiveBrainCreateSpec(
                website_id=website.id,
                name=f"EB {suffix}",
                brief=ExecutiveBrainSpec(client_brand="Acme"),
            ),
        )
        assert report.brief_id
        row = db.scalar(
            select(ExecutiveBrainBrief).where(ExecutiveBrainBrief.id == report.brief_id)
        )
        assert row is not None
        assert len(report.result.role_summaries) == 2
    finally:
        db.close()
