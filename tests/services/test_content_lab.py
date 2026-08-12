"""Peacock Content Lab — opportunities, info gain, moat, citability."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from content_lab import (
    CITABILITY_DISCLAIMER,
    MOAT_FORMAT_PRIORS,
    OPPORTUNITY_DIMENSIONS,
    ContentLabService,
    ProposalInput,
    evaluate_proposals,
)
from content_lab.models import ContentLabSpec
from db_models import Organisation, Website, Workspace
from db_models.base import new_uuid
from db_models.content_lab import ClContentProposal


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


def test_opportunity_dimensions_cover_spec() -> None:
    required = {
        "seo_opportunity",
        "aeo_opportunity",
        "geo_opportunity",
        "ai_citation_opportunity",
        "business_value",
        "audience_relevance",
        "competitor_gap",
        "information_gain",
        "originality_opportunity",
        "topical_authority_impact",
        "conversion_potential",
        "backlink_potential",
        "entity_impact",
        "effort",
        "time_sensitivity",
    }
    assert required == set(OPPORTUNITY_DIMENSIONS)


def test_moat_priors_match_examples() -> None:
    assert MOAT_FORMAT_PRIORS["generic_listicle"] == 18
    assert MOAT_FORMAT_PRIORS["expert_interview"] == 51
    assert MOAT_FORMAT_PRIORS["original_dataset"] == 86
    assert MOAT_FORMAT_PRIORS["proprietary_benchmark_study"] == 94


def test_listicle_vs_benchmark_ranking() -> None:
    scores = evaluate_proposals(
        [
            ProposalInput(
                title="Top 10 CRM Tips",
                slug="top-10-crm-tips",
                content_format="generic_listicle",
                angle="tips and tricks commodity advice",
            ),
            ProposalInput(
                title="2026 CRM Benchmark Study",
                slug="crm-benchmark-2026",
                content_format="proprietary_benchmark_study",
                angle="our survey of n=1200 with fresh statistics and new comparison",
                citability_signals={
                    "specificity": 0.85,
                    "evidence": 0.9,
                    "tables": 0.8,
                    "original_information": 0.9,
                    "comparisons": 0.85,
                    "direct_answers": 0.7,
                },
            ),
            ProposalInput(
                title="Expert Interview: CRO Playbook",
                slug="expert-interview-cro",
                content_format="expert_interview",
                angle="interview with expert opinion and first-party insight",
            ),
            ProposalInput(
                title="Open CRM Dataset",
                slug="open-crm-dataset",
                content_format="original_dataset",
                angle="original data release sample of 50k rows",
            ),
        ]
    )
    by_slug = {s.slug: s for s in scores}
    assert by_slug["top-10-crm-tips"].content_moat_score < 30
    assert abs(by_slug["top-10-crm-tips"].content_moat_score - 18) < 12
    assert by_slug["expert-interview-cro"].content_moat_score > 40
    assert by_slug["open-crm-dataset"].content_moat_score > 75
    assert by_slug["crm-benchmark-2026"].content_moat_score > 85

    assert (
        by_slug["crm-benchmark-2026"].information_gain_score
        > by_slug["top-10-crm-tips"].information_gain_score
    )
    assert (
        by_slug["crm-benchmark-2026"].lab_priority_score
        > by_slug["top-10-crm-tips"].lab_priority_score
    )


def test_information_gain_penalties_and_rewards() -> None:
    weak = evaluate_proposals(
        [
            ProposalInput(
                title="What is CRM",
                slug="what-is-crm",
                content_format="article",
                angle="definition of CRM and best practices only",
                info_gain_penalties={
                    "common_definitions": 0.8,
                    "commodity_advice": 0.7,
                    "generic_duplication": 0.6,
                },
            )
        ]
    )[0]
    strong = evaluate_proposals(
        [
            ProposalInput(
                title="Our CRM Experiment",
                slug="crm-experiment",
                content_format="article",
                angle="we tested an original experiment with unique framework",
                info_gain_rewards={
                    "original_experiment": 0.9,
                    "unique_framework": 0.8,
                    "first_party_insight": 0.7,
                },
            )
        ]
    )[0]
    assert strong.information_gain_score > weak.information_gain_score
    assert any(s.polarity == "penalty" for s in weak.info_gain_signals)
    assert any(s.polarity == "reward" for s in strong.info_gain_signals)


def test_citability_is_proprietary_estimate_not_guarantee() -> None:
    score = evaluate_proposals(
        [
            ProposalInput(
                title="Citability page",
                slug="citability",
                content_format="article",
                citability_signals={"specificity": 0.8, "evidence": 0.7, "direct_answers": 0.75},
            )
        ]
    )[0]
    assert score.citability_is_proprietary_estimate is True
    assert "proprietary estimate" in score.citability_disclaimer.lower()
    assert "not a guaranteed" in score.citability_disclaimer.lower()
    assert CITABILITY_DISCLAIMER[:40] in score.citability_disclaimer
    assert 0 <= score.generative_citability_score <= 100
    assert len(score.citability_components) == 11


@pytest.mark.skipif(not _can_connect(), reason="PostgreSQL not available")
def test_content_lab_persists() -> None:
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
            name=f"cl-{suffix}",
            slug=f"cl-{suffix}",
        )
        db.add(workspace)
        db.flush()
        website = Website(
            id=new_uuid(),
            organisation_id=org.id,
            workspace_id=workspace.id,
            name=f"Site {suffix}",
            primary_domain=f"cl-{suffix}.com",
            root_url=f"https://cl-{suffix}.com",
        )
        db.add(website)
        db.commit()

        report = ContentLabService(db).analyse(
            organisation_id=org.id,
            workspace_id=workspace.id,
            spec=ContentLabSpec(
                website_id=website.id,
                name=f"Lab {suffix}",
                client_brand="Client",
                proposals=[
                    ProposalInput(
                        title="Generic tips",
                        slug=f"tips-{suffix}",
                        content_format="generic_listicle",
                    ),
                    ProposalInput(
                        title="Benchmark",
                        slug=f"bench-{suffix}",
                        content_format="proprietary_benchmark_study",
                        angle="our survey n=800 fresh statistics",
                    ),
                ],
            ),
        )
        assert report.citability_is_proprietary_estimate is True
        assert report.example_moat
        rows = list(
            db.scalars(
                select(ClContentProposal).where(
                    ClContentProposal.analysis_id == report.analysis_id
                )
            ).all()
        )
        assert len(rows) == 2
    finally:
        db.close()
