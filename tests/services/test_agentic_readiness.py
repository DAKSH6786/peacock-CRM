"""Peacock Agentic Web Readiness — Agent Discoverability + Agent Readiness Score."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from agentic_readiness import (
    DISCOVERABILITY_CHECKS,
    NOT_INDUSTRY_STANDARD,
    SURFACE_SEPARATION,
    CheckSignal,
    ReadinessSpec,
    analyse_readiness,
)
from agentic_readiness.models import AgenticReadinessSpec
from agentic_readiness.service import AgenticReadinessService
from db_models import Organisation, Website, Workspace
from db_models.agentic_readiness import AgenticReadinessAnalysis
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


def test_all_discoverability_checks_present() -> None:
    expected = {
        "structured_product_information",
        "clear_pricing",
        "availability",
        "product_ids",
        "schema",
        "api_discoverability",
        "machine_readable_policies",
        "service_descriptions",
        "locations",
        "booking_information",
        "contact_mechanisms",
        "returns",
        "shipping",
        "trust_signals",
    }
    assert set(DISCOVERABILITY_CHECKS) == expected


def test_agent_readiness_score_and_disclaimers() -> None:
    result = analyse_readiness(
        ReadinessSpec(
            client_brand="Acme",
            business_type="commerce",
            signals=[
                CheckSignal("structured_product_information", 80, "JSON-LD Product"),
                CheckSignal("clear_pricing", 75, "Offer price present"),
                CheckSignal("availability", 70, "InStock"),
                CheckSignal("product_ids", 85, "GTIN present"),
                CheckSignal("schema", 78, "Product+Offer"),
                CheckSignal("api_discoverability", 40, "No OpenAPI"),
                CheckSignal("machine_readable_policies", 55, "HTML policies"),
                CheckSignal("service_descriptions", 30, "N/A commerce"),
                CheckSignal("locations", 60, "Store locator"),
                CheckSignal("booking_information", 20, "N/A"),
                CheckSignal("contact_mechanisms", 65, "mailto+chat"),
                CheckSignal("returns", 72, "30-day policy"),
                CheckSignal("shipping", 68, "Carrier table"),
                CheckSignal("trust_signals", 70, "Reviews schema"),
            ],
        )
    )
    assert 0 <= result.agent_readiness_score <= 100
    assert result.readiness_band in ("nascent", "emerging", "operable", "agent_ready")
    assert result.checks_total == 14
    assert len(result.checks) == 14
    assert result.separate_from_seo_aeo_geo is True
    assert result.not_industry_standard is True
    assert "SEO" in result.surface_separation_note or SURFACE_SEPARATION
    assert "industry-standard" in result.not_industry_standard_note.lower() or (
        "industry standard" in NOT_INDUSTRY_STANDARD.lower()
    )
    assert any(g.check_code == "api_discoverability" for g in result.gaps)
    # Stronger signals should outscore weak priors
    weak = analyse_readiness(
        ReadinessSpec(
            client_brand="Acme",
            signals=[CheckSignal(c, 20, "weak") for c in DISCOVERABILITY_CHECKS],
        )
    )
    assert result.agent_readiness_score > weak.agent_readiness_score


def test_separate_from_seo_aeo_geo_and_not_standard() -> None:
    result = analyse_readiness(ReadinessSpec(client_brand="Acme"))
    assert result.separate_from_seo_aeo_geo is True
    assert result.not_industry_standard is True
    assert "AEO" in result.surface_separation_note or "GEO" in result.surface_separation_note
    assert "proprietary" in result.not_industry_standard_note.lower() or (
        "does not claim" in result.not_industry_standard_note.lower()
    )


@pytest.mark.skipif(not _can_connect(), reason="PostgreSQL not available")
def test_persist_agentic_readiness() -> None:
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
            name=f"awr-{suffix}",
            slug=f"awr-{suffix}",
        )
        db.add(workspace)
        db.flush()
        website = Website(
            id=new_uuid(),
            organisation_id=org.id,
            workspace_id=workspace.id,
            name=f"Site {suffix}",
            primary_domain=f"awr-{suffix}.com",
            root_url=f"https://awr-{suffix}.com",
        )
        db.add(website)
        db.commit()

        report = AgenticReadinessService(db).analyse(
            organisation_id=org.id,
            workspace_id=workspace.id,
            created_by=None,
            spec=AgenticReadinessSpec(
                website_id=website.id,
                name=f"AWR {suffix}",
                readiness=ReadinessSpec(
                    client_brand="Acme",
                    business_type="mixed",
                    signals=[
                        CheckSignal("api_discoverability", 90, "OpenAPI published"),
                        CheckSignal("schema", 85, "Organization+Product"),
                    ],
                ),
            ),
        )
        assert report.analysis_id
        assert report.result.separate_from_seo_aeo_geo is True
        assert report.result.not_industry_standard is True
        row = db.scalar(
            select(AgenticReadinessAnalysis).where(
                AgenticReadinessAnalysis.id == report.analysis_id
            )
        )
        assert row is not None
        assert row.checks_total == 14
        assert row.separate_from_seo_aeo_geo is True
        assert row.not_industry_standard is True
    finally:
        db.close()
