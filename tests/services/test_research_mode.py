"""Peacock Research Mode — controlled laboratory studies."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from db_models import Organisation, Website, Workspace
from db_models.base import new_uuid
from db_models.research_mode import STUDY_PHASES, ResearchStudy
from research_mode import (
    ResearchStudySpec,
    analyse_research_study,
    catalog,
)
from research_mode.models import ResearchModeCreateSpec
from research_mode.service import ResearchModeService


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


def test_catalog_laboratory_positioning() -> None:
    c = catalog()
    assert c["study_phases"] == list(STUDY_PHASES)
    assert "hypothesis" in c["study_phases"]
    assert "findings" in c["study_phases"]
    assert "laboratory" in c["laboratory_positioning"].lower()
    assert "SEO software" in c["laboratory_positioning"]
    assert "proprietary statistics" in c["example_research_question"].lower()


def test_demo_study_runs_full_pipeline() -> None:
    result = analyse_research_study(
        ResearchStudySpec(
            client_brand="Acme",
            research_question=(
                "Does adding proprietary statistics increase AI citation probability?"
            ),
            hypothesis=(
                "Adding proprietary statistics increases AI citation probability "
                "on treatment pages."
            ),
            metric_key="ai_citation_probability",
            treatment_description="Add proprietary statistics blocks.",
            observation_rounds=3,
        )
    )
    assert result.completed_phases == list(STUDY_PHASES)
    assert result.pages_count >= 2
    assert result.prompts_count >= 2
    assert result.observation_rounds >= 3
    assert len(result.observations) >= 12
    assert result.baseline_mean is not None
    assert result.treatment_mean is not None
    assert result.absolute_delta is not None
    assert result.uncertainty_band in ("low", "moderate", "high", "very_high")
    assert result.findings
    assert all(f.auto_causal_conclusion_rejected for f in result.findings)
    assert "laboratory" in result.laboratory_positioning.lower()


@pytest.mark.skipif(not _can_connect(), reason="PostgreSQL not available")
def test_persist_research_study() -> None:
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
            name=f"rm-{suffix}",
            slug=f"rm-{suffix}",
        )
        db.add(workspace)
        db.flush()
        website = Website(
            id=new_uuid(),
            organisation_id=org.id,
            workspace_id=workspace.id,
            name=f"Site {suffix}",
            primary_domain=f"rm-{suffix}.com",
            root_url=f"https://rm-{suffix}.com",
        )
        db.add(website)
        db.commit()

        report = ResearchModeService(db).run_study(
            organisation_id=org.id,
            workspace_id=workspace.id,
            created_by=None,
            spec=ResearchModeCreateSpec(
                website_id=website.id,
                name=f"RM {suffix}",
                study=ResearchStudySpec(
                    client_brand="Acme",
                    research_question=(
                        "Does adding proprietary statistics increase AI citation probability?"
                    ),
                    hypothesis="Proprietary stats lift citation probability.",
                    metric_key="ai_citation_probability",
                    treatment_description="Add proprietary statistics.",
                ),
            ),
        )
        assert report.study_id
        row = db.scalar(select(ResearchStudy).where(ResearchStudy.id == report.study_id))
        assert row is not None
        assert row.finding_verdict
        assert "hypothesis" in row.completed_phases
    finally:
        db.close()
