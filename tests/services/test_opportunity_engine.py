"""Peacock Opportunity Engine — explainable adaptive ranking."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from db_models import Organisation, Website, Workspace
from db_models.base import new_uuid
from db_models.opportunity_engine import OpportunityScan, PeacockOpportunity
from opportunity_engine import (
    DEFAULT_RANKING_WEIGHTS,
    OPPORTUNITY_TYPES,
    RANKING_FEATURES,
    EvidenceInput,
    OpportunityEngineService,
    OpportunityScanSpec,
    OutcomeFeedbackInput,
    SignalInput,
    detect_and_rank,
    learn_weights_from_outcomes,
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


def _signal(
    opportunity_type: str,
    *,
    impact: float,
    urgency: float,
    confidence: float,
    difficulty: float,
    expected_value: float,
    title: str | None = None,
) -> SignalInput:
    return SignalInput(
        opportunity_type=opportunity_type,
        title=title or opportunity_type.replace("_", " ").title(),
        description=f"Signal for {opportunity_type}",
        impact=impact,
        urgency=urgency,
        confidence=confidence,
        difficulty=difficulty,
        expected_value=expected_value,
        recommended_action="Act on the signal with evidence-backed content.",
        evidence=[
            EvidenceInput(
                evidence_type="observation",
                statement=f"Observed {opportunity_type}",
                strength=confidence,
            )
        ],
        related_entity="Acme",
    )


def test_opportunity_types_cover_examples() -> None:
    required = {
        "competitor_gained_ai_visibility",
        "new_citation_source_emerged",
        "high_value_topic_available",
        "existing_article_decaying",
        "entity_relationship_weakened",
        "new_prompt_cluster_appeared",
        "competitor_content_outdated",
        "ai_sentiment_changed",
        "backlink_source_gained_influence",
        "search_demand_shifted",
        "ai_answer_changed_materially",
    }
    assert required == set(OPPORTUNITY_TYPES)
    assert set(RANKING_FEATURES) == {
        "impact",
        "urgency",
        "confidence",
        "expected_value",
        "difficulty",
    }
    assert abs(sum(DEFAULT_RANKING_WEIGHTS.values()) - 1.0) < 1e-6


def test_explainable_ranking_and_fields() -> None:
    result = detect_and_rank(
        [
            _signal(
                "existing_article_decaying",
                impact=80,
                urgency=90,
                confidence=70,
                difficulty=40,
                expected_value=85,
                title="Existing article is decaying",
            ),
            _signal(
                "competitor_content_outdated",
                impact=50,
                urgency=40,
                confidence=60,
                difficulty=70,
                expected_value=45,
            ),
        ]
    )
    assert result.fixed_formula_rejected is True
    assert result.ranking_is_adaptive is True
    assert "always" in result.always_on_note.lower() or "continuous" in result.always_on_note.lower()
    top = result.opportunities[0]
    assert top.rank == 1
    assert top.opportunity_score >= result.opportunities[1].opportunity_score
    assert top.impact and top.urgency and top.confidence
    assert top.difficulty is not None and top.expected_value is not None
    assert top.recommended_action
    assert top.evidence
    assert len(top.ranking_factors) == len(RANKING_FEATURES)
    assert "Explainable" in top.ranking_explanation or "explainable" in top.ranking_explanation.lower()
    assert all(w.feature_code in RANKING_FEATURES for w in result.ranking_weights)


def test_outcomes_adapt_weights_not_forever_fixed() -> None:
    # Outcomes where high expected_value strongly predicts success
    feedback = [
        OutcomeFeedbackInput(
            opportunity_type="high_value_topic_available",
            impact=60,
            urgency=50,
            confidence=55,
            difficulty=40,
            expected_value=90,
            predicted_score=60,
            realized_outcome=95,
        )
        for _ in range(5)
    ] + [
        OutcomeFeedbackInput(
            opportunity_type="ai_sentiment_changed",
            impact=80,
            urgency=80,
            confidence=40,
            difficulty=30,
            expected_value=20,
            predicted_score=70,
            realized_outcome=25,
        )
        for _ in range(5)
    ]
    model = learn_weights_from_outcomes(feedback)
    assert model.learning_sample_size == 10
    assert model.blend_toward_learned > 0
    eff = model.effective_weights()
    base = dict(DEFAULT_RANKING_WEIGHTS)
    # Effective weights should differ from pure base once learning kicks in
    assert any(abs(eff[k] - base[k]) > 0.01 for k in RANKING_FEATURES)
    # fixed forever formula rejected conceptually
    snaps = model.weight_snapshots()
    assert any("Fixed forever-formula rejected" in s.explanation for s in snaps)

    ranked = detect_and_rank(
        [
            _signal(
                "high_value_topic_available",
                impact=55,
                urgency=50,
                confidence=50,
                difficulty=40,
                expected_value=95,
            ),
            _signal(
                "ai_sentiment_changed",
                impact=85,
                urgency=85,
                confidence=40,
                difficulty=30,
                expected_value=15,
            ),
        ],
        model=model,
    )
    assert ranked.fixed_formula_rejected is True
    assert ranked.opportunities[0].opportunity_type == "high_value_topic_available"


@pytest.mark.skipif(not _can_connect(), reason="PostgreSQL not available")
def test_opportunity_scan_persists() -> None:
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
            name=f"po-{suffix}",
            slug=f"po-{suffix}",
        )
        db.add(workspace)
        db.flush()
        website = Website(
            id=new_uuid(),
            organisation_id=org.id,
            workspace_id=workspace.id,
            name=f"Site {suffix}",
            primary_domain=f"po-{suffix}.com",
            root_url=f"https://po-{suffix}.com",
        )
        db.add(website)
        db.commit()

        report = OpportunityEngineService(db).run_scan(
            organisation_id=org.id,
            workspace_id=workspace.id,
            spec=OpportunityScanSpec(
                website_id=website.id,
                name=f"Scan {suffix}",
                client_brand="Acme",
                signals=[
                    _signal(
                        "competitor_gained_ai_visibility",
                        impact=75,
                        urgency=70,
                        confidence=65,
                        difficulty=50,
                        expected_value=80,
                    )
                ],
            ),
        )
        assert report.always_on_layer is True
        assert report.result.fixed_formula_rejected is True
        scan = db.scalar(
            select(OpportunityScan).where(OpportunityScan.id == report.scan_id)
        )
        assert scan is not None
        assert scan.fixed_formula_rejected is True
        opps = list(
            db.scalars(
                select(PeacockOpportunity).where(
                    PeacockOpportunity.scan_id == report.scan_id
                )
            ).all()
        )
        assert len(opps) == 1
    finally:
        db.close()
