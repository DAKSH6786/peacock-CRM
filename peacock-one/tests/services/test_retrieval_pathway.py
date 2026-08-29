"""Retrieval Pathway Intelligence — inferred forensics with uncertainty."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from db_models import Organisation, Website, Workspace
from db_models.base import new_uuid
from db_models.retrieval_pathway import (
    FORENSIC_CAUSES,
    METHODOLOGY_DISCLAIMER,
    RpiBottleneckDiagnosis,
    RpiCauseClassification,
)
from retrieval_pathway import (
    ObservedEvidenceInput,
    RetrievalPathwayService,
    RetrievalPathwaySpec,
    run_forensics,
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


def test_all_forensic_causes_classified() -> None:
    report = run_forensics(ObservedEvidenceInput(topical_relevance=0.8))
    assert {c.cause_code for c in report.causes} == set(FORENSIC_CAUSES)
    assert all(c.uncertainty in {"low", "moderate", "high", "very_high"} for c in report.causes)
    assert report.proprietary_ranking_access_claimed is False
    assert "proprietary" in report.disclaimer.lower()


def test_high_retrieval_low_selection_bottleneck_example() -> None:
    """Canonical example: relevant page, weak citation selection."""
    evidence = ObservedEvidenceInput(
        page_reachable=True,
        http_status=200,
        robots_blocked=False,
        noindex=False,
        topical_relevance=0.88,
        entity_relationship_strength=0.7,
        competitor_page_strength=0.85,
        source_freshness_days=60,
        extractability=0.8,
        supporting_evidence_strength=0.45,
        third_party_corroboration=0.2,
        content_appeared_retrieved=True,
        brand_mentioned=True,
        page_cited=False,
        citation_rate=0.05,
        mention_rate=0.4,
        observation_sample_size=20,
        evidence_confidence=0.7,
    )
    report = run_forensics(evidence)
    assert report.retrieval_likelihood_band in {"HIGH", "VERY_HIGH"}
    assert report.selection_likelihood_band in {"VERY_LOW", "LOW", "MEDIUM"}
    assert report.estimated_retrieval_likelihood > report.estimated_selection_likelihood
    assert report.bottleneck.headline == "LIKELY VISIBILITY BOTTLENECK"
    assert report.bottleneck.retrieval_probability_band in {"HIGH", "VERY_HIGH"}
    assert report.bottleneck.citation_selection_band in {"VERY_LOW", "LOW", "MEDIUM"}
    assert "citation-quality gap" in report.bottleneck.recommended_investigation
    assert "inferred" in report.bottleneck.interpretation.lower() or "observed" in report.bottleneck.interpretation.lower()
    assert METHODOLOGY_DISCLAIMER[:40] in report.disclaimer

    # content_retrieved_but_not_selected or competitor_page_stronger should rank highly
    top_codes = {c.cause_code for c in report.causes[:3]}
    assert top_codes & {
        "content_retrieved_but_not_selected",
        "competitor_page_stronger",
        "brand_mentioned_but_not_cited",
        "lack_of_third_party_corroboration",
    }


def test_unavailable_page_retrieval_bottleneck() -> None:
    evidence = ObservedEvidenceInput(
        page_reachable=False,
        http_status=404,
        topical_relevance=0.7,
        citation_rate=0.0,
        page_cited=False,
        observation_sample_size=8,
        evidence_confidence=0.8,
    )
    report = run_forensics(evidence)
    assert report.estimated_retrieval_likelihood < 0.45
    primary = next(c for c in report.causes if c.is_primary)
    assert primary.cause_code in {
        "page_unavailable",
        "content_not_retrieved",
        "crawl_restricted",
    }
    assert "RETRIEVAL" in report.bottleneck.headline or report.bottleneck.bottleneck_stage == "retrieval"


def test_terminology_avoids_vendor_ranking_claims() -> None:
    report = run_forensics(
        ObservedEvidenceInput(topical_relevance=0.5, evidence_confidence=0.4)
    )
    blob = (
        report.disclaimer
        + report.bottleneck.interpretation
        + " ".join(c.rationale for c in report.causes)
    ).lower()
    assert "proprietary" in report.disclaimer.lower()
    assert "does not have access" in report.disclaimer.lower()
    for banned in ("we scraped openai's ranker", "internal ranking weight leaked"):
        assert banned not in blob
    assert report.methodology == "inferred_retrieval_pathway"


@pytest.mark.skipif(not _can_connect(), reason="PostgreSQL not available")
def test_retrieval_pathway_persists() -> None:
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
            name=f"rpi-{suffix}",
            slug=f"rpi-{suffix}",
        )
        db.add(workspace)
        db.flush()
        website = Website(
            id=new_uuid(),
            organisation_id=org.id,
            workspace_id=workspace.id,
            name=f"Site {suffix}",
            primary_domain=f"rpi-{suffix}.com",
            root_url=f"https://rpi-{suffix}.com",
        )
        db.add(website)
        db.commit()

        report = RetrievalPathwayService(db).analyse(
            organisation_id=org.id,
            workspace_id=workspace.id,
            spec=RetrievalPathwaySpec(
                website_id=website.id,
                name=f"CRM forensics {suffix}",
                query_cluster="Enterprise CRM",
                client_brand="Client",
                target_url=f"https://rpi-{suffix}.com/crm",
                evidence=ObservedEvidenceInput(
                    page_reachable=True,
                    http_status=200,
                    topical_relevance=0.9,
                    competitor_page_strength=0.8,
                    content_appeared_retrieved=True,
                    page_cited=False,
                    citation_rate=0.04,
                    brand_mentioned=True,
                    mention_rate=0.35,
                    observation_sample_size=15,
                    evidence_confidence=0.75,
                ),
            ),
        )
        assert report.example_display["headline"] == "LIKELY VISIBILITY BOTTLENECK"
        assert report.proprietary_ranking_access_claimed is False

        causes = list(
            db.scalars(
                select(RpiCauseClassification).where(
                    RpiCauseClassification.analysis_id == report.analysis_id
                )
            ).all()
        )
        assert len(causes) == len(FORENSIC_CAUSES)
        bottleneck = db.scalar(
            select(RpiBottleneckDiagnosis).where(
                RpiBottleneckDiagnosis.analysis_id == report.analysis_id
            )
        )
        assert bottleneck is not None
        assert bottleneck.disclaimer.startswith("Peacock does not have access")
    finally:
        db.close()
