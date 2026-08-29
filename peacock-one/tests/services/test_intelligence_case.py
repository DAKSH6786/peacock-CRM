"""PINE IntelligenceCase — typed aggregate + relational persistence."""

from __future__ import annotations

import os
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from db_models import IntelligenceCaseEvidence, IntelligenceCaseRecord, Organisation, Workspace
from db_models.base import new_uuid
from intelligence import (
    CaseAgentFinding,
    CaseAssumption,
    CaseContextItem,
    CaseContradiction,
    CaseEvidence,
    CaseHypothesis,
    CaseModelUsed,
    CaseObservation,
    CaseOpportunity,
    CaseRecommendation,
    CaseRisk,
    CaseToolUsed,
    CaseUnknown,
    IntelligenceCase,
    IntelligenceCaseRepository,
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


def _sample_case(org_id: str, workspace_id: str) -> IntelligenceCase:
    return IntelligenceCase(
        case_id=new_uuid(),
        organisation_id=org_id,
        workspace_id=workspace_id,
        objective="Improve generative visibility for brand queries",
        title="Brand visibility case",
        confidence=0.72,
        cost_usd_micros=12500,
        latency_ms=840,
        created_at=datetime.now(UTC),
        context=[
            CaseContextItem(
                kind="website",
                key="primary",
                summary="Primary marketing site",
                relevance=0.9,
                tokens_estimate=120,
                source="context_selector",
            )
        ],
        observations=[
            CaseObservation(
                code="obs.crawl.pages",
                label="Crawl coverage",
                detail="120 pages indexed in last crawl",
                source="crawler",
            )
        ],
        evidence=[
            CaseEvidence(
                code="ev.seo.score",
                label="Peacock SEO Score",
                kind="deterministic",
                source="seo_engine",
                confidence=1.0,
                value_number=68.0,
                unit="score",
                related_urls=["https://example.com/"],
            ),
            CaseEvidence(
                code="ev.research.mention",
                label="AI mention rate",
                kind="research",
                source="geo_probe",
                confidence=0.8,
                value_text="mentioned in 2 of 5 engines",
            ),
        ],
        hypotheses=[
            CaseHypothesis(
                statement="Schema gaps reduce citation likelihood",
                confidence=0.65,
                supporting_evidence_codes=["ev.seo.score"],
            )
        ],
        agent_findings=[
            CaseAgentFinding(
                agent_name="schema_specialist",
                role="specialist",
                summary="Missing Organisation and FAQ schema on key pages",
                confidence=0.7,
                claims=["FAQ pages lack FAQPage markup", "Organisation schema incomplete"],
            )
        ],
        contradictions=[
            CaseContradiction(
                claim="Content volume is sufficient",
                challenge="Top competitors publish 3x more topical cluster pages",
                severity="medium",
            )
        ],
        unknowns=[
            CaseUnknown(
                question="What is current GSC brand CTR for AI-referred sessions?",
                impact_if_unknown="Cannot quantify brand query opportunity",
            )
        ],
        assumptions=[
            CaseAssumption(
                statement="Primary market is English-speaking enterprise buyers",
                confidence=0.8,
                risk_if_wrong="Locale targeting may be wrong",
            )
        ],
        risks=[
            CaseRisk(
                title="Over-optimising for one engine",
                description="Perplexity-specific tactics may not transfer",
                severity="medium",
                likelihood="medium",
            )
        ],
        opportunities=[
            CaseOpportunity(
                title="FAQ schema rollout",
                description="Add FAQPage markup to support pages",
                impact=0.7,
                effort=0.3,
            )
        ],
        recommendations=[
            CaseRecommendation(
                title="Ship Organisation + FAQ schema",
                rationale="Deterministic audit gaps align with citation research",
                priority="high",
                impact=0.75,
                effort=0.35,
                confidence=0.8,
                priority_score=0.72,
                evidence_refs=["ev.seo.score", "ev.research.mention"],
                suggested_fix="Add JSON-LD templates to layout",
            )
        ],
        models_used=[
            CaseModelUsed(
                provider_code="anthropic",
                model_code="claude-sonnet",
                role="specialist",
                request_count=2,
                cost_usd_micros=8000,
                latency_ms=600,
            )
        ],
        tools_used=[
            CaseToolUsed(
                tool_name="seo_engine",
                purpose="deterministic audit",
                invocation_count=1,
                latency_ms=200,
            )
        ],
    )


def test_intelligence_case_typed_contract() -> None:
    case = _sample_case("org-1", "ws-1")
    assert case.organization_id == case.organisation_id == "org-1"
    payload = case.to_dict()
    assert payload["case_id"] == case.case_id
    assert payload["organization_id"] == "org-1"
    assert payload["cost"] == {"usd_micros": 12500}
    assert payload["latency"] == {"ms": 840}
    assert len(payload["evidence"]) == 2
    assert payload["evidence"][0]["kind"] == "deterministic"
    assert payload["recommendations"][0]["evidence_refs"] == [
        "ev.seo.score",
        "ev.research.mention",
    ]
    # Collections stay lists of typed shapes — not nested opaque blobs
    assert isinstance(payload["context"], list)
    assert isinstance(payload["observations"], list)
    assert isinstance(payload["hypotheses"], list)


def test_intelligence_case_record_has_no_jsonb() -> None:
    from sqlalchemy import inspect

    for model in (IntelligenceCaseRecord, IntelligenceCaseEvidence):
        for column in inspect(model).columns:
            assert "json" not in type(column.type).__name__.lower()


@pytest.mark.skipif(not _can_connect(), reason="PostgreSQL not available")
def test_intelligence_case_repository_roundtrip() -> None:
    engine = create_engine(_database_url())
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = SessionLocal()
    try:
        org = db.scalar(select(Organisation).limit(1))
        workspace = db.scalar(select(Workspace).limit(1))
        if org is None or workspace is None:
            pytest.skip("Seed organisation/workspace required")

        case = _sample_case(org.id, workspace.id)
        repo = IntelligenceCaseRepository(db)
        saved = repo.save(case)
        assert saved.case_id == case.case_id
        assert saved.organization_id == org.id
        assert len(saved.evidence) == 2
        assert saved.evidence[0].related_urls == ["https://example.com/"]
        assert saved.agent_findings[0].claims == [
            "FAQ pages lack FAQPage markup",
            "Organisation schema incomplete",
        ]
        assert saved.recommendations[0].evidence_refs == [
            "ev.seo.score",
            "ev.research.mention",
        ]
        assert saved.hypotheses[0].supporting_evidence_codes == ["ev.seo.score"]
        assert saved.models_used[0].provider_code == "anthropic"
        assert saved.tools_used[0].tool_name == "seo_engine"
        assert saved.cost_usd_micros == 12500
        assert saved.latency_ms == 840

        loaded = repo.get(saved.case_id)
        assert loaded is not None
        assert loaded.to_dict()["objective"] == case.objective

        row = db.get(IntelligenceCaseRecord, saved.case_id)
        assert row is not None
        assert len(row.evidence_items) == 2
        assert row.evidence_items[0].value_number == 68.0
    finally:
        db.close()
