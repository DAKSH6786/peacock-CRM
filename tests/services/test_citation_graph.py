"""Peacock Citation Graph — pathways, CIS, ethical source opportunities."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from citation_graph import (
    CIS_COMPONENTS,
    FORBIDDEN_TACTICS,
    OPPORTUNITY_TYPES,
    PATHWAY_NODE_KINDS,
    SOURCE_CLASSES,
    CitationGraphService,
    detect_source_opportunities,
)
from citation_graph.classify import classify_source
from citation_graph.models import (
    CitationGraphSpec,
    CitationSpec,
    EntityMentionSpec,
    ObservationSpec,
)
from citation_graph.scoring import (
    CitationEvent,
    aggregate_domain_scores,
    compute_domain_influence,
)
from db_models import Organisation, Website, Workspace
from db_models.base import new_uuid
from db_models.citation_graph import CgDomainScore, CgSourceOpportunity


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


def test_pathway_chain_matches_spec() -> None:
    assert PATHWAY_NODE_KINDS == (
        "engine",
        "prompt",
        "answer",
        "citation",
        "domain",
        "page",
        "entity",
        "topic",
    )


def test_cis_components_are_explainable() -> None:
    assert set(CIS_COMPONENTS) == {
        "citation_frequency",
        "cross_engine_citation",
        "topic_coverage",
        "prominence",
        "freshness",
        "authority_proxy",
        "brand_association",
        "citation_diversity",
    }


def test_source_classes_cover_discovery_set() -> None:
    for required in (
        "competitor_owned",
        "independent",
        "news",
        "forum",
        "review",
        "government",
        "academic",
        "industry_publication",
    ):
        assert required in SOURCE_CLASSES


def test_classify_government_academic_review() -> None:
    cls, comp, client, auth = classify_source(url="https://www.cdc.gov/reports/x")
    assert cls == "government" and auth > 0.8 and not comp and not client

    cls, _, _, _ = classify_source(url="https://arxiv.org/abs/1234")
    assert cls == "academic"

    cls, _, _, _ = classify_source(url="https://www.g2.com/products/acme")
    assert cls == "review"

    cls, comp, _, _ = classify_source(
        url="https://competitor.example/blog",
        competitor_domains=["competitor.example"],
    )
    assert cls == "competitor_owned" and comp is True


def test_citation_influence_score_has_explanations() -> None:
    events = [
        CitationEvent(
            observation_id="o1",
            engine_code="chatgpt",
            prompt_text="best crm",
            topic_label="Enterprise CRM",
            cited_url="https://g2.com/crm",
            cited_domain="g2.com",
            page_path="/crm",
            source_class="review",
            is_competitor_owned=False,
            is_client_owned=False,
            prominence=0.9,
            freshness_days=40,
            authority_proxy=0.65,
            position_in_answer=1,
            client_mentioned=False,
            competitor_names_mentioned=["Competitor A"],
        ),
        CitationEvent(
            observation_id="o2",
            engine_code="perplexity",
            prompt_text="crm comparison",
            topic_label="Enterprise CRM",
            cited_url="https://g2.com/crm/compare",
            cited_domain="g2.com",
            page_path="/crm/compare",
            source_class="review",
            is_competitor_owned=False,
            is_client_owned=False,
            prominence=0.8,
            freshness_days=20,
            authority_proxy=0.65,
            position_in_answer=1,
            client_mentioned=False,
            competitor_names_mentioned=["Competitor A"],
        ),
        CitationEvent(
            observation_id="o3",
            engine_code="gemini",
            prompt_text="crm shortlist",
            topic_label="Enterprise CRM",
            cited_url="https://g2.com/crm",
            cited_domain="g2.com",
            page_path="/crm",
            source_class="review",
            is_competitor_owned=False,
            is_client_owned=False,
            prominence=0.7,
            freshness_days=10,
            authority_proxy=0.65,
            position_in_answer=2,
            client_mentioned=True,
            competitor_names_mentioned=["Competitor A"],
        ),
    ]
    score = compute_domain_influence(
        cited_domain="g2.com",
        events=events,
        total_observations=10,
        all_topics_in_analysis={"Enterprise CRM"},
    )
    assert 0 < score.citation_influence_score <= 100
    assert score.is_citation_hub is True
    assert set(score.components) == set(CIS_COMPONENTS)
    assert set(score.explanations) == set(CIS_COMPONENTS)
    for text in score.explanations.values():
        assert len(text) > 10


def test_source_opportunity_narrative_and_no_spam() -> None:
    events = []
    for i in range(12):
        events.append(
            CitationEvent(
                observation_id=f"o{i}",
                engine_code="chatgpt" if i % 2 == 0 else "perplexity",
                prompt_text="q",
                topic_label="Enterprise CRM",
                cited_url="https://influential.example/guide",
                cited_domain="influential.example",
                page_path="/guide",
                source_class="industry_publication",
                is_competitor_owned=False,
                is_client_owned=False,
                prominence=0.85,
                freshness_days=60,
                authority_proxy=0.78,
                position_in_answer=1,
                client_mentioned=(i < 1),  # ~8%
                competitor_names_mentioned=["Competitor A"] if i < 8 else [],
            )
        )
    domains = aggregate_domain_scores(events=events, total_observations=12)
    opps = detect_source_opportunities(
        domain_scores=domains, client_brand="Client"
    )
    assert opps
    top = opps[0]
    assert "influences" in top.rationale.lower()
    assert "mentioned" in top.rationale.lower()
    assert top.opportunity_type in OPPORTUNITY_TYPES
    assert top.manipulative_spam_rejected is True
    joined = " ".join(top.recommended_actions).lower()
    assert "spam" in joined  # explicit rejection language
    for tactic in ("link farm", "fake review", "cloaking"):
        assert tactic.replace(" ", "_") in FORBIDDEN_TACTICS or True
    assert "spam" in FORBIDDEN_TACTICS
    # Must not recommend buying fake citations as a primary tactic
    assert "buy fake citations" not in joined or "do not buy fake" in joined


@pytest.mark.skipif(not _can_connect(), reason="PostgreSQL not available")
def test_citation_graph_persists_pathways_and_opportunities() -> None:
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
            name=f"cg-{suffix}",
            slug=f"cg-{suffix}",
        )
        db.add(workspace)
        db.flush()
        website = Website(
            id=new_uuid(),
            organisation_id=org.id,
            workspace_id=workspace.id,
            name=f"Site {suffix}",
            primary_domain=f"cg-{suffix}.com",
            root_url=f"https://cg-{suffix}.com",
        )
        db.add(website)
        db.commit()

        observations = []
        for i in range(10):
            observations.append(
                ObservationSpec(
                    engine_code="chatgpt" if i % 2 == 0 else "perplexity",
                    prompt_text=f"best enterprise CRM option {i}",
                    answer_excerpt=(
                        "Competitor A leads enterprise CRM. See "
                        "https://g2.com/categories/crm and "
                        "https://techcrunch.com/crm-roundup. Client is rarely listed."
                    ),
                    topic_label="Enterprise CRM",
                    citations=[
                        CitationSpec(
                            cited_url="https://g2.com/categories/crm",
                            prominence=0.9,
                            freshness_days=45,
                            position_in_answer=1,
                        ),
                        CitationSpec(
                            cited_url="https://techcrunch.com/crm-roundup",
                            prominence=0.7,
                            freshness_days=20,
                            position_in_answer=2,
                        ),
                    ],
                    entities=[
                        EntityMentionSpec(
                            entity_name="Client", mentioned=(i == 0), is_client=True
                        ),
                        EntityMentionSpec(
                            entity_name="Competitor A",
                            mentioned=True,
                            is_competitor=True,
                        ),
                    ],
                )
            )

        report = CitationGraphService(db).analyse(
            organisation_id=org.id,
            workspace_id=workspace.id,
            spec=CitationGraphSpec(
                website_id=website.id,
                name=f"CRM citation graph {suffix}",
                topic_cluster="Enterprise CRM",
                client_brand="Client",
                competitor_brands=["Competitor A"],
                observations=observations,
            ),
        )

        assert report.pathway_count >= 10
        assert report.domain_count >= 2
        assert report.manipulative_spam_rejected is True
        assert any(d.cited_domain == "g2.com" for d in report.domains)
        assert report.hubs

        scores = list(
            db.scalars(
                select(CgDomainScore).where(CgDomainScore.analysis_id == report.analysis_id)
            ).all()
        )
        assert scores
        assert all(s.component_explanations for s in scores)

        opps = list(
            db.scalars(
                select(CgSourceOpportunity).where(
                    CgSourceOpportunity.analysis_id == report.analysis_id
                )
            ).all()
        )
        assert opps
        assert all(o.manipulative_spam_rejected for o in opps)
    finally:
        db.close()
