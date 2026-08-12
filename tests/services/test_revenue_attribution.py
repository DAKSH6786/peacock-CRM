"""Peacock Revenue Attribution — funnel chain with uncertainty, no causal overclaim."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from db_models import Organisation, Website, Workspace
from db_models.base import new_uuid
from db_models.revenue_attribution import RevenueAttributionAnalysis
from revenue_attribution import (
    CAUSALITY_WARNING,
    FUNNEL_STAGES,
    AttributionSpec,
    SourceAvailability,
    StageObservation,
    attribute_revenue,
)
from revenue_attribution.models import RevenueAttributionSpec
from revenue_attribution.service import RevenueAttributionService


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


def test_funnel_path_complete() -> None:
    assert FUNNEL_STAGES == (
        "recommendation",
        "content",
        "visibility",
        "traffic",
        "lead",
        "conversion",
        "revenue",
    )
    result = attribute_revenue(AttributionSpec(client_brand="Acme"))
    assert result.funnel_path == [
        "Recommendation",
        "Content",
        "Visibility",
        "Traffic",
        "Lead",
        "Conversion",
        "Revenue",
    ]
    assert len(result.stages) == 7
    assert len(result.links) == 6


def test_attribution_includes_uncertainty_and_warning() -> None:
    result = attribute_revenue(
        AttributionSpec(
            client_brand="Acme",
            sources=SourceAvailability(
                ga4=True,
                crm=True,
                search_console=True,
                conversions=True,
                transactions=True,
                leads=True,
            ),
            observations=[
                StageObservation("traffic", 500, 900, "sessions", "ga4", 80),
                StageObservation("lead", 10, 25, "count", "crm", 75),
                StageObservation("revenue", 40_000, 95_000, "INR", "transactions", 70),
            ],
        )
    )
    assert result.attributed_revenue_high >= result.attributed_revenue_low
    assert result.overall_uncertainty > 0
    assert result.causality_warning == CAUSALITY_WARNING
    assert "causality" in result.causality_warning.lower()
    assert result.overall_causality_level != "causal_evidence"
    assert all(s.value_high >= s.value_low for s in result.stages)
    assert all(s.uncertainty > 0 for s in result.stages)
    assert all(l.causality_level != "causal_evidence" for l in result.links)
    assert "ga4" in result.sources_available
    assert "pipeline" in result.sources_missing


def test_missing_sources_raise_uncertainty() -> None:
    rich = attribute_revenue(
        AttributionSpec(
            client_brand="Acme",
            sources=SourceAvailability(
                ga4=True,
                crm=True,
                search_console=True,
                conversions=True,
                pipeline=True,
                transactions=True,
                leads=True,
            ),
        )
    )
    poor = attribute_revenue(
        AttributionSpec(
            client_brand="Acme",
            sources=SourceAvailability(peacock_internal=True),
        )
    )
    assert poor.data_completeness < rich.data_completeness
    assert poor.overall_uncertainty >= rich.overall_uncertainty * 0.9
    assert poor.overall_causality_level in (
        "insufficient_data",
        "correlation",
        "likely_contribution",
    )


@pytest.mark.skipif(not _can_connect(), reason="PostgreSQL not available")
def test_persist_revenue_attribution() -> None:
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
            name=f"ra-{suffix}",
            slug=f"ra-{suffix}",
        )
        db.add(workspace)
        db.flush()
        website = Website(
            id=new_uuid(),
            organisation_id=org.id,
            workspace_id=workspace.id,
            name=f"Site {suffix}",
            primary_domain=f"ra-{suffix}.com",
            root_url=f"https://ra-{suffix}.com",
        )
        db.add(website)
        db.commit()

        report = RevenueAttributionService(db).analyse(
            organisation_id=org.id,
            workspace_id=workspace.id,
            created_by=None,
            spec=RevenueAttributionSpec(
                website_id=website.id,
                name=f"RA {suffix}",
                attribution=AttributionSpec(
                    client_brand="Acme",
                    sources=SourceAvailability(ga4=True, crm=True, transactions=True),
                ),
            ),
        )
        assert report.analysis_id
        assert report.result.overall_causality_level != "causal_evidence"
        row = db.scalar(
            select(RevenueAttributionAnalysis).where(
                RevenueAttributionAnalysis.id == report.analysis_id
            )
        )
        assert row is not None
        assert row.attributed_revenue_high >= row.attributed_revenue_low
        assert "CAUSALITY" in row.causality_warning
    finally:
        db.close()
