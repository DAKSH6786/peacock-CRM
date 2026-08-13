"""Peacock Proprietary Metrics — formulas documented + proprietary disclaimer."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from db_models import Organisation, Website, Workspace
from db_models.base import new_uuid
from db_models.proprietary_metrics import (
    METRIC_KEYS,
    NOT_OFFICIAL_PLATFORMS,
    PROPRIETARY_DISCLAIMER,
    ProprietaryMetricScorecard,
)
from proprietary_metrics import (
    FORMULA_DOCS,
    ProprietaryMetricsSpec,
    catalog,
    score_proprietary_metrics,
)
from proprietary_metrics.models import ProprietaryMetricsCreateSpec
from proprietary_metrics.service import ProprietaryMetricsService


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


def test_all_metrics_have_documented_formulas() -> None:
    assert set(FORMULA_DOCS) == set(METRIC_KEYS)
    c = catalog()
    assert len(c["formulas"]) == len(METRIC_KEYS)
    for f in c["formulas"]:
        assert f["formula_id"]
        assert f["formula_text"]
        assert "NOT" in f["proprietary_note"] or "not" in f["proprietary_note"].lower()


def test_disclaimer_rejects_official_platform_representation() -> None:
    assert "Google" in PROPRIETARY_DISCLAIMER
    assert "OpenAI" in PROPRIETARY_DISCLAIMER
    assert "Anthropic" in PROPRIETARY_DISCLAIMER
    assert "Perplexity" in PROPRIETARY_DISCLAIMER
    for name in ("Google", "OpenAI", "Anthropic", "Perplexity"):
        assert name in NOT_OFFICIAL_PLATFORMS
    c = catalog()
    assert "Never represent" in c["important"]


def test_scorecard_includes_all_metrics_with_formulas() -> None:
    result = score_proprietary_metrics(ProprietaryMetricsSpec(client_brand="Acme"))
    assert result.metrics_scored == len(METRIC_KEYS)
    keys = [m.metric_key for m in result.metrics]
    assert keys == list(METRIC_KEYS)
    for m in result.metrics:
        assert m.formula_id
        assert m.formula_text
        assert m.components
        assert "Google" in m.proprietary_note or "NOT" in m.proprietary_note
    pvi = next(m for m in result.metrics if m.metric_key == "peacock_visibility_index")
    assert 0 <= pvi.score <= 100
    oc = next(m for m in result.metrics if m.metric_key == "opportunity_confidence")
    assert 0 <= oc.score <= 1
    assert "Google" in result.proprietary_disclaimer


@pytest.mark.skipif(not _can_connect(), reason="PostgreSQL not available")
def test_persist_scorecard() -> None:
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
            name=f"pm-{suffix}",
            slug=f"pm-{suffix}",
        )
        db.add(workspace)
        db.flush()
        website = Website(
            id=new_uuid(),
            organisation_id=org.id,
            workspace_id=workspace.id,
            name=f"Site {suffix}",
            primary_domain=f"pm-{suffix}.com",
            root_url=f"https://pm-{suffix}.com",
        )
        db.add(website)
        db.commit()

        report = ProprietaryMetricsService(db).create_scorecard(
            organisation_id=org.id,
            workspace_id=workspace.id,
            created_by=None,
            spec=ProprietaryMetricsCreateSpec(
                website_id=website.id,
                name=f"PM {suffix}",
                scorecard=ProprietaryMetricsSpec(client_brand="Acme"),
            ),
        )
        assert report.scorecard_id
        row = db.scalar(
            select(ProprietaryMetricScorecard).where(
                ProprietaryMetricScorecard.id == report.scorecard_id
            )
        )
        assert row is not None
        assert row.metrics_scored == len(METRIC_KEYS)
        assert "OpenAI" in row.proprietary_disclaimer
    finally:
        db.close()
