"""Peacock Temporal Intelligence — timeline queries + noise-aware change points."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from db_models import Organisation, Website, Workspace
from db_models.base import new_uuid
from db_models.temporal_intelligence import TemporalTimeline
from temporal_intelligence import (
    EVENT_KINDS,
    NOISE_GUARDRAIL,
    MetricSeries,
    MetricSeriesPoint,
    TimelineEventInput,
    TimelineSpec,
    analyse_timeline,
    detect_change_points,
)
from temporal_intelligence.models import TemporalIntelligenceSpec
from temporal_intelligence.service import TemporalIntelligenceService


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


def test_event_kinds_complete() -> None:
    assert set(EVENT_KINDS) == {
        "search_change",
        "ai_answer_change",
        "citation_change",
        "competitor_change",
        "entity_change",
        "sentiment_change",
        "content_update",
        "algorithm_event",
        "peacock_action",
    }


def test_timeline_queries_and_noise_guardrail() -> None:
    end = datetime(2026, 8, 12, tzinfo=UTC)
    start = end - timedelta(days=35)
    result = analyse_timeline(
        TimelineSpec(
            client_brand="Acme",
            window_start=start,
            window_end=end,
            questions=[
                "What changed?",
                "Why did visibility drop?",
                "What happened before citations increased?",
                "Which action preceded our ranking increase?",
            ],
        )
    )
    assert result.events_count >= 1
    assert all(k in EVENT_KINDS for k in {e.event_kind for e in result.events})
    intents = {q.intent for q in result.query_answers}
    assert "what_changed" in intents
    assert "why_visibility_drop" in intents
    assert "before_citations_increased" in intents
    assert "action_preceded_ranking_increase" in intents
    assert result.noise_guardrail == NOISE_GUARDRAIL
    assert "noise" in result.noise_guardrail.lower()
    assert result.alerts_suppressed >= 0
    # Sharp visibility drop should produce at least one alert; flat noise suppressed
    alerts = [c for c in result.change_points if c.is_alert]
    noise = [c for c in result.change_points if c.suppressed_as_noise]
    assert any(c.metric_key == "visibility_index" for c in alerts)
    assert any(c.metric_key == "noise_metric" for c in noise)
    assert all(not c.is_alert for c in noise)


def test_change_point_does_not_alert_on_flat_noise() -> None:
    start = datetime(2026, 7, 1, tzinfo=UTC)
    points = [
        MetricSeriesPoint(start + timedelta(days=d), 50.0 + 0.2 * (d % 3))
        for d in range(25)
    ]
    cps = detect_change_points(MetricSeries("flat", points))
    assert cps  # candidates exist
    assert all(c.suppressed_as_noise for c in cps)
    assert not any(c.is_alert for c in cps)


def test_change_point_alerts_on_step_shift() -> None:
    start = datetime(2026, 7, 1, tzinfo=UTC)
    points = [
        MetricSeriesPoint(start + timedelta(days=d), 60.0 if d < 15 else 40.0)
        for d in range(25)
    ]
    cps = detect_change_points(MetricSeries("step", points))
    alerts = [c for c in cps if c.is_alert]
    assert alerts
    assert any(c.effect_size < 0 for c in alerts)


@pytest.mark.skipif(not _can_connect(), reason="PostgreSQL not available")
def test_persist_temporal_timeline() -> None:
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
            name=f"ti-{suffix}",
            slug=f"ti-{suffix}",
        )
        db.add(workspace)
        db.flush()
        website = Website(
            id=new_uuid(),
            organisation_id=org.id,
            workspace_id=workspace.id,
            name=f"Site {suffix}",
            primary_domain=f"ti-{suffix}.com",
            root_url=f"https://ti-{suffix}.com",
        )
        db.add(website)
        db.commit()

        end = datetime(2026, 8, 12, tzinfo=UTC)
        report = TemporalIntelligenceService(db).analyse(
            organisation_id=org.id,
            workspace_id=workspace.id,
            created_by=None,
            spec=TemporalIntelligenceSpec(
                website_id=website.id,
                name=f"Timeline {suffix}",
                timeline=TimelineSpec(
                    client_brand="Acme",
                    window_start=end - timedelta(days=35),
                    window_end=end,
                    events=[
                        TimelineEventInput(
                            "peacock_action",
                            end - timedelta(days=10),
                            "Schema action",
                            "Executed schema suggestion",
                            magnitude=2.0,
                            direction="up",
                        )
                    ],
                ),
            ),
        )
        assert report.timeline_id
        assert report.result.noise_guardrail
        row = db.scalar(
            select(TemporalTimeline).where(TemporalTimeline.id == report.timeline_id)
        )
        assert row is not None
        assert row.events_count >= 1
    finally:
        db.close()
