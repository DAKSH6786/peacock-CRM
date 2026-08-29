"""Final Peacock Architecture — system map + product difference standard."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from db_models import Organisation, Website, Workspace
from db_models.base import new_uuid
from db_models.final_architecture import (
    PIPELINE_STAGES,
    PRODUCT_QUESTIONS,
    FinalArchitectureMap,
)
from final_architecture import (
    FinalArchitectureCreateSpec,
    FinalArchitectureService,
    FinalArchitectureSpec,
    build_architecture_map,
    catalog,
    demo_map,
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


def test_catalog_pipeline_and_questions() -> None:
    c = catalog()
    assert c["pipeline_stages"] == list(PIPELINE_STAGES)
    assert "peacock_learning" in c["pipeline_stages"]
    assert c["learning_loops_to"] == "pine"
    assert len(c["product_questions"]) == 13
    assert c["product_question_text"]["how_visible"] == "How visible are we?"
    assert c["product_question_text"]["what_did_peacock_learn"] == "What did Peacock learn?"
    assert "How visible are we?" in c["not_only_visibility_note"]
    assert "PEACOCK ONE" in c["architecture_diagram"]
    assert "PEACOCK LEARNING" in c["architecture_diagram"]


def test_demo_full_standard() -> None:
    result = demo_map("Acme")
    assert result.stages_count == len(PIPELINE_STAGES)
    assert result.observation_sources_count == 5
    assert result.pine_lanes_count == 3
    assert result.product_questions_count == 13
    assert result.learning_loops_to_pine is True
    assert result.not_only_visibility is True
    assert result.product_standard_coverage == 100.0
    learning = next(s for s in result.stages if s.stage_key == "peacock_learning")
    assert learning.loops_to_stage_key == "pine"
    assert all(q.addressed for q in result.product_questions)


def test_visibility_only_fails_not_only_flag() -> None:
    result = build_architecture_map(
        FinalArchitectureSpec(
            client_brand="Acme",
            addressed_questions=["how_visible"],
            assume_full_standard=False,
        )
    )
    assert result.product_standard_coverage < 20
    assert result.not_only_visibility is False


@pytest.mark.skipif(not _can_connect(), reason="PostgreSQL not available")
def test_persist_architecture_map() -> None:
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
            name=f"fa-{suffix}",
            slug=f"fa-{suffix}",
        )
        db.add(workspace)
        db.flush()
        website = Website(
            id=new_uuid(),
            organisation_id=org.id,
            workspace_id=workspace.id,
            name=f"Site {suffix}",
            primary_domain=f"fa-{suffix}.com",
            root_url=f"https://fa-{suffix}.com",
        )
        db.add(website)
        db.commit()

        report = FinalArchitectureService(db).create_map(
            organisation_id=org.id,
            workspace_id=workspace.id,
            created_by=None,
            spec=FinalArchitectureCreateSpec(
                website_id=website.id,
                name=f"FA {suffix}",
                architecture=FinalArchitectureSpec(client_brand="Acme"),
            ),
        )
        assert report.result.product_questions_count == len(PRODUCT_QUESTIONS)
        row = db.scalar(
            select(FinalArchitectureMap).where(
                FinalArchitectureMap.id == report.map_id
            )
        )
        assert row is not None
        assert row.learning_loops_to_pine is True

        loaded = FinalArchitectureService(db).get_map(
            map_id=report.map_id, organisation_id=org.id
        )
        assert loaded is not None
        assert len(loaded.result.stages) == len(PIPELINE_STAGES)
    finally:
        db.close()
