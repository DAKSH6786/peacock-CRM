"""Share of Answer — multi-indicator influence, not token-only Share of Voice."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from db_models import Organisation, Website, Workspace
from db_models.base import new_uuid
from db_models.share_of_answer import SOA_INDICATORS, SoaBrandScore
from share_of_answer import ShareOfAnswerService
from share_of_answer.extractor import AnswerDocument, extract_entity_indicators
from share_of_answer.models import AnswerObservationSpec, ShareOfAnswerSpec
from share_of_answer.scoring import (
    EntityIndicatorReading,
    aggregate_brand_scores,
    compute_influence,
    normalise_share_of_answer,
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


def test_soa_indicators_cover_spec() -> None:
    assert set(SOA_INDICATORS) == {
        "mention",
        "position",
        "recommendation_strength",
        "answer_space",
        "citation_ownership",
        "semantic_prominence",
        "positive_claims",
        "negative_claims",
        "neutral_claims",
        "comparison_outcome",
    }


def test_token_span_alone_does_not_equal_influence() -> None:
    """A brand with only high token span and no other signals gets zero influence."""
    token_heavy = EntityIndicatorReading(
        entity_name="VerboseCo",
        mention=False,
        token_span_ratio=0.9,
        recommendation_strength=0.0,
        answer_space=0.0,
        citation_ownership=0.0,
        semantic_prominence=0.0,
        comparison_outcome="absent",
    )
    breakdown = compute_influence(token_heavy)
    assert breakdown.influence == 0.0
    assert breakdown.token_span_used_as_sole_signal is True

    strong = EntityIndicatorReading(
        entity_name="BrandA",
        mention=True,
        position=1,
        recommendation_strength=0.95,
        answer_space=0.4,
        citation_ownership=0.8,
        semantic_prominence=0.85,
        positive_claims=4,
        negative_claims=0,
        neutral_claims=1,
        comparison_outcome="win",
        token_span_ratio=0.15,  # fewer tokens than VerboseCo
    )
    strong_inf = compute_influence(strong).influence
    assert strong_inf > 0.5


def test_enterprise_crm_cluster_normalises_to_percentages() -> None:
    """Example shape: Brand A / Brand B / Client shares."""
    obs = [
        [
            EntityIndicatorReading(
                entity_name="Brand A",
                mention=True,
                position=1,
                recommendation_strength=0.9,
                answer_space=0.35,
                citation_ownership=0.7,
                semantic_prominence=0.8,
                positive_claims=5,
                negative_claims=0,
                neutral_claims=1,
                comparison_outcome="win",
                token_span_ratio=0.25,
            ),
            EntityIndicatorReading(
                entity_name="Brand B",
                mention=True,
                position=2,
                recommendation_strength=0.75,
                answer_space=0.30,
                citation_ownership=0.55,
                semantic_prominence=0.65,
                positive_claims=3,
                negative_claims=1,
                neutral_claims=1,
                comparison_outcome="tie",
                token_span_ratio=0.40,  # more tokens than Brand A
            ),
            EntityIndicatorReading(
                entity_name="Client",
                is_client=True,
                mention=True,
                position=4,
                recommendation_strength=0.35,
                answer_space=0.12,
                citation_ownership=0.2,
                semantic_prominence=0.3,
                positive_claims=1,
                negative_claims=1,
                neutral_claims=2,
                comparison_outcome="lose",
                token_span_ratio=0.35,
            ),
        ]
    ]
    brands = aggregate_brand_scores(entity_readings_per_observation=obs)
    by_name = {b.entity_name: b for b in brands}
    assert by_name["Brand A"].share_of_answer > by_name["Brand B"].share_of_answer
    assert by_name["Client"].share_of_answer < by_name["Brand B"].share_of_answer
    total = sum(b.share_of_answer for b in brands)
    assert abs(total - 100.0) < 0.1

    # Token-only ranking would favour Brand B; multi-indicator favours Brand A
    assert by_name["Brand B"].token_only_share > by_name["Brand A"].token_only_share
    assert by_name["Brand A"].share_of_answer > by_name["Brand B"].share_of_answer
    assert by_name["Brand A"].token_vs_influence_gap != 0.0


def test_normalise_share_of_answer() -> None:
    shares = normalise_share_of_answer({"A": 0.34, "B": 0.28, "Client": 0.11})
    assert abs(sum(shares.values()) - 100.0) < 1e-6
    assert shares["A"] > shares["B"] > shares["Client"]


def test_heuristic_extractor_tracks_all_indicators() -> None:
    doc = AnswerDocument(
        prompt_text="best enterprise CRM platforms",
        engine_code="chatgpt",
        raw_excerpt=(
            "1. Brand A is the strongest overall recommendation and leads on scale "
            "with documentation at https://branda.example/docs.\n"
            "2. Brand B is a solid alternative for analytics.\n"
            "3. Client appears as a niche option with limited coverage and drawbacks."
        ),
    )
    readings = extract_entity_indicators(
        doc,
        client_brand="Client",
        competitor_brands=["Brand A", "Brand B"],
    )
    by_name = {r.entity_name: r for r in readings}

    assert by_name["Brand A"].mention is True
    assert by_name["Brand B"].mention is True
    assert by_name["Client"].mention is True
    assert by_name["Client"].is_client is True

    assert by_name["Brand A"].position == 1
    assert by_name["Brand B"].position == 2
    assert by_name["Client"].position == 3

    assert by_name["Brand A"].recommendation_strength > by_name["Client"].recommendation_strength
    assert by_name["Brand A"].citation_ownership > 0
    assert by_name["Brand A"].semantic_prominence > by_name["Client"].semantic_prominence
    assert by_name["Brand A"].positive_claims >= 1
    assert by_name["Client"].negative_claims >= 1
    assert by_name["Brand A"].comparison_outcome == "win"
    assert by_name["Client"].answer_space > 0

    brands = aggregate_brand_scores(entity_readings_per_observation=[readings])
    assert brands[0].entity_name == "Brand A"
    assert abs(sum(b.share_of_answer for b in brands) - 100.0) < 0.1


def test_unmentioned_brand_is_absent() -> None:
    doc = AnswerDocument(
        prompt_text="crm",
        engine_code="chatgpt",
        raw_excerpt="Brand A is recommended. Brand B is comparable.",
    )
    readings = extract_entity_indicators(
        doc,
        client_brand="Client",
        competitor_brands=["Brand A", "Brand B"],
    )
    client = next(r for r in readings if r.entity_name == "Client")
    assert client.mention is False
    assert client.comparison_outcome == "absent"
    assert compute_influence(client).influence == 0.0


@pytest.mark.skipif(not _can_connect(), reason="PostgreSQL not available")
def test_share_of_answer_persists_multi_indicator_report() -> None:
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
            name=f"soa-{suffix}",
            slug=f"soa-{suffix}",
        )
        db.add(workspace)
        db.flush()
        website = Website(
            id=new_uuid(),
            organisation_id=org.id,
            workspace_id=workspace.id,
            name=f"Site {suffix}",
            primary_domain=f"soa-{suffix}.com",
            root_url=f"https://soa-{suffix}.com",
        )
        db.add(website)
        db.commit()

        report = ShareOfAnswerService(db).analyse(
            organisation_id=org.id,
            workspace_id=workspace.id,
            spec=ShareOfAnswerSpec(
                website_id=website.id,
                name=f"Enterprise CRM SOA {suffix}",
                query_cluster="Enterprise CRM",
                client_brand="Client",
                competitor_brands=["Brand A", "Brand B"],
                observations=[
                    AnswerObservationSpec(
                        prompt_text="best enterprise CRM platforms",
                        engine_code="chatgpt",
                        raw_excerpt=(
                            "Top enterprise CRM options include Brand A for scale, "
                            "Brand B for analytics, and Client for emerging teams. "
                            "Brand A is the strongest overall recommendation."
                        ),
                    ),
                    AnswerObservationSpec(
                        prompt_text="enterprise CRM comparison shortlist",
                        engine_code="perplexity",
                        raw_excerpt=(
                            "Brand B leads on insights. Brand A remains widely cited. "
                            "Client appears as a niche alternative."
                        ),
                    ),
                ],
            ),
        )

        assert report.token_count_alone_rejected is True
        assert report.methodology == "multi_indicator"
        assert report.query_cluster == "Enterprise CRM"
        assert len(report.brands) == 3
        assert abs(sum(b.share_of_answer for b in report.brands) - 100.0) < 0.2

        client = next(b for b in report.brands if b.is_client or b.entity_name == "Client")
        assert 0.0 <= client.share_of_answer <= 100.0

        rows = list(
            db.scalars(
                select(SoaBrandScore).where(SoaBrandScore.analysis_id == report.analysis_id)
            ).all()
        )
        assert len(rows) == 3
        for row in rows:
            assert 0.0 <= row.mention_rate <= 1.0
            assert row.observation_sample_size == 2

        with pytest.raises(ValueError, match="Token count alone"):
            ShareOfAnswerService(db).analyse(
                organisation_id=org.id,
                workspace_id=workspace.id,
                spec=ShareOfAnswerSpec(
                    website_id=website.id,
                    name="bad",
                    query_cluster="x",
                    client_brand="Client",
                    competitor_brands=["Brand A"],
                    observations=[
                        AnswerObservationSpec(
                            prompt_text="q",
                            engine_code="chatgpt",
                            raw_excerpt="Client Brand A",
                        )
                    ],
                    indicator_weights={"token_span": 1.0},
                ),
            )
    finally:
        db.close()
