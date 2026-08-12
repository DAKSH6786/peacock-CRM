"""Peacock Judge 2.0 — deterministic multi-signal judgment + reversal conditions."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from db_models import Organisation, Website, Workspace
from db_models.base import new_uuid
from db_models.judge2 import J2ReversalCondition, Judge2Judgment
from judge2 import (
    JUDGE_SIGNAL_FAMILIES,
    EvidenceInput,
    Judge2Service,
    Judge2Spec,
    JudgeBrief,
    judge_decision,
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


def test_signal_families() -> None:
    assert set(JUDGE_SIGNAL_FAMILIES) == {
        "deterministic_data",
        "statistical_evidence",
        "historical_outcomes",
        "multi_model_findings",
        "source_reliability",
        "business_goals",
        "cost",
        "risk",
        "confidence",
    }


def test_deterministic_scoring_outside_llm_and_outputs() -> None:
    result = judge_decision(
        JudgeBrief(
            decision_question="Invest in proprietary GEO benchmark study?",
            client_brand="Acme",
            signals={
                "deterministic_data": 80,
                "statistical_evidence": 75,
                "historical_outcomes": 70,
                "multi_model_findings": 72,
                "source_reliability": 85,
                "business_goals": 90,
                "cost": 40,
                "risk": 35,
                "confidence": 80,
            },
            evidence=[
                EvidenceInput(
                    evidence_type="stat",
                    statement="Prior benchmark pages earned citations at 2.1x baseline.",
                    reliability=80,
                    signal_code="historical_outcomes",
                )
            ],
            business_goal_summary="Grow AI citation share in CRM category.",
        )
    )
    assert result.scoring_outside_llm is True
    assert "outside LLM" in result.scoring_note or "outside the LLM" in result.scoring_note
    assert all(s.computed_outside_llm for s in result.signal_scores)
    assert len(result.signal_scores) == 9
    assert result.recommended_action
    assert result.why
    assert result.evidence
    assert result.expected_upside and result.expected_upside_score >= 0
    assert result.risk_summary and result.risk_score >= 0
    assert 0 <= result.confidence <= 100
    assert result.alternative
    assert result.what_would_change_decision
    assert "WHAT WOULD CHANGE THIS RECOMMENDATION" in result.what_would_change_decision
    assert any("keyword demand declines >40%" in r.statement for r in result.reversal_conditions)
    assert any(
        "Competitor A loses citation dominance" in r.statement
        for r in result.reversal_conditions
    )
    assert result.action_code in ("proceed", "conditional", "defer", "reject")
    assert result.composite_score >= 60


def test_high_risk_cost_defers_or_rejects() -> None:
    weak = judge_decision(
        JudgeBrief(
            decision_question="Bet the brand on unproven tactic?",
            client_brand="Acme",
            signals={
                "deterministic_data": 30,
                "statistical_evidence": 25,
                "historical_outcomes": 20,
                "multi_model_findings": 30,
                "source_reliability": 40,
                "business_goals": 35,
                "cost": 90,
                "risk": 92,
                "confidence": 30,
            },
        )
    )
    strong = judge_decision(
        JudgeBrief(
            decision_question="Ship measured content refresh?",
            client_brand="Acme",
            signals={
                "deterministic_data": 85,
                "statistical_evidence": 80,
                "historical_outcomes": 78,
                "multi_model_findings": 82,
                "source_reliability": 88,
                "business_goals": 86,
                "cost": 25,
                "risk": 20,
                "confidence": 90,
            },
        )
    )
    assert strong.composite_score > weak.composite_score
    assert weak.action_code in ("defer", "reject", "conditional")
    assert strong.action_code in ("proceed", "conditional")


@pytest.mark.skipif(not _can_connect(), reason="PostgreSQL not available")
def test_judge2_persists() -> None:
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
            name=f"j2-{suffix}",
            slug=f"j2-{suffix}",
        )
        db.add(workspace)
        db.flush()
        website = Website(
            id=new_uuid(),
            organisation_id=org.id,
            workspace_id=workspace.id,
            name=f"Site {suffix}",
            primary_domain=f"j2-{suffix}.com",
            root_url=f"https://j2-{suffix}.com",
        )
        db.add(website)
        db.commit()

        report = Judge2Service(db).judge(
            organisation_id=org.id,
            workspace_id=workspace.id,
            spec=Judge2Spec(
                website_id=website.id,
                name=f"Judge {suffix}",
                brief=JudgeBrief(
                    decision_question="Approve GEO Lab budget?",
                    client_brand="Acme",
                    signals={"business_goals": 80, "risk": 40, "confidence": 70},
                ),
            ),
        )
        assert report.result.scoring_outside_llm is True
        row = db.scalar(
            select(Judge2Judgment).where(Judge2Judgment.id == report.judgment_id)
        )
        assert row is not None
        assert row.scoring_outside_llm is True
        assert row.what_would_change_decision
        reversals = list(
            db.scalars(
                select(J2ReversalCondition).where(
                    J2ReversalCondition.judgment_id == report.judgment_id
                )
            ).all()
        )
        assert reversals
    finally:
        db.close()
