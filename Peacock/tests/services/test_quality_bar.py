"""Peacock One Quality Bar — shipping completeness gates."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from db_models import Organisation, Website, Workspace
from db_models.base import new_uuid
from db_models.quality_bar import QUALITY_GATES, QualityBarAssessment
from quality_bar import (
    GateAnswer,
    QualityBarCreateSpec,
    QualityBarService,
    QualityBarSpec,
    assess_quality_bar,
    catalog,
    demo_assessment,
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


def test_catalog_seven_gates() -> None:
    c = catalog()
    assert c["quality_gates"] == list(QUALITY_GATES)
    assert len(c["quality_gates"]) == 7
    assert any("conventional SEO" in q for q in c["checklist"])
    assert any("Peacock Learning" in q for q in c["checklist"])
    assert any("Move it out of the LLM" in q for q in c["checklist"])


def test_llm_only_recommender_incomplete() -> None:
    result = demo_assessment("Acme")
    assert result.completeness_verdict == "incomplete"
    assert result.gates_failed >= 4
    assert "evidence_backed_recommendations" in result.blocked_by
    assert "uncertainty_with_evidence" in result.blocked_by
    assert "outcome_tracking" in result.blocked_by
    assert "learning_loop" in result.blocked_by
    assert "deterministic_over_llm" in result.blocked_by
    labels = {r.action_label for r in result.remediation_actions}
    assert "Add evidence." in labels or "Add evidence" in " ".join(labels)
    assert any(r.links_to_learning for r in result.remediation_actions)
    assert "Add evidence" in result.improvement_summary
    assert "Add confidence" in result.improvement_summary
    assert "outcome tracking" in result.improvement_summary.lower()
    assert "Peacock Learning" in result.improvement_summary
    assert "Move it out of the LLM" in result.improvement_summary


def test_share_of_answer_complete() -> None:
    result = assess_quality_bar(
        QualityBarSpec(client_brand="Acme", module_key="share_of_answer")
    )
    assert result.completeness_verdict == "complete"
    assert result.gates_passed == 7
    assert result.completeness_score == 100.0
    assert result.remediation_actions == []


def test_conventional_seo_blocked() -> None:
    result = assess_quality_bar(
        QualityBarSpec(client_brand="Acme", module_key="conventional_seo_auditor")
    )
    assert result.completeness_verdict in ("incomplete", "blocked")
    assert result.gates_failed >= 5
    seo_gate = next(
        g for g in result.gate_results if g.gate_key == "beyond_conventional_seo"
    )
    assert seo_gate.passed is False
    assert seo_gate.improvement_if_fail == "Improve it."


def test_custom_overrides() -> None:
    answers = [
        GateAnswer(gate_key=g, answer_yes_problem=False, rationale="ok")
        for g in QUALITY_GATES
    ]
    result = assess_quality_bar(
        QualityBarSpec(
            client_brand="Acme",
            module_key="custom",
            module_label="Fixed custom module",
            gate_answers=answers,
        )
    )
    assert result.completeness_verdict == "complete"


@pytest.mark.skipif(not _can_connect(), reason="PostgreSQL not available")
def test_persist_assessment() -> None:
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
            name=f"qb-{suffix}",
            slug=f"qb-{suffix}",
        )
        db.add(workspace)
        db.flush()
        website = Website(
            id=new_uuid(),
            organisation_id=org.id,
            workspace_id=workspace.id,
            name=f"Site {suffix}",
            primary_domain=f"qb-{suffix}.com",
            root_url=f"https://qb-{suffix}.com",
        )
        db.add(website)
        db.commit()

        report = QualityBarService(db).assess(
            organisation_id=org.id,
            workspace_id=workspace.id,
            created_by=None,
            spec=QualityBarCreateSpec(
                website_id=website.id,
                name=f"QB {suffix}",
                assessment=QualityBarSpec(
                    client_brand="Acme",
                    module_key="llm_only_recommender",
                ),
            ),
        )
        assert report.result.gates_failed >= 4
        row = db.scalar(
            select(QualityBarAssessment).where(
                QualityBarAssessment.id == report.assessment_id
            )
        )
        assert row is not None
        assert row.completeness_verdict == "incomplete"

        loaded = QualityBarService(db).get_assessment(
            assessment_id=report.assessment_id, organisation_id=org.id
        )
        assert loaded is not None
        assert len(loaded.result.gate_results) == 7
    finally:
        db.close()
