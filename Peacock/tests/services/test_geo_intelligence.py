from __future__ import annotations

import pytest

from geo_intelligence import (
    ENGINE_META,
    PeacockAIGateway,
    ProviderResponse,
    build_platform_recommendations,
    default_simulated_responses,
    extract_geo_intelligence,
    run_geo_intelligence,
)


def _simulated_responses(brand: str, competitors: list[str]) -> list[ProviderResponse]:
    return [
        ProviderResponse(
            engine_code=code,
            engine_name=ENGINE_META[code]["name"],
            provider_code=ENGINE_META[code]["provider"],
            content=content,
            simulated=True,
        )
        for code, content in default_simulated_responses(brand, competitors).items()
    ]


@pytest.mark.asyncio
async def test_gateway_broadcast_falls_back_to_simulated_without_llm_gateway() -> None:
    gateway = PeacockAIGateway(llm_gateway=None)
    responses = await gateway.broadcast(
        organisation_id="org",
        research_prompt="test prompt",
        engine_codes=list(ENGINE_META.keys()),
        simulated_responses=default_simulated_responses("Acme", ["Semrush"]),
    )
    assert len(responses) == len(ENGINE_META)
    assert all(r.simulated for r in responses)
    assert all(r.content for r in responses)
    assert {r.engine_code for r in responses} == set(ENGINE_META.keys())


@pytest.mark.asyncio
async def test_gateway_broadcast_never_raises_on_unknown_engine_code() -> None:
    gateway = PeacockAIGateway(llm_gateway=None)
    responses = await gateway.broadcast(
        organisation_id="org",
        research_prompt="test prompt",
        engine_codes=["chatgpt", "not-a-real-plugin"],
        simulated_responses={},
    )
    assert {r.engine_code for r in responses} == {"chatgpt"}


def test_extract_geo_intelligence_finds_signals_across_providers() -> None:
    responses = _simulated_responses("Acme", ["Semrush", "Ahrefs"])

    result = extract_geo_intelligence(
        client_brand="Acme",
        competitors=["Semrush", "Ahrefs"],
        site_topics=["seo audits", "keyword research"],
        responses=responses,
    )

    assert result.keywords
    assert any(k.phrase == "acme" for k in result.keywords)
    assert any(e.name == "Acme" and e.kind == "client" for e in result.entities)
    assert {e.name for e in result.competitor_mentions} == {"semrush", "ahrefs"}
    assert result.questions
    assert result.citations
    assert len(result.terminology_by_engine) == len(responses)
    # Terminology should not just repeat the brand name for every engine.
    assert not any(t.top_terms == ["acme"] for t in result.terminology_by_engine if t.top_terms)


def test_build_platform_recommendations_never_claims_guaranteed_ranking() -> None:
    responses = _simulated_responses("Acme", ["Semrush"])
    extraction = extract_geo_intelligence(
        client_brand="Acme", competitors=["Semrush"], site_topics=[], responses=responses
    )
    recommendations = build_platform_recommendations(
        client_brand="Acme", responses=responses, extraction=extraction
    )
    assert len(recommendations) == len(responses)
    for rec in recommendations:
        assert rec.opportunities
        joined = " ".join(rec.opportunities).lower()
        assert "guarantee" not in joined
        assert rec.signal_strength in {"low", "medium", "high"}


@pytest.mark.asyncio
async def test_run_geo_intelligence_end_to_end_without_llm_gateway() -> None:
    report = await run_geo_intelligence(llm_gateway=None, organisation_id="org", client_brand="Acme")
    assert report.client_brand == "Acme"
    assert len(report.provider_responses) == len(ENGINE_META)
    assert report.extraction.keywords
    assert len(report.recommendations) == len(ENGINE_META)
    assert "not a guarantee" in report.disclaimer.lower()
