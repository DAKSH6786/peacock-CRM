"""Crawlability / technical crawl-signal analysis."""

from __future__ import annotations

from collections import Counter

from crawler.store import StoredCrawl, StoredPage
from scoring import ScoreResult, penalty_score, ratio_score
from seo_engine.models import SeoFinding, SeoRecommendation


def _ok_pages(crawl: StoredCrawl) -> list[StoredPage]:
    return [p for p in crawl.pages.values() if (p.status_code or 0) < 400 and p.status != "failed"]


def analyse_crawlability(crawl: StoredCrawl) -> tuple[list[SeoFinding], list[SeoRecommendation], ScoreResult, ScoreResult]:
    pages = list(crawl.pages.values())
    ok = _ok_pages(crawl)
    findings: list[SeoFinding] = []
    recs: list[SeoRecommendation] = []

    # robots
    if crawl.robots_raw:
        findings.append(
            SeoFinding(
                code="robots_present",
                severity="info",
                title="robots.txt discovered",
                description="Crawl recorded a robots.txt response for the seed host.",
                category="crawlability",
            )
        )
    else:
        findings.append(
            SeoFinding(
                code="robots_missing",
                severity="warning",
                title="robots.txt missing or unreadable",
                description="No robots.txt payload was stored for this crawl.",
                category="crawlability",
            )
        )
        recs.append(
            SeoRecommendation(
                code="add_robots",
                title="Publish a valid robots.txt",
                priority="medium",
                impact=0.55,
                effort=0.2,
                confidence=0.85,
                affected_pages=[crawl.seed_url],
                reason="Crawlers lack explicit sitewide crawl directives.",
                suggested_fix="Add /robots.txt with clear Allow/Disallow rules and a Sitemap declaration.",
                category="crawlability",
            )
        )

    # sitemap
    if crawl.sitemap_urls:
        findings.append(
            SeoFinding(
                code="sitemap_present",
                severity="info",
                title="Sitemap discovered",
                description=f"Found {len(crawl.sitemap_urls)} sitemap URL(s).",
                category="crawlability",
                evidence={"sitemap_urls": crawl.sitemap_urls[:10]},
            )
        )
    else:
        findings.append(
            SeoFinding(
                code="sitemap_missing",
                severity="warning",
                title="No sitemap discovered",
                description="Crawl did not locate a usable XML sitemap.",
                category="crawlability",
            )
        )
        recs.append(
            SeoRecommendation(
                code="add_sitemap",
                title="Publish and reference an XML sitemap",
                priority="high",
                impact=0.7,
                effort=0.35,
                confidence=0.9,
                affected_pages=[crawl.seed_url],
                reason="Sitemaps help discovery of deep and orphaned URLs.",
                suggested_fix="Generate sitemap.xml, submit it in Search Console, and reference it from robots.txt.",
                category="crawlability",
            )
        )

    # status codes
    status_counts = Counter((p.status_code or 0) for p in pages)
    broken = [p for p in pages if (p.status_code or 0) >= 400 or p.status == "failed"]
    if broken:
        findings.append(
            SeoFinding(
                code="broken_status_codes",
                severity="critical",
                title="Broken pages detected",
                description=f"{len(broken)} URL(s) returned 4xx/5xx or failed fetches.",
                category="crawlability",
                page_urls=[p.url for p in broken[:50]],
                evidence={"status_counts": dict(status_counts)},
            )
        )
        recs.append(
            SeoRecommendation(
                code="fix_broken_pages",
                title="Fix or redirect broken URLs",
                priority="critical",
                impact=0.95,
                effort=0.5,
                confidence=0.95,
                affected_pages=[p.url for p in broken[:50]],
                reason="Broken URLs waste crawl budget and damage UX/indexability.",
                suggested_fix="Repair content, restore pages, or 301 redirect to live equivalents; remove dead internal links.",
                category="crawlability",
            )
        )

    # redirects
    long_redirects = [p for p in pages if len(p.redirect_chain or []) > 2]
    if long_redirects:
        findings.append(
            SeoFinding(
                code="redirect_chains",
                severity="warning",
                title="Redirect chains detected",
                description=f"{len(long_redirects)} page(s) traverse multi-hop redirects.",
                category="crawlability",
                page_urls=[p.url for p in long_redirects[:50]],
            )
        )
        recs.append(
            SeoRecommendation(
                code="flatten_redirects",
                title="Flatten redirect chains",
                priority="medium",
                impact=0.55,
                effort=0.4,
                confidence=0.85,
                affected_pages=[p.url for p in long_redirects[:50]],
                reason="Redirect chains slow crawlers and dilute signals.",
                suggested_fix="Point links and canonicals directly at the final URL with a single 301 where needed.",
                category="crawlability",
            )
        )

    # canonicalisation
    canonical_mismatch = [
        p
        for p in ok
        if p.canonical and p.canonical.rstrip("/") != p.url.rstrip("/")
    ]
    missing_canonical = [p for p in ok if not p.canonical]
    if missing_canonical:
        findings.append(
            SeoFinding(
                code="canonical_missing",
                severity="warning",
                title="Missing canonical tags",
                description=f"{len(missing_canonical)} indexable page(s) lack a canonical.",
                category="crawlability",
                page_urls=[p.url for p in missing_canonical[:50]],
            )
        )
    if canonical_mismatch:
        findings.append(
            SeoFinding(
                code="canonical_mismatch",
                severity="opportunity",
                title="Canonical points away from crawled URL",
                description=f"{len(canonical_mismatch)} page(s) canonicalize elsewhere.",
                category="crawlability",
                page_urls=[p.url for p in canonical_mismatch[:50]],
            )
        )

    # indexability
    noindex = [p for p in ok if (p.indexability or "") in {"noindex", "non_indexable_status"}]
    indexable = [p for p in ok if (p.indexability or "") == "indexable"]
    if noindex:
        findings.append(
            SeoFinding(
                code="noindex_pages",
                severity="warning",
                title="Pages marked non-indexable",
                description=f"{len(noindex)} page(s) are noindex or non-indexable by status.",
                category="indexability",
                page_urls=[p.url for p in noindex[:50]],
            )
        )

    total = max(len(pages), 1)
    tech_penalties = []
    if not crawl.robots_raw:
        tech_penalties.append(8)
    if not crawl.sitemap_urls:
        tech_penalties.append(10)
    tech_penalties.append(min(40.0, 8.0 * len(broken)))
    tech_penalties.append(min(20.0, 4.0 * len(long_redirects)))
    tech_penalties.append(min(15.0, 2.0 * len(missing_canonical)))

    technical = ScoreResult(
        code="technical_seo",
        label="Technical SEO",
        score=penalty_score(100.0, tech_penalties),
        confidence=0.9 if pages else 0.2,
        inputs_used=[
            "robots_raw",
            "sitemap_urls",
            "status_code",
            "redirect_chain",
            "canonical",
            f"page_count={len(pages)}",
        ],
        major_positive_factors=[
            *(["robots.txt present"] if crawl.robots_raw else []),
            *(["sitemap discovered"] if crawl.sitemap_urls else []),
            *(["majority of pages return 2xx"] if len(broken) == 0 else []),
        ],
        major_negative_factors=[
            *(["broken status codes"] if broken else []),
            *(["missing robots.txt"] if not crawl.robots_raw else []),
            *(["missing sitemap"] if not crawl.sitemap_urls else []),
            *(["redirect chains"] if long_redirects else []),
        ],
        recommended_actions=[r.title for r in recs[:5]],
    )

    index_score = ratio_score(len(indexable), len(ok), empty=50.0)
    if broken:
        index_score = penalty_score(index_score, [min(25.0, 5.0 * len(broken))])
    indexability = ScoreResult(
        code="indexability",
        label="Indexability",
        score=index_score,
        confidence=0.88 if ok else 0.25,
        inputs_used=["indexability", "status_code", "robots", "canonical", f"ok_pages={len(ok)}"],
        major_positive_factors=[
            f"{len(indexable)} indexable page(s)" if indexable else "No confirmed indexable pages",
        ],
        major_negative_factors=[
            *(["noindex / non-indexable pages"] if noindex else []),
            *(["broken pages block indexation"] if broken else []),
        ],
        recommended_actions=[
            "Review noindex directives on money pages",
            "Ensure canonical and status codes agree on the preferred URL",
        ],
    )

    return findings, recs, technical, indexability
