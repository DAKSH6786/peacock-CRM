"""Probabilistic AI Visibility — controlled repetitions, not single-shot truth."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from db_models import Organisation, Website, Workspace
from db_models.base import new_uuid
from geo_engine import (
    HARD_MAX_REPETITIONS,
    CampaignSpec,
    ProbeCellSpec,
    ProbabilisticVisibilityService,
    RateLimitPolicy,
)
from geo_engine.probabilistic_sampler import validate_repetitions
from geo_engine.probabilistic_stats import (
    bernoulli_estimate,
    peacock_visibility_confidence,
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


def test_single_shot_never_gets_high_confidence() -> None:
    score, label = peacock_visibility_confidence(
        sample_size=1,
        engine_count=1,
        prompt_count=1,
        period_count=1,
        mean_variance=0.0,
        mean_engine_disagreement=0.0,
        mean_temporal_volatility=0.0,
    )
    assert label == "LOW"
    assert score <= 0.45


def test_bernoulli_distribution_fields() -> None:
    est = bernoulli_estimate(37, 50)
    assert abs(est.probability - 0.74) < 1e-9
    assert est.sample_size == 50
    assert est.variance == pytest.approx(0.74 * 0.26)
    assert 0.0 <= est.ci_low <= est.probability <= est.ci_high <= 1.0


def test_repetition_hard_ceiling_blocks_abuse() -> None:
    with pytest.raises(ValueError, match="hard ceiling"):
        validate_repetitions(HARD_MAX_REPETITIONS + 1, max_repetitions=HARD_MAX_REPETITIONS)


@pytest.mark.asyncio
@pytest.mark.skipif(not _can_connect(), reason="PostgreSQL not available")
async def test_campaign_computes_distributions_not_single_shot() -> None:
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
            name=f"vis-{suffix}",
            slug=f"vis-{suffix}",
        )
        db.add(workspace)
        db.flush()
        website = Website(
            id=new_uuid(),
            organisation_id=org.id,
            workspace_id=workspace.id,
            name=f"Site {suffix}",
            primary_domain=f"example-{suffix}.com",
            root_url=f"https://example-{suffix}.com",
        )
        db.add(website)
        db.commit()

        service = ProbabilisticVisibilityService(db)
        campaign = service.create_campaign(
            organisation_id=org.id,
            workspace_id=workspace.id,
            spec=CampaignSpec(
                website_id=website.id,
                name="Strategic prompt panel",
                brand_name="Peacock One",
                competitors=["competitor_a", "competitor_b"],
                rate_limit=RateLimitPolicy(
                    target_repetitions=5,
                    max_repetitions=10,
                    max_calls_per_minute=30,
                    min_interval_ms=500,
                    max_concurrent=1,
                    max_total_calls=200,
                ),
                cells=[
                    ProbeCellSpec(
                        prompt_text="best enterprise SEO platform",
                        engine_code="chatgpt",
                        location_code="us",
                        persona_code="seo_lead",
                        config_code="temp_0.2",
                        temperature=0.2,
                        time_bucket="2026-q3",
                        target_repetitions=5,
                    ),
                    ProbeCellSpec(
                        prompt_text="best enterprise SEO platform",
                        engine_code="perplexity",
                        location_code="us",
                        persona_code="seo_lead",
                        time_bucket="2026-q3",
                        target_repetitions=5,
                    ),
                    ProbeCellSpec(
                        prompt_text="generative visibility intelligence tools",
                        engine_code="gemini",
                        location_code="uk",
                        persona_code="cmo",
                        time_bucket="2026-q3",
                        target_repetitions=5,
                    ),
                ],
            ),
        )

        card = await service.run_campaign(
            campaign_id=campaign.id,
            organisation_id=org.id,
            use_mock=True,
        )
        assert card.observation_count == 15
        assert card.engine_count == 3
        assert card.prompt_count == 2
        assert 0.0 <= card.brand_mention_probability <= 1.0
        assert 0.0 <= card.citation_probability <= 1.0
        assert 0.0 <= card.top3_probability <= 1.0
        assert "competitor_a" in card.competitor_probabilities or card.competitor_probabilities
        assert card.measurement_confidence in {"LOW", "MEDIUM", "HIGH"}
        assert card.single_shot_rejected is True
        assert any(d.metric_key == "brand_mention_probability" for d in card.distributions)
        for dist in card.distributions:
            assert dist.sample_size == card.observation_count
            assert "variance" in dist.to_dict()
            assert "ci_low" in dist.to_dict()
            assert "engine_disagreement" in dist.to_dict()
            assert "temporal_volatility" in dist.to_dict()

        payload = card.to_dict()
        assert "AI Visibility Score" in payload["summary"] or payload["ai_visibility_score"] >= 0
        assert payload["based_on"]["observations"] == 15
        assert payload["based_on"]["engines"] == 3
        assert payload["single_shot_rejected"] is True
    finally:
        db.close()
