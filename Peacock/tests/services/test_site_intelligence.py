"""Tests for the Peacock Site Intelligence engine.

These tests build ``StoredPage``/``StoredCrawl`` fixtures directly (no
network access) so they run offline and deterministically, while the real
end-to-end network path is exercised manually against a public site (see
the PR description / task report).
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from crawler.policy import CrawlPolicy
from crawler.ports import CrawlProgress
from crawler.store import StoredCrawl, StoredPage
from geo_intelligence.gateway import ENGINE_META
from geo_intelligence.models import EntityMention, GeoExtractionResult, ProviderResponse

from site_intelligence.geo_score import compute_page_geo_score
from site_intelligence.impact import build_top_actions, peacock_impact_score, score_page_opportunities
from site_intelligence.information_gain import detect_information_gain_signals, score_information_gain
from site_intelligence.llm_geo_score import score_llm_geo
from site_intelligence.llm_keyword_map import build_llm_keyword_map
from site_intelligence.models import DATA_UNAVAILABLE
from site_intelligence.page_scoring import build_page_opportunity


def _make_page(
    url: str = "https://example.com/",
    *,
    title: str | None = "Example — A Practical Guide",
    meta_description: str | None = "A practical guide to Example, covering pricing, features, and FAQs.",
    h1: list[str] | None = None,
    h2: list[str] | None = None,
    body_text: str = "",
    word_count: int = 500,
    external_links: list[str] | None = None,
    internal_links: list[str] | None = None,
    schema: list[dict] | None = None,
    status_code: int = 200,
    robots: str | None = None,
    is_js_heavy: bool = False,
    viewport_meta: str | None = "width=device-width, initial-scale=1.0",
) -> StoredPage:
    return StoredPage(
        id=str(uuid4()),
        url=url,
        canonical=url,
        status_code=status_code,
        title=title,
        meta_description=meta_description,
        h1=h1 or ["Example — A Practical Guide"],
        h2=h2 or ["What is Example?", "How does Example work?"],
        h3=[],
        body_text=body_text,
        word_count=word_count,
        internal_links=internal_links or [],
        external_links=external_links or [],
        images=[],
        schema=schema or [],
        robots=robots,
        indexability="indexable" if not (robots and "noindex" in robots) else "noindex",
        crawl_depth=0,
        content_hash=None,
        content_type="text/html",
        language="en",
        is_js_heavy=is_js_heavy,
        redirect_chain=[],
        fetch_mode="httpx",
        status="fetched",
        viewport_meta=viewport_meta,
    )


def _make_crawl(pages: list[StoredPage]) -> StoredCrawl:
    return StoredCrawl(
        id=str(uuid4()),
        organisation_id="test",
        workspace_id="test",
        website_id=None,
        seed_url=pages[0].url if pages else "https://example.com/",
        status="completed",
        policy=CrawlPolicy(),
        progress=CrawlProgress(pages_crawled=len(pages), max_pages=len(pages), status="completed"),
        pages={p.url: p for p in pages},
    )


def test_information_gain_detects_real_patterns_not_invented_ones() -> None:
    rich_text = (
        "Our data shows that 73% of teams struggle with this. We surveyed 500 companies in 2025 "
        "and found original patterns. According to our CEO, this is a new framework we built."
    )
    thin_text = "What is a widget? A widget is a small part of a machine. This is the ultimate guide."

    penalties_rich, rewards_rich, evidence_rich = detect_information_gain_signals(rich_text)
    penalties_thin, rewards_thin, evidence_thin = detect_information_gain_signals(thin_text)

    assert rewards_rich  # original data / expert opinion signals detected
    assert evidence_rich
    assert penalties_thin  # generic_duplication / common_definitions detected
    assert evidence_thin

    score_rich, _signals_rich, _e = score_information_gain(rich_text)
    score_thin, _signals_thin, _e2 = score_information_gain(thin_text)
    assert score_rich > score_thin


def test_information_gain_penalizes_near_duplicate_only_when_competitor_text_supplied() -> None:
    text = "This is our exact page content about widgets and gadgets for enterprise teams."
    penalties_no_comp, _rewards, _evidence = detect_information_gain_signals(text)
    assert "near_identical_competitor_coverage" not in penalties_no_comp

    penalties_with_comp, _rewards2, _evidence2 = detect_information_gain_signals(text, competitor_text=text)
    assert "near_identical_competitor_coverage" in penalties_with_comp


def test_geo_score_breakdown_has_seven_transparent_factors() -> None:
    page = _make_page(
        body_text=(
            "What is Example? Example is a platform for testing. How does Example work? "
            "It processes data. Our data shows 42% improvement in 2025. Sources: see references below."
        ),
        h2=["What is Example?", "How does Example work?"],
        external_links=["https://www.reuters.com/example-article"],
        schema=[{"@type": "FAQPage"}, {"@type": "Organization"}],
    )
    breakdown = compute_page_geo_score(page, site_key_terms=["example", "platform"])

    assert 0 <= breakdown.geo_score <= 100
    factor_labels = {
        breakdown.entity_authority.label,
        breakdown.citation_readiness.label,
        breakdown.answerability.label,
        breakdown.evidence.label,
        breakdown.topical_coverage.label,
        breakdown.technical_ai_accessibility.label,
        breakdown.brand_authority.label,
    }
    assert factor_labels == {
        "Entity Authority",
        "Citation Readiness",
        "Answerability",
        "Evidence",
        "Topical Coverage",
        "Technical AI Accessibility",
        "Brand Authority",
    }
    for factor_score in (
        breakdown.entity_authority,
        breakdown.citation_readiness,
        breakdown.answerability,
        breakdown.evidence,
        breakdown.topical_coverage,
        breakdown.technical_ai_accessibility,
        breakdown.brand_authority,
    ):
        assert factor_score.factors, f"{factor_score.label} must expose its evidence factors"
        for f in factor_score.factors:
            assert f.evidence  # every factor is explainable


def test_page_opportunity_flags_missing_title_as_critical() -> None:
    page = _make_page(title=None, meta_description=None, h1=[], word_count=50)
    opportunity, _geo = build_page_opportunity(
        page, site_key_terms=[], competitor_text=None, competitor_summary=DATA_UNAVAILABLE
    )
    assert opportunity.priority == "Critical"
    assert any("title" in w.lower() for w in opportunity.whats_wrong)
    assert opportunity.competitor_doing_better == DATA_UNAVAILABLE
    assert opportunity.confidence in {"high", "medium", "experimental"}


def test_peacock_impact_score_formula_matches_spec() -> None:
    score = peacock_impact_score(
        visibility_opportunity=0.5,
        business_intent=0.8,
        competitive_gap=0.6,
        fix_confidence=0.9,
        implementation_difficulty=2.0,
    )
    expected = min(100.0, (0.5 * 0.8 * 0.6 * 0.9 / 2.0) * 100.0)
    assert score == round(expected, 2)


def test_top_actions_are_ranked_by_impact_descending() -> None:
    good_page = _make_page(url="https://example.com/good", word_count=1200, title="Good Page — Example")
    bad_page = _make_page(url="https://example.com/bad", title=None, meta_description=None, h1=[], word_count=40)
    pages = [
        build_page_opportunity(p, site_key_terms=[], competitor_text=None, competitor_summary=DATA_UNAVAILABLE)[0]
        for p in (good_page, bad_page)
    ]
    score_page_opportunities(
        pages,
        depth_by_url={p.url: 0 for p in (good_page, bad_page)},
        page_tokens_by_url={p.url: set() for p in (good_page, bad_page)},
        missing_topics=[],
    )
    extraction = GeoExtractionResult(
        keywords=[], entities=[], questions=[], citations=[], competitor_mentions=[],
        terminology_by_engine=[], top_brand_topics=[], missing_topics=[],
    )
    actions = build_top_actions(pages=pages, keyword_map=_empty_keyword_map(), extraction=extraction, recommendations=[])
    scores = [a.impact_score for a in actions]
    assert scores == sorted(scores, reverse=True)
    assert [a.rank for a in actions] == list(range(1, len(actions) + 1))


def _empty_keyword_map():
    from site_intelligence.models import LlmKeywordMap

    return LlmKeywordMap(
        entries=[], universal_terms=[], platform_specific_terms={}, missing_semantic_entities=[],
        competitive_association_gaps=[],
    )


def test_llm_geo_score_never_computed_for_simulated_response() -> None:
    response = ProviderResponse(
        engine_code="chatgpt", engine_name="ChatGPT", provider_code="openai",
        content="", simulated=True,
    )
    extraction = GeoExtractionResult(
        keywords=[], entities=[], questions=[], citations=[], competitor_mentions=[],
        terminology_by_engine=[], top_brand_topics=[], missing_topics=[],
    )
    result = score_llm_geo(response, brand="Acme", extraction=extraction)
    assert result.available is False
    assert result.score is None
    assert result.reason_unavailable and "no live api key" in result.reason_unavailable.lower()


def test_llm_geo_score_computed_from_real_response_content() -> None:
    response = ProviderResponse(
        engine_code="chatgpt", engine_name="ChatGPT", provider_code="openai",
        content="Acme is a great platform. What is Acme? Acme helps teams track visibility.",
        simulated=False,
    )
    extraction = GeoExtractionResult(
        keywords=[], entities=[EntityMention(name="Acme", kind="client", frequency=2, engine_codes=["chatgpt"])],
        questions=[], citations=[], competitor_mentions=[], terminology_by_engine=[], top_brand_topics=[],
        missing_topics=[],
    )
    result = score_llm_geo(response, brand="Acme", extraction=extraction)
    assert result.available is True
    assert result.score is not None
    assert result.brand_mentioned is True


def test_llm_keyword_map_builds_universal_and_platform_specific_terms() -> None:
    from geo_intelligence.models import KeywordSignal

    extraction = GeoExtractionResult(
        keywords=[
            KeywordSignal(phrase="visibility", frequency=10, engine_codes=list(ENGINE_META.keys())),
            KeywordSignal(phrase="deepseek only term", frequency=2, engine_codes=["deepseek"]),
        ],
        entities=[], questions=[], citations=[], competitor_mentions=[], terminology_by_engine=[],
        top_brand_topics=[], missing_topics=[],
    )
    keyword_map = build_llm_keyword_map(
        extraction=extraction, responses=[], site_text="some unrelated site text", client_brand="Acme"
    )
    assert "visibility" in keyword_map.universal_terms
    assert any("deepseek only term" in terms for terms in keyword_map.platform_specific_terms.values())
