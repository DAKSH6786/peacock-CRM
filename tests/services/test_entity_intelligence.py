"""Peacock Entity Intelligence — association strength, gaps, strategy."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from db_models import Organisation, Website, Workspace
from db_models.base import new_uuid
from db_models.entity_intelligence import ENTITY_TYPES, EiAssociation, EiEntityGap
from entity_intelligence import (
    EntityIntelligenceService,
    compute_entity_gaps,
    generate_strategies,
    score_associations,
)
from entity_intelligence.models import (
    AssociationInputSpec,
    EntityIntelligenceSpec,
    EntityNodeSpec,
)
from entity_intelligence.scoring import AssociationSignal


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


def test_entity_types_cover_spec() -> None:
    required = {
        "brand",
        "founder",
        "executive",
        "product",
        "service",
        "person",
        "industry",
        "problem",
        "location",
        "competitor",
        "feature",
        "publication",
        "concept",
        "customer",
        "topic",
        "page",
        "source",
    }
    assert required <= set(ENTITY_TYPES)


def test_hsbc_style_association_strength() -> None:
    signals = [
        AssociationSignal(
            source_entity_name="HSBC",
            source_entity_type="brand",
            target_entity_name="Premier Banking",
            target_entity_type="product",
            is_client_owned=True,
            co_occurrence=0.95,
            semantic_proximity=0.9,
            ownership_signal=0.95,
            citation_linkage=0.85,
            topical_centrality=0.9,
            recency=0.8,
            cross_source_consistency=0.9,
            observation_count=40,
        ),
        AssociationSignal(
            source_entity_name="HSBC",
            source_entity_type="brand",
            target_entity_name="Wealth Management",
            target_entity_type="service",
            is_client_owned=True,
            co_occurrence=0.88,
            semantic_proximity=0.85,
            ownership_signal=0.9,
            citation_linkage=0.75,
            topical_centrality=0.85,
            recency=0.75,
            cross_source_consistency=0.8,
            observation_count=35,
        ),
        AssociationSignal(
            source_entity_name="HSBC",
            source_entity_type="brand",
            target_entity_name="Student Banking",
            target_entity_type="product",
            is_client_owned=True,
            co_occurrence=0.65,
            semantic_proximity=0.6,
            ownership_signal=0.7,
            citation_linkage=0.5,
            topical_centrality=0.55,
            recency=0.6,
            cross_source_consistency=0.55,
            observation_count=18,
        ),
    ]
    scores = score_associations(signals)
    by_target = {s.target_entity_name: s.association_strength for s in scores}
    assert by_target["Premier Banking"] > by_target["Wealth Management"] > by_target["Student Banking"]
    assert by_target["Premier Banking"] >= 0.85
    assert abs(by_target["Premier Banking"] - 0.91) < 0.08
    assert abs(by_target["Wealth Management"] - 0.84) < 0.08
    assert abs(by_target["Student Banking"] - 0.61) < 0.08
    assert all(s.explanations for s in scores)


def test_entity_gap_international_wealth_management() -> None:
    signals = [
        AssociationSignal(
            source_entity_name="Competitor A",
            source_entity_type="competitor",
            target_entity_name="International Wealth Management",
            target_entity_type="concept",
            is_competitor_owned=True,
            co_occurrence=0.9,
            semantic_proximity=0.9,
            ownership_signal=0.85,
            citation_linkage=0.85,
            topical_centrality=0.9,
            recency=0.85,
            cross_source_consistency=0.88,
            observation_count=50,
        ),
        AssociationSignal(
            source_entity_name="Competitor B",
            source_entity_type="competitor",
            target_entity_name="International Wealth Management",
            target_entity_type="concept",
            is_competitor_owned=True,
            co_occurrence=0.82,
            semantic_proximity=0.8,
            ownership_signal=0.78,
            citation_linkage=0.75,
            topical_centrality=0.8,
            recency=0.8,
            cross_source_consistency=0.8,
            observation_count=40,
        ),
        AssociationSignal(
            source_entity_name="Client",
            source_entity_type="brand",
            target_entity_name="International Wealth Management",
            target_entity_type="concept",
            is_client_owned=True,
            co_occurrence=0.4,
            semantic_proximity=0.45,
            ownership_signal=0.35,
            citation_linkage=0.3,
            topical_centrality=0.4,
            recency=0.5,
            cross_source_consistency=0.35,
            observation_count=12,
        ),
    ]
    scores = score_associations(signals)
    gaps = compute_entity_gaps(
        client_brand="Client",
        associations=scores,
        target_concepts=["International Wealth Management"],
    )
    assert len(gaps) == 1
    gap = gaps[0]
    assert gap.leading_competitor_name == "Competitor A"
    assert gap.leading_competitor_association >= 0.80
    assert gap.competitor_associations["Competitor B"] >= 0.70
    assert gap.client_association <= 0.50
    assert gap.gap_size >= 0.30
    assert "International Wealth Management" in gap.summary

    strategies = generate_strategies(gaps=gaps, client_brand="Client")
    assert strategies
    assert strategies[0].target_concept == "International Wealth Management"
    assert strategies[0].recommended_moves
    assert strategies[0].expected_association_lift > 0


@pytest.mark.skipif(not _can_connect(), reason="PostgreSQL not available")
def test_entity_intelligence_persists() -> None:
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
            name=f"ei-{suffix}",
            slug=f"ei-{suffix}",
        )
        db.add(workspace)
        db.flush()
        website = Website(
            id=new_uuid(),
            organisation_id=org.id,
            workspace_id=workspace.id,
            name=f"Site {suffix}",
            primary_domain=f"ei-{suffix}.com",
            root_url=f"https://ei-{suffix}.com",
        )
        db.add(website)
        db.commit()

        report = EntityIntelligenceService(db).analyse(
            organisation_id=org.id,
            workspace_id=workspace.id,
            spec=EntityIntelligenceSpec(
                website_id=website.id,
                name=f"Banking entities {suffix}",
                client_brand="HSBC",
                industry="Banking",
                entities=[
                    EntityNodeSpec("HSBC", "brand", is_client=True),
                    EntityNodeSpec("Competitor A", "competitor", is_competitor=True),
                ],
                associations=[
                    AssociationInputSpec(
                        source_entity_name="HSBC",
                        source_entity_type="brand",
                        target_entity_name="Premier Banking",
                        target_entity_type="product",
                        is_client_owned=True,
                        co_occurrence=0.95,
                        semantic_proximity=0.9,
                        ownership_signal=0.95,
                        citation_linkage=0.85,
                        topical_centrality=0.9,
                        recency=0.8,
                        cross_source_consistency=0.9,
                        observation_count=40,
                    ),
                    AssociationInputSpec(
                        source_entity_name="Competitor A",
                        source_entity_type="competitor",
                        target_entity_name="International Wealth Management",
                        target_entity_type="concept",
                        is_competitor_owned=True,
                        co_occurrence=0.9,
                        semantic_proximity=0.9,
                        ownership_signal=0.85,
                        citation_linkage=0.85,
                        topical_centrality=0.9,
                        recency=0.85,
                        cross_source_consistency=0.88,
                        observation_count=50,
                    ),
                    AssociationInputSpec(
                        source_entity_name="HSBC",
                        source_entity_type="brand",
                        target_entity_name="International Wealth Management",
                        target_entity_type="concept",
                        is_client_owned=True,
                        co_occurrence=0.4,
                        semantic_proximity=0.45,
                        ownership_signal=0.35,
                        citation_linkage=0.3,
                        topical_centrality=0.4,
                        recency=0.5,
                        cross_source_consistency=0.35,
                        observation_count=12,
                    ),
                ],
                target_concepts=["International Wealth Management", "Premier Banking"],
            ),
        )
        assert report.example_ownership
        assert report.gaps
        assert report.strategies
        rows = list(
            db.scalars(
                select(EiAssociation).where(EiAssociation.analysis_id == report.analysis_id)
            ).all()
        )
        assert len(rows) == 3
        gap_rows = list(
            db.scalars(
                select(EiEntityGap).where(EiEntityGap.analysis_id == report.analysis_id)
            ).all()
        )
        assert gap_rows
    finally:
        db.close()
