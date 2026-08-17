"""Peacock Moat Data Model — proprietary intelligence pathways."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from db_models import Organisation, Website, Workspace
from db_models.base import new_uuid
from db_models.moat_data_model import (
    PATHWAY_KINDS,
    PATHWAY_LABELS,
    MoatIntelligenceRun,
)
from moat_data_model import (
    MoatCreateSpec,
    MoatDataModelService,
    MoatRunSpec,
    accumulate_moat,
    catalog,
    demo_pathways,
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


def test_catalog_covers_seven_pathway_kinds() -> None:
    c = catalog()
    assert c["pathway_kinds"] == list(PATHWAY_KINDS)
    assert len(c["pathway_kinds"]) == 7
    assert "recommendation → outcome" in c["example_pathways"]
    assert "competitive advantage" in c["moat_positioning"].lower()
    assert "not a universal" in c["not_universal_geo"].lower() or "industry-scoped" in c[
        "not_universal_geo"
    ].lower()


def test_demo_pathways_cover_all_kinds() -> None:
    specs = demo_pathways("Acme", industry="saas_b2b")
    kinds = {p.pathway_kind for p in specs}
    assert kinds == set(PATHWAY_KINDS)
    geo = next(p for p in specs if p.pathway_kind == "industry_geo_strategy_result")
    assert geo.industry == "saas_b2b"
    assert "not universal" in geo.narrative.lower()


def test_accumulate_moat_strength() -> None:
    result = accumulate_moat(MoatRunSpec(client_brand="Acme", industry="saas_b2b"))
    assert result.pathways_count == 7
    assert result.nodes_count >= 14
    assert result.edges_count >= 7
    assert result.outcomes_count == 7
    assert 0.0 < result.moat_strength_score <= 100.0
    assert set(result.pathway_kind_coverage) == set(PATHWAY_KINDS)
    labels = {p.pathway_label for p in result.pathways}
    assert labels == set(PATHWAY_LABELS.values())
    assert "competitive advantage" in result.summary.lower()


def test_empty_brand_rejected() -> None:
    with pytest.raises(ValueError, match="client_brand"):
        accumulate_moat(MoatRunSpec(client_brand="  "))


@pytest.mark.skipif(not _can_connect(), reason="PostgreSQL not available")
def test_persist_moat_run() -> None:
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
            name=f"moat-{suffix}",
            slug=f"moat-{suffix}",
        )
        db.add(workspace)
        db.flush()
        website = Website(
            id=new_uuid(),
            organisation_id=org.id,
            workspace_id=workspace.id,
            name=f"Site {suffix}",
            primary_domain=f"moat-{suffix}.com",
            root_url=f"https://moat-{suffix}.com",
        )
        db.add(website)
        db.commit()

        report = MoatDataModelService(db).accumulate(
            organisation_id=org.id,
            workspace_id=workspace.id,
            created_by=None,
            spec=MoatCreateSpec(
                website_id=website.id,
                name=f"Moat {suffix}",
                run=MoatRunSpec(client_brand="Acme", industry="saas_b2b"),
            ),
        )
        assert report.result.pathways_count == 7
        row = db.scalar(
            select(MoatIntelligenceRun).where(MoatIntelligenceRun.id == report.run_id)
        )
        assert row is not None
        assert row.pathways_count == 7
        assert row.moat_strength_score > 0

        loaded = MoatDataModelService(db).get_run(
            run_id=report.run_id, organisation_id=org.id
        )
        assert loaded is not None
        assert loaded.result.pathways_count == 7
        assert len(loaded.result.pathways) == 7
    finally:
        db.close()
