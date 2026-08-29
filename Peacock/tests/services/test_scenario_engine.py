"""Peacock Scenario Engine — counterfactual ranges (not fake precision)."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from db_models import Organisation, Website, Workspace
from db_models.base import new_uuid
from db_models.scenario_engine import (
    STRATEGY_CODES,
    STRATEGY_LABELS,
    ScenarioAnalysis,
    SeScenario,
)
from scenario_engine import (
    ContextSignals,
    ScenarioEngineService,
    ScenarioEngineSpec,
    ScenarioSpec,
    run_scenario_analysis,
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


def test_all_strategies_catalogued() -> None:
    assert len(STRATEGY_CODES) == 10
    assert set(STRATEGY_LABELS) == set(STRATEGY_CODES)
    assert STRATEGY_LABELS["do_nothing"] == "Do nothing"
    assert STRATEGY_LABELS["peacock_recommended"] == "Peacock recommended strategy"
    assert "SEO + AEO + GEO" in STRATEGY_LABELS.values()


def test_example_ranges_and_metadata() -> None:
    result = run_scenario_analysis(
        ScenarioSpec(client_brand="Acme", horizon_days=90, context=ContextSignals())
    )
    by_code = {s.strategy_code: s for s in result.scenarios}
    assert set(by_code) == set(STRATEGY_CODES)

    assert by_code["do_nothing"].range_low_pct == 0.0
    assert by_code["do_nothing"].range_high_pct == 4.0
    assert by_code["publish_more_content"].range_low_pct == 7.0
    assert by_code["publish_more_content"].range_high_pct == 18.0
    assert by_code["build_third_party_authority"].range_low_pct == 9.0
    assert by_code["build_third_party_authority"].range_high_pct == 22.0
    assert by_code["peacock_recommended"].range_low_pct == 14.0
    assert by_code["peacock_recommended"].range_high_pct == 31.0

    assert result.ranges_not_fake_precision is True
    assert "ranges" in result.ranges_disclaimer.lower() or "fake" in result.ranges_disclaimer.lower()
    assert result.overall_confidence > 0
    assert result.overall_data_quality > 0
    assert result.overall_uncertainty > 0
    assert len(result.assumptions) >= 1
    assert result.assumptions_summary
    assert result.recommended_strategy_code == "peacock_recommended"

    for s in result.scenarios:
        assert s.range_high_pct > s.range_low_pct  # never a point
        assert 0 <= s.confidence <= 100
        assert 0 <= s.data_quality <= 100
        assert 0 <= s.uncertainty <= 100
        assert s.display_band  # e.g. "+14% to +31%"
        assert "to" in s.display_band


def test_weak_data_widens_bands() -> None:
    strong = run_scenario_analysis(
        ScenarioSpec(
            client_brand="Acme",
            context=ContextSignals(data_quality=90.0, competitor_pressure=40.0),
        )
    )
    weak = run_scenario_analysis(
        ScenarioSpec(
            client_brand="Acme",
            context=ContextSignals(data_quality=30.0, competitor_pressure=80.0),
        )
    )
    s_strong = next(s for s in strong.scenarios if s.strategy_code == "peacock_recommended")
    s_weak = next(s for s in weak.scenarios if s.strategy_code == "peacock_recommended")
    assert (s_weak.range_high_pct - s_weak.range_low_pct) >= (
        s_strong.range_high_pct - s_strong.range_low_pct
    )
    assert s_weak.uncertainty >= s_strong.uncertainty
    assert weak.overall_data_quality < strong.overall_data_quality


@pytest.mark.skipif(not _can_connect(), reason="PostgreSQL not available")
def test_persist_scenario_analysis() -> None:
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
            name=f"se-{suffix}",
            slug=f"se-{suffix}",
        )
        db.add(workspace)
        db.flush()
        website = Website(
            id=new_uuid(),
            organisation_id=org.id,
            workspace_id=workspace.id,
            name=f"Site {suffix}",
            primary_domain=f"se-{suffix}.com",
            root_url=f"https://se-{suffix}.com",
        )
        db.add(website)
        db.commit()

        report = ScenarioEngineService(db).analyse(
            organisation_id=org.id,
            workspace_id=workspace.id,
            created_by=None,
            spec=ScenarioEngineSpec(
                website_id=website.id,
                name=f"90d visibility {suffix}",
                scenario=ScenarioSpec(client_brand="Acme"),
            ),
        )
        assert report.analysis_id
        assert report.result.ranges_not_fake_precision is True
        assert len(report.result.scenarios) == 10

        row = db.scalar(
            select(ScenarioAnalysis).where(ScenarioAnalysis.id == report.analysis_id)
        )
        assert row is not None
        assert row.ranges_not_fake_precision is True
        scenarios = list(
            db.scalars(
                select(SeScenario).where(SeScenario.analysis_id == report.analysis_id)
            ).all()
        )
        assert len(scenarios) == 10
        peacock = next(s for s in scenarios if s.is_peacock_recommended)
        assert peacock.range_low_pct == 14.0
        assert peacock.range_high_pct == 31.0

        loaded = ScenarioEngineService(db).get_analysis(
            analysis_id=report.analysis_id, organisation_id=org.id
        )
        assert loaded is not None
        assert loaded.result.recommended_strategy_code == "peacock_recommended"
    finally:
        db.close()
