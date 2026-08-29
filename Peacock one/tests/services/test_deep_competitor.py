"""Deep Competitor Intelligence — discovery, deltas, no-copy strategies."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from db_models import Organisation, Website, Workspace
from db_models.base import new_uuid
from db_models.deep_competitor import (
    COMPETITOR_CATEGORIES,
    FORBIDDEN_RECOMMENDATION_MODES,
    DcCompetitorProfile,
)
from deep_competitor import (
    DeepCompetitorService,
    compute_deltas,
    discover_competitors,
    generate_differentiated_strategies,
    reverse_engineer_content,
)
from deep_competitor.delta import DimensionScoreInput
from deep_competitor.discovery import DiscoverySignalInput
from deep_competitor.models import DeepCompetitorSpec
from deep_competitor.reverse_content import ContentDimensionInput


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


def test_competitor_categories_complete() -> None:
    assert set(COMPETITOR_CATEGORIES) == {
        "business_competitor",
        "search_competitor",
        "content_competitor",
        "ai_visibility_competitor",
        "citation_competitor",
        "entity_competitor",
        "serp_competitor",
    }


def test_discovers_more_than_four_and_non_business_seo_rival() -> None:
    """Not limited to four manual domains; SEO rival need not be business rival."""
    candidates = [
        DiscoverySignalInput(
            domain="biz-rival.com",
            name="Biz Rival",
            product_similarity=0.9,
            keyword_overlap=0.5,
            known_business_competitor=True,
        ),
        DiscoverySignalInput(
            domain="seo-only.com",
            name="SEO Only",
            keyword_overlap=0.8,
            serp_overlap=0.75,
            product_similarity=0.1,
        ),
        DiscoverySignalInput(
            domain="ai-cite.com",
            ai_mention_overlap=0.7,
            citation_overlap=0.65,
            topic_overlap=0.4,
        ),
        DiscoverySignalInput(
            domain="entity-lab.com",
            entity_similarity=0.7,
            topic_overlap=0.5,
        ),
        DiscoverySignalInput(
            domain="content-hub.io",
            topic_overlap=0.85,
            keyword_overlap=0.4,
        ),
        DiscoverySignalInput(
            domain="weak.example",
            keyword_overlap=0.05,
        ),
    ]
    found = discover_competitors(candidates)
    assert len(found) >= 5  # more than four
    seo = next(c for c in found if c.domain == "seo-only.com")
    assert "search_competitor" in seo.categories or "serp_competitor" in seo.categories
    assert seo.is_direct_business_competitor is False
    biz = next(c for c in found if c.domain == "biz-rival.com")
    assert biz.is_direct_business_competitor is True
    assert "business_competitor" in biz.categories


def test_competitive_delta_answers_five_questions() -> None:
    deltas = compute_deltas(
        [
            DimensionScoreInput(
                competitor_domain="seo-only.com",
                competitor_name="SEO Only",
                dimension="search_visibility",
                client_score=0.35,
                competitor_score=0.82,
                evidence="Keyword overlap footprint",
            )
        ]
    )
    assert len(deltas) == 1
    d = deltas[0]
    assert "stronger" in d.where_stronger.lower() or d.delta > 0
    assert d.why_stronger
    assert d.gap_difficulty in {"hard", "moderate", "achievable", "easy"}
    assert d.how_to_close
    assert d.how_to_leapfrog
    assert "copy" not in d.how_to_close.lower() or "not" in d.how_to_close.lower() or "never" in d.how_to_close.lower()


def test_reverse_content_never_recommends_copying() -> None:
    diffs = reverse_engineer_content(
        [
            ContentDimensionInput(
                competitor_domain="content-hub.io",
                competitor_url="https://content-hub.io/guide",
                client_url="https://client.com/guide",
                dimension="topical_completeness",
                client_score=0.4,
                competitor_score=0.85,
                evidence_summary="Competitor covers 18 subtopics vs client 7",
            ),
            ContentDimensionInput(
                competitor_domain="content-hub.io",
                competitor_url="https://content-hub.io/guide",
                client_url="https://client.com/guide",
                dimension="original_data",
                client_score=0.2,
                competitor_score=0.7,
                evidence_summary="Competitor publishes proprietary survey",
            ),
        ]
    )
    assert diffs
    blob = " ".join(d.differentiated_recommendation.lower() for d in diffs)
    assert all(d.copy_rejected for d in diffs)
    for mode in FORBIDDEN_RECOMMENDATION_MODES:
        assert mode in blob
    assert "do not mirror" in blob or "rather than" in blob or "forbidden" in blob


def test_differentiated_strategy_rejects_copy() -> None:
    comps = discover_competitors(
        [
            DiscoverySignalInput(
                domain="rival.com",
                keyword_overlap=0.7,
                topic_overlap=0.6,
                serp_overlap=0.65,
            )
        ]
    )
    deltas = compute_deltas(
        [
            DimensionScoreInput(
                competitor_domain="rival.com",
                competitor_name="Rival",
                dimension="content_depth",
                client_score=0.3,
                competitor_score=0.8,
            )
        ]
    )
    strategies = generate_differentiated_strategies(
        competitors=comps,
        deltas=deltas,
        content_diffs=[],
        client_brand="Client",
    )
    assert strategies
    assert strategies[0].copy_competitor_content_rejected is True
    assert "copy" in strategies[0].forbidden_modes_note.lower()
    moves = " ".join(strategies[0].differentiated_moves).lower()
    assert "never copy" in moves or "do not copy" in moves


@pytest.mark.skipif(not _can_connect(), reason="PostgreSQL not available")
def test_deep_competitor_persists() -> None:
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
            name=f"dc-{suffix}",
            slug=f"dc-{suffix}",
        )
        db.add(workspace)
        db.flush()
        website = Website(
            id=new_uuid(),
            organisation_id=org.id,
            workspace_id=workspace.id,
            name=f"Site {suffix}",
            primary_domain=f"dc-{suffix}.com",
            root_url=f"https://dc-{suffix}.com",
        )
        db.add(website)
        db.commit()

        report = DeepCompetitorService(db).analyse(
            organisation_id=org.id,
            workspace_id=workspace.id,
            spec=DeepCompetitorSpec(
                website_id=website.id,
                name=f"Deep rivals {suffix}",
                client_brand="Client",
                client_domain=f"dc-{suffix}.com",
                discovery_candidates=[
                    DiscoverySignalInput(
                        domain="seo-only.com",
                        keyword_overlap=0.8,
                        serp_overlap=0.7,
                        product_similarity=0.1,
                    ),
                    DiscoverySignalInput(
                        domain="biz.com",
                        product_similarity=0.85,
                        known_business_competitor=True,
                    ),
                    DiscoverySignalInput(
                        domain="ai-vis.com",
                        ai_mention_overlap=0.7,
                        citation_overlap=0.6,
                    ),
                    DiscoverySignalInput(
                        domain="entity.com",
                        entity_similarity=0.7,
                    ),
                    DiscoverySignalInput(
                        domain="topics.com",
                        topic_overlap=0.8,
                    ),
                ],
                content_comparisons=[
                    ContentDimensionInput(
                        competitor_domain="topics.com",
                        competitor_url="https://topics.com/x",
                        client_url="https://client.com/x",
                        dimension="freshness",
                        client_score=0.3,
                        competitor_score=0.8,
                        evidence_summary="Competitor updated weekly",
                    )
                ],
            ),
        )
        assert report.copy_competitor_content_rejected is True
        assert len(report.competitors) >= 4
        assert report.strategies
        assert all(s.copy_competitor_content_rejected for s in report.strategies)
        rows = list(
            db.scalars(
                select(DcCompetitorProfile).where(
                    DcCompetitorProfile.analysis_id == report.analysis_id
                )
            ).all()
        )
        assert len(rows) >= 4
    finally:
        db.close()
