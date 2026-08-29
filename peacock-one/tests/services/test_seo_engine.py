"""Peacock SEO Engine tests — deterministic scoring from crawl fixtures."""

from __future__ import annotations

import pytest

from crawler.policy import CrawlPolicy
from crawler.ports import CrawlProgress
from crawler.store import StoredCrawl, StoredPage
from scoring import PEACOCK_SEO_WEIGHTS, ScoreResult, peacock_seo_score, weighted_score
from seo_engine import PeacockSeoEngine, SeoEngine
from seo_engine.adapters import MockPageSpeedProvider


def _page(**kwargs) -> StoredPage:
    defaults = dict(
        id="p1",
        url="https://example.com/",
        canonical="https://example.com/",
        status_code=200,
        title="Example Company Home Page Title Here",
        meta_description="A sufficiently long meta description that explains the page value for searchers.",
        h1=["Example Company"],
        h2=["Services"],
        h3=["Details"],
        body_text=" ".join(["content"] * 200) + " the and with for updated 2026",
        word_count=220,
        internal_links=["https://example.com/about"],
        external_links=[],
        images=[{"src": "https://example.com/logo.png", "alt": "Logo"}],
        schema=[{"@type": "Organization", "name": "Example"}],
        robots=None,
        indexability="indexable",
        crawl_depth=0,
        content_hash="abc",
        content_type="text/html",
        language="en",
        is_js_heavy=False,
        redirect_chain=["https://example.com/"],
        fetch_mode="httpx",
        status="fetched",
    )
    defaults.update(kwargs)
    return StoredPage(**defaults)  # type: ignore[arg-type]


def _crawl(pages: list[StoredPage], **kwargs) -> StoredCrawl:
    policy = CrawlPolicy(max_pages=50)
    crawl = StoredCrawl(
        id="crawl-1",
        organisation_id="org",
        workspace_id="ws",
        website_id="site-1",
        seed_url="https://example.com/",
        status="completed",
        policy=policy,
        progress=CrawlProgress(
            pages_discovered=len(pages),
            pages_crawled=len(pages),
            pages_failed=0,
            issues_found=0,
            max_pages=50,
            status="completed",
        ),
        robots_raw="User-agent: *\nAllow: /\n",
        sitemap_urls=["https://example.com/sitemap.xml"],
    )
    for page in pages:
        crawl.pages[page.url] = page
    for key, value in kwargs.items():
        setattr(crawl, key, value)
    return crawl


def test_peacock_seo_score_is_weighted_and_deterministic() -> None:
    sections = {
        code: ScoreResult(
            code=code,
            label=code,
            score=80.0,
            confidence=1.0,
            inputs_used=["x"],
        )
        for code in PEACOCK_SEO_WEIGHTS
    }
    overall = peacock_seo_score(sections)
    assert overall.code == "peacock_seo_score"
    assert overall.score == 80.0
    assert overall.confidence == 1.0
    # Same inputs → same score (no LLM nondeterminism)
    assert peacock_seo_score(sections).score == overall.score


def test_recommendation_priority_uses_weighted_score() -> None:
    assert weighted_score(0.9, 0.9, 0.1) > weighted_score(0.2, 0.5, 0.9)


@pytest.mark.asyncio
async def test_engine_produces_full_audit_structure() -> None:
    about = _page(
        id="p2",
        url="https://example.com/about",
        canonical="https://example.com/about",
        title="About Example Company Page Title",
        meta_description="About page description that is long enough for SEO checks and uniqueness.",
        h1=["About"],
        internal_links=["https://example.com/"],
        schema=[{"@type": "WebPage"}],
        content_hash="def",
        crawl_depth=1,
    )
    thin = _page(
        id="p3",
        url="https://example.com/thin",
        canonical=None,
        title="",
        meta_description=None,
        h1=[],
        h2=[],
        body_text="short",
        word_count=1,
        internal_links=[],
        images=[{"src": "https://example.com/x.png", "alt": ""}],
        schema=[],
        content_hash="thin",
        crawl_depth=2,
        is_orphan_candidate=True,
    )
    broken = _page(
        id="p4",
        url="https://example.com/broken",
        status_code=404,
        title=None,
        status="failed",
        word_count=0,
        body_text="",
        internal_links=[],
        images=[],
        schema=[],
        indexability="non_indexable_status",
    )
    crawl = _crawl([_page(), about, thin, broken])
    # create a broken internal link from home
    crawl.pages["https://example.com/"].internal_links.append("https://example.com/broken")

    engine = PeacockSeoEngine(pagespeed=MockPageSpeedProvider(performance_score=60))
    report = await engine.audit_crawl(crawl)

    assert report.peacock_seo_score.score >= 0
    assert report.peacock_seo_score.score <= 100
    assert report.peacock_seo_score.inputs_used
    assert set(report.scores) >= {
        "technical_seo",
        "content_quality",
        "on_page_seo",
        "internal_linking",
        "structured_data",
        "performance",
        "indexability",
    }
    for score in report.scores.values():
        assert 0 <= score.score <= 100
        assert 0 <= score.confidence <= 1
        assert isinstance(score.inputs_used, list)
        assert isinstance(score.major_positive_factors, list)
        assert isinstance(score.major_negative_factors, list)
        assert isinstance(score.recommended_actions, list)

    assert report.critical_issues or report.warnings
    assert report.recommendations
    for rec in report.recommendations:
        assert rec.priority
        assert 0 <= rec.impact <= 1
        assert 0 <= rec.effort <= 1
        assert 0 <= rec.confidence <= 1
        assert rec.reason
        assert rec.suggested_fix
        assert isinstance(rec.affected_pages, list)

    assert any(f.code == "title_missing" for f in report.findings)
    assert any(f.code == "thin_pages" for f in report.findings)
    assert any(f.code == "broken_status_codes" for f in report.findings)
    assert report.page_issues
    assert "pagespeed" in report.connector_signals
    # Interpretation is narrative only — score comes from deterministic rollup
    assert "deterministically" in (report.interpretation or "").lower() or "deterministic" in (
        report.interpretation or ""
    ).lower()


@pytest.mark.asyncio
async def test_identical_crawls_yield_identical_scores() -> None:
    pages = [
        _page(),
        _page(
            id="p2",
            url="https://example.com/about",
            title="About Example Company Services Page",
            meta_description="Another unique description for the about page that is long enough.",
            content_hash="about",
            schema=[{"@type": "WebPage"}],
        ),
    ]
    a = await PeacockSeoEngine().audit_crawl(_crawl(pages))
    b = await PeacockSeoEngine().audit_crawl(_crawl(pages))
    assert a.peacock_seo_score.score == b.peacock_seo_score.score
    assert {k: v.score for k, v in a.scores.items()} == {k: v.score for k, v in b.scores.items()}


def test_service_status_flags_features_implemented() -> None:
    status = SeoEngine("org").status()
    assert status["features_implemented"] is True
    assert status["scoring"] == "deterministic"
