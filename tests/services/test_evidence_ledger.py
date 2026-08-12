"""Evidence Ledger — typed graph + relational persistence."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from db_models import Organisation, Workspace
from evidence_ledger import (
    ClaimEvidencePointer,
    EvidenceType,
    EvidenceLedgerRepository,
    LedgerActionNode,
    LedgerEvidenceNode,
    LedgerFindingNode,
    LedgerOutcomeNode,
    LedgerRecommendationNode,
    SupportingValue,
    compute_freshness,
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


def test_evidence_types_cover_product_contract() -> None:
    assert {t.value for t in EvidenceType} == {
        "CRAWL",
        "SERP",
        "ANALYTICS",
        "SEARCH_CONSOLE",
        "BACKLINK",
        "AI_RESPONSE",
        "COMPETITOR_PAGE",
        "USER_DATA",
        "MODEL_INFERENCE",
        "EXTERNAL_SOURCE",
        "HISTORICAL_OUTCOME",
        "EXPERIMENT",
    }


def test_evidence_node_serialises_required_fields() -> None:
    observed = datetime(2026, 8, 1, tzinfo=UTC)
    node = LedgerEvidenceNode(
        evidence_type=EvidenceType.CRAWL,
        source="peacock_crawler",
        observed_at=observed,
        confidence=0.95,
        scope_kind="page",
        scope_ref="https://example.com/pricing",
        summary="Missing H1 on pricing page",
        supporting_value=SupportingValue(text="h1_missing", boolean=True),
        freshness_hours=24.0,
        freshness_score=0.9,
    )
    payload = node.to_dict()
    assert payload["evidence_type"] == "CRAWL"
    assert payload["source"] == "peacock_crawler"
    assert payload["timestamp"] == observed.isoformat()
    assert payload["freshness"] == {"hours": 24.0, "score": 0.9}
    assert payload["confidence"] == 0.95
    assert payload["scope"] == {"kind": "page", "ref": "https://example.com/pricing"}
    assert payload["supporting_value"]["boolean"] is True


def test_compute_freshness_decays_with_age() -> None:
    now = datetime(2026, 8, 12, tzinfo=UTC)
    hours, score = compute_freshness(now - timedelta(hours=168), now=now, half_life_hours=168.0)
    assert hours == 168.0
    assert abs(score - 0.5) < 1e-9


@pytest.mark.skipif(not _can_connect(), reason="PostgreSQL not available")
def test_evidence_graph_chain_roundtrip() -> None:
    engine = create_engine(_database_url())
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = SessionLocal()
    try:
        org = db.scalar(select(Organisation).limit(1))
        workspace = db.scalar(select(Workspace).limit(1))
        if org is None or workspace is None:
            pytest.skip("Seed organisation/workspace required")

        repo = EvidenceLedgerRepository(db)
        evidence = repo.record_evidence(
            organisation_id=org.id,
            workspace_id=workspace.id,
            node=LedgerEvidenceNode(
                evidence_type=EvidenceType.SEARCH_CONSOLE,
                source="gsc_connector",
                observed_at=datetime.now(UTC),
                confidence=0.9,
                scope_kind="query",
                scope_ref="peacock one seo",
                summary="Brand query CTR is 12%",
                supporting_value=SupportingValue(number=0.12, unit="ctr"),
            ),
        )
        finding = repo.record_finding(
            organisation_id=org.id,
            workspace_id=workspace.id,
            node=LedgerFindingNode(
                statement="Brand query CTR underperforms category peers",
                confidence=0.8,
                evidence_ids=[evidence.id or ""],
            ),
            evidence_ids=[evidence.id or ""],
        )
        recommendation = repo.record_recommendation(
            organisation_id=org.id,
            workspace_id=workspace.id,
            node=LedgerRecommendationNode(
                title="Expand brand SERP features",
                rationale="CTR gap is evidence-backed",
                priority="high",
                impact=0.7,
                effort=0.4,
                confidence=0.75,
                finding_ids=[finding.id or ""],
            ),
            finding_ids=[finding.id or ""],
        )
        action = repo.record_action(
            organisation_id=org.id,
            workspace_id=workspace.id,
            node=LedgerActionNode(
                title="Add FAQ schema to homepage",
                description="Ship Organisation + FAQ JSON-LD",
                owner_role="seo_lead",
                success_metric="brand_ctr",
                recommendation_ids=[recommendation.id or ""],
            ),
            recommendation_ids=[recommendation.id or ""],
        )
        outcome = repo.record_outcome(
            organisation_id=org.id,
            workspace_id=workspace.id,
            node=LedgerOutcomeNode(
                metric_key="brand_ctr",
                metric_value=0.15,
                baseline_value=0.12,
                target_value=0.18,
                observed_at=datetime.now(UTC),
                action_ids=[action.id or ""],
            ),
            action_ids=[action.id or ""],
        )
        pointer = repo.link_claim_to_evidence(
            organisation_id=org.id,
            workspace_id=workspace.id,
            pointer=ClaimEvidencePointer(
                claim_kind="seo_finding",
                claim_ref="finding.brand_ctr",
                claim_text="Brand CTR is weak",
                evidence_id=evidence.id or "",
                confidence=0.9,
            ),
        )

        assert pointer.evidence_id == evidence.id
        traced = repo.trace_from_evidence(evidence.id or "")
        assert traced is not None
        assert len(traced.evidences) == 1
        assert len(traced.findings) == 1
        assert len(traced.recommendations) == 1
        assert len(traced.actions) == 1
        assert len(traced.outcomes) == 1
        kinds = {(e.from_kind, e.to_kind) for e in traced.edges}
        assert ("evidence", "finding") in kinds
        assert ("finding", "recommendation") in kinds
        assert ("recommendation", "action") in kinds
        assert ("action", "outcome") in kinds
        assert outcome.metric_value == 0.15

        graph = repo.get_graph_for_workspace(
            organisation_id=org.id,
            workspace_id=workspace.id,
        )
        assert any(e.id == evidence.id for e in graph.evidences)
        assert any(p.claim_ref == "finding.brand_ctr" for p in graph.claim_pointers)
        assert graph.to_dict()["chain"] == [
            "evidence",
            "finding",
            "recommendation",
            "action",
            "outcome",
        ]
    finally:
        db.close()
