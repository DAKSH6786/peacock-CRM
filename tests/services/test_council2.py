"""Peacock Council 2.0 — opposing roles, five-round debate, no CoT storage."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from council2 import (
    COUNCIL_ROLES,
    DEBATE_ROUNDS,
    FORBIDDEN_STORAGE_FIELDS,
    STORED_ARTIFACT_KINDS,
    ContextFact,
    Council2Service,
    Council2Spec,
    CouncilBrief,
    assert_no_open_opinion_prompt,
    run_council_debate,
)
from db_models import Organisation, Website, Workspace
from db_models.base import new_uuid
from db_models.council2 import C2Claim, Council2Session


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


def test_roles_and_rounds() -> None:
    assert set(COUNCIL_ROLES) == {
        "seo_researcher",
        "geo_researcher",
        "business_strategist",
        "competitor_analyst",
        "evidence_reviewer",
        "sceptic",
        "risk_analyst",
    }
    assert [r[0] for r in DEBATE_ROUNDS] == [1, 2, 3, 4, 5]
    assert set(STORED_ARTIFACT_KINDS) == {
        "claim",
        "evidence",
        "counterargument",
        "confidence",
        "decision",
    }


def test_rejects_what_do_you_think() -> None:
    with pytest.raises(ValueError, match="Open opinion prompts are rejected"):
        assert_no_open_opinion_prompt("What do you think?")
    with pytest.raises(ValueError, match="Open opinion prompts are rejected"):
        run_council_debate(
            CouncilBrief(
                decision_question="What do you think about expanding to EU?",
                client_brand="Acme",
            )
        )


def test_five_round_debate_stores_only_allowed_artifacts() -> None:
    result = run_council_debate(
        CouncilBrief(
            decision_question="Should we invest in a proprietary GEO benchmark study?",
            client_brand="Acme",
            context_summary="Major capital decision with competitive stakes.",
            facts=[
                ContextFact(
                    label="citation_gap",
                    statement="Rivals earn more AI citations on benchmark queries.",
                    polarity="support",
                    strength=0.8,
                ),
                ContextFact(
                    label="cost_risk",
                    statement="Study requires significant research budget.",
                    polarity="oppose",
                    strength=0.6,
                ),
            ],
            model_by_role={"sceptic": "claude-critic", "geo_researcher": "gpt-geo"},
        )
    )
    assert result.open_opinion_prompts_rejected is True
    assert result.chain_of_thought_not_stored is True
    assert len(result.rounds) == 5
    assert len(result.agents) == 7
    assert all(a.open_opinion_prompt_rejected for a in result.agents)
    assert all("what do you think" not in a.role_mandate.lower() for a in result.agents)
    assert result.claims and result.evidence and result.decisions
    assert result.disagreements  # sceptic/risk vs supporters expected
    assert result.evidence_requests
    assert 0.0 <= result.final_confidence <= 1.0
    serialized = result.to_dict()
    for field in FORBIDDEN_STORAGE_FIELDS:
        assert field not in serialized
        # Nested dicts must not carry CoT payload keys either
        assert field not in serialized.get("agents", [{}])[0]
    assert "claims" in serialized and "decisions" in serialized
    # Boolean flag about CoT policy is allowed; actual CoT payloads are not
    assert serialized["chain_of_thought_not_stored"] is True
    assert "hidden_reasoning" not in serialized
    assert "private_scratchpad" not in serialized


def test_opposing_roles_produce_stance_diversity() -> None:
    result = run_council_debate(
        CouncilBrief(
            decision_question="Launch aggressive content refresh across 40 URLs?",
            client_brand="Acme",
            facts=[
                ContextFact(
                    label="decay",
                    statement="Many pages show decaying impressions.",
                    polarity="support",
                    strength=0.7,
                )
            ],
        )
    )
    stances = {c.stance for c in result.claims if c.round_number == 1}
    # With sceptic + risk + supporters we expect more than one stance
    assert len(stances) >= 2


@pytest.mark.skipif(not _can_connect(), reason="PostgreSQL not available")
def test_council2_persists_without_cot() -> None:
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
            name=f"c2-{suffix}",
            slug=f"c2-{suffix}",
        )
        db.add(workspace)
        db.flush()
        website = Website(
            id=new_uuid(),
            organisation_id=org.id,
            workspace_id=workspace.id,
            name=f"Site {suffix}",
            primary_domain=f"c2-{suffix}.com",
            root_url=f"https://c2-{suffix}.com",
        )
        db.add(website)
        db.commit()

        report = Council2Service(db).run_session(
            organisation_id=org.id,
            workspace_id=workspace.id,
            spec=Council2Spec(
                website_id=website.id,
                name=f"Council {suffix}",
                brief=CouncilBrief(
                    decision_question="Approve GEO Lab experiment budget?",
                    client_brand="Acme",
                    facts=[
                        ContextFact(
                            label="upside",
                            statement="Controlled experiments may improve citation rate.",
                            polarity="support",
                            strength=0.75,
                        )
                    ],
                ),
            ),
        )
        assert report.result.chain_of_thought_not_stored is True
        row = db.scalar(
            select(Council2Session).where(Council2Session.id == report.session_id)
        )
        assert row is not None
        assert row.open_opinion_prompts_rejected is True
        assert row.chain_of_thought_not_stored is True
        assert row.round_count == 5
        claims = list(
            db.scalars(
                select(C2Claim).where(C2Claim.session_id == report.session_id)
            ).all()
        )
        assert claims
    finally:
        db.close()
