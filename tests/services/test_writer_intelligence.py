"""Writer Intelligence 2.0 — DNA, W×T×C outcome model, Outcome Graph."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from db_models import Organisation, Website, Workspace
from db_models.base import new_uuid
from db_models.writer_intelligence import WiRecommendation, WriterIntelligenceAnalysis
from writer_intelligence import (
    PERFORMANCE_METRICS,
    SIMILARITY_ONLY_REJECTED,
    WRITER_DNA_TRAITS,
    ArticleOutcomeHistory,
    DecisionContext,
    WriterCandidate,
    WriterIntelligenceService,
    WriterIntelligenceSpec,
    recommend_writers,
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


def test_dna_traits_cover_spec() -> None:
    required = {
        "subject_expertise",
        "research_depth",
        "technical_accuracy",
        "style",
        "tone",
        "sentence_structure",
        "readability",
        "storytelling",
        "citations",
        "fact_density",
        "original_thinking",
        "seo_execution",
        "aeo_execution",
        "geo_execution",
        "editing_effort",
        "deadline_reliability",
        "client_acceptance",
    }
    assert required == set(WRITER_DNA_TRAITS)
    assert set(PERFORMANCE_METRICS) == {
        "approval",
        "revision_rounds",
        "ranking",
        "impressions",
        "ai_citations",
        "engagement",
        "links_earned",
        "conversion",
    }


def test_rejects_similarity_only_as_primary() -> None:
    assert "Similarity-only" in SIMILARITY_ONLY_REJECTED or "similarity" in SIMILARITY_ONLY_REJECTED.lower()
    result = recommend_writers(
        context=DecisionContext(
            client_brand="Acme",
            industry="B2B SaaS",
            topic="CRM pipeline conversion",
            audience="RevOps leaders",
        ),
        writers=[
            WriterCandidate(writer_key="w1", display_name="Alex"),
            WriterCandidate(writer_key="w2", display_name="Sam"),
        ],
        history=[],
    )
    assert result.similarity_only_rejected is True
    assert all(r.similarity_not_used_as_primary for r in result.recommendations)
    assert all(r.similarity_score_unused is None for r in result.recommendations)
    assert "THIS topic" in result.decision_question or "topic" in result.decision_question.lower()
    assert "best outcome" in result.decision_question.lower()


def test_outcome_model_prefers_topic_client_fit_over_generic() -> None:
    specialist = WriterCandidate(
        writer_key="specialist",
        display_name="Specialist",
        dna_traits={
            "subject_expertise": 90,
            "geo_execution": 85,
            "aeo_execution": 80,
            "seo_execution": 80,
            "citations": 85,
            "original_thinking": 80,
            "deadline_reliability": 90,
            "client_acceptance": 88,
            "editing_effort": 20,
            "research_depth": 85,
            "technical_accuracy": 88,
            "fact_density": 82,
        },
        subject_tags=["crm", "pipeline conversion", "revops"],
        prior_clients=["Acme"],
        prior_industries=["B2B SaaS"],
        prior_topics=["CRM pipeline conversion", "sales velocity"],
        prior_audiences=["RevOps leaders"],
    )
    generalist = WriterCandidate(
        writer_key="generalist",
        display_name="Generalist",
        dna_traits={
            "subject_expertise": 55,
            "style": 90,
            "tone": 90,
            "storytelling": 88,
            "readability": 85,
            "seo_execution": 50,
            "aeo_execution": 45,
            "geo_execution": 40,
            "editing_effort": 40,
            "deadline_reliability": 70,
            "client_acceptance": 60,
        },
        subject_tags=["lifestyle", "travel"],
        prior_clients=["TravelCo"],
        prior_industries=["Travel"],
        prior_topics=["weekend getaways"],
        prior_audiences=["consumers"],
    )
    history = [
        ArticleOutcomeHistory(
            article_key="a1",
            writer_key="specialist",
            client_key="Acme",
            industry="B2B SaaS",
            topic="CRM pipeline conversion",
            approval=0.95,
            revision_rounds=1,
            ranking=0.8,
            ai_citations=12,
            links_earned=8,
            conversion=0.04,
        ),
        ArticleOutcomeHistory(
            article_key="a2",
            writer_key="generalist",
            client_key="TravelCo",
            industry="Travel",
            topic="weekend getaways",
            approval=0.9,
            revision_rounds=1,
            ranking=0.7,
            ai_citations=2,
            engagement=0.5,
        ),
    ]
    result = recommend_writers(
        context=DecisionContext(
            client_brand="Acme",
            industry="B2B SaaS",
            topic="CRM pipeline conversion",
            audience="RevOps leaders",
            needs_seo=True,
            needs_aeo=True,
            needs_geo=True,
        ),
        writers=[specialist, generalist],
        history=history,
    )
    assert result.recommendations[0].writer_key == "specialist"
    assert (
        result.recommendations[0].predicted_outcome_score
        > result.recommendations[1].predicted_outcome_score
    )
    assert result.dna_profiles
    assert len(result.dna_profiles[0].traits) == len(WRITER_DNA_TRAITS)
    kinds = {n.node_kind for n in result.outcome_nodes}
    assert {"writer", "article", "client", "industry", "topic", "performance"} <= kinds
    assert any(e.edge_type == "wrote" for e in result.outcome_edges)
    assert any(e.edge_type == "achieved" for e in result.outcome_edges)
    assert result.performance_records


@pytest.mark.skipif(not _can_connect(), reason="PostgreSQL not available")
def test_writer_intelligence_persists() -> None:
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
            name=f"wi-{suffix}",
            slug=f"wi-{suffix}",
        )
        db.add(workspace)
        db.flush()
        website = Website(
            id=new_uuid(),
            organisation_id=org.id,
            workspace_id=workspace.id,
            name=f"Site {suffix}",
            primary_domain=f"wi-{suffix}.com",
            root_url=f"https://wi-{suffix}.com",
        )
        db.add(website)
        db.commit()

        report = WriterIntelligenceService(db).analyse(
            organisation_id=org.id,
            workspace_id=workspace.id,
            spec=WriterIntelligenceSpec(
                website_id=website.id,
                name=f"WI {suffix}",
                context=DecisionContext(
                    client_brand="Acme",
                    industry="SaaS",
                    topic="AI citations",
                    audience="CMOs",
                ),
                writers=[
                    WriterCandidate(
                        writer_key=f"w-{suffix}",
                        display_name="Pat",
                        dna_traits={"geo_execution": 80, "subject_expertise": 75},
                        prior_topics=["AI citations"],
                        prior_clients=["Acme"],
                    )
                ],
                history=[
                    ArticleOutcomeHistory(
                        article_key=f"art-{suffix}",
                        writer_key=f"w-{suffix}",
                        client_key="Acme",
                        industry="SaaS",
                        topic="AI citations",
                        approval=0.9,
                        ai_citations=5,
                    )
                ],
            ),
        )
        assert report.result.similarity_only_rejected is True
        row = db.scalar(
            select(WriterIntelligenceAnalysis).where(
                WriterIntelligenceAnalysis.id == report.analysis_id
            )
        )
        assert row is not None
        assert row.similarity_only_rejected is True
        recs = list(
            db.scalars(
                select(WiRecommendation).where(
                    WiRecommendation.analysis_id == report.analysis_id
                )
            ).all()
        )
        assert len(recs) == 1
        assert recs[0].similarity_not_used_as_primary is True
    finally:
        db.close()
