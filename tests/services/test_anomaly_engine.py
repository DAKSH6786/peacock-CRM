"""Peacock Anomaly Engine — detect + rank by probable business impact."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from anomaly_engine import (
    ANOMALY_TYPES,
    AnomalyScanSpec,
    MetricObservation,
    scan_anomalies,
)
from anomaly_engine.models import AnomalyEngineSpec
from anomaly_engine.service import AnomalyEngineService
from db_models import Organisation, Website, Workspace
from db_models.anomaly_engine import AnomalyScan
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


def test_all_anomaly_types_supported() -> None:
    assert set(ANOMALY_TYPES) == {
        "sudden_ranking_loss",
        "ai_visibility_collapse",
        "citation_disappearance",
        "negative_sentiment_spike",
        "competitor_acceleration",
        "crawler_issue",
        "indexation_loss",
        "traffic_anomaly",
        "backlink_loss",
    }


def test_demo_scan_detects_and_ranks_by_impact() -> None:
    end = datetime(2026, 8, 13, tzinfo=UTC)
    result = scan_anomalies(
        AnomalyScanSpec(
            client_brand="Acme",
            window_start=end - timedelta(days=25),
            window_end=end,
        )
    )
    assert result.anomalies_detected >= 5
    types_found = {a.anomaly_type for a in result.anomalies}
    # Demo should cover most/all types
    assert types_found <= set(ANOMALY_TYPES)
    assert len(types_found) >= 5
    ranks = [a.impact_rank for a in result.anomalies]
    assert ranks == sorted(ranks)
    scores = [a.impact_score for a in result.anomalies]
    assert scores == sorted(scores, reverse=True)
    assert result.top_anomaly_type == result.anomalies[0].anomaly_type
    assert result.top_impact_score == result.anomalies[0].impact_score
    assert all(a.severity in ("low", "medium", "high", "critical") for a in result.anomalies)
    assert all(a.recommended_response for a in result.anomalies)


def test_higher_revenue_exposure_raises_impact() -> None:
    end = datetime(2026, 8, 13, tzinfo=UTC)
    start = end - timedelta(days=14)
    pts = [(start + timedelta(days=i), v) for i, v in enumerate(
        [70, 71, 69, 70, 72, 71, 70, 55, 50, 48, 47, 46, 45, 44]
    )]
    low = scan_anomalies(
        AnomalyScanSpec(
            client_brand="Acme",
            window_start=start,
            window_end=end,
            observations=[
                MetricObservation(
                    "organic_rank_score",
                    "sudden_ranking_loss",
                    pts,
                    revenue_exposure=1_000,
                )
            ],
        )
    )
    high = scan_anomalies(
        AnomalyScanSpec(
            client_brand="Acme",
            window_start=start,
            window_end=end,
            observations=[
                MetricObservation(
                    "organic_rank_score",
                    "sudden_ranking_loss",
                    pts,
                    revenue_exposure=1_000_000,
                )
            ],
        )
    )
    assert low.anomalies and high.anomalies
    assert high.anomalies[0].impact_score >= low.anomalies[0].impact_score


@pytest.mark.skipif(not _can_connect(), reason="PostgreSQL not available")
def test_persist_anomaly_scan() -> None:
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
            name=f"ae-{suffix}",
            slug=f"ae-{suffix}",
        )
        db.add(workspace)
        db.flush()
        website = Website(
            id=new_uuid(),
            organisation_id=org.id,
            workspace_id=workspace.id,
            name=f"Site {suffix}",
            primary_domain=f"ae-{suffix}.com",
            root_url=f"https://ae-{suffix}.com",
        )
        db.add(website)
        db.commit()

        end = datetime(2026, 8, 13, tzinfo=UTC)
        report = AnomalyEngineService(db).scan(
            organisation_id=org.id,
            workspace_id=workspace.id,
            created_by=None,
            spec=AnomalyEngineSpec(
                website_id=website.id,
                name=f"Scan {suffix}",
                scan=AnomalyScanSpec(
                    client_brand="Acme",
                    window_start=end - timedelta(days=25),
                    window_end=end,
                ),
            ),
        )
        assert report.scan_id
        assert report.result.anomalies_detected >= 1
        row = db.scalar(select(AnomalyScan).where(AnomalyScan.id == report.scan_id))
        assert row is not None
        assert row.top_impact_score is not None
    finally:
        db.close()
