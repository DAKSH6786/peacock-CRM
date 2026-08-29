"""Internal linking analysis."""

from __future__ import annotations

from collections import Counter

from crawler.store import StoredCrawl, StoredPage
from scoring import ScoreResult, penalty_score
from seo_engine.models import SeoFinding, SeoRecommendation

DEEP_DEPTH = 4
LOW_INBOUND = 1


def _ok(pages: list[StoredPage]) -> list[StoredPage]:
    return [p for p in pages if (p.status_code or 0) < 400 and p.status != "failed"]


def analyse_linking(crawl: StoredCrawl) -> tuple[list[SeoFinding], list[SeoRecommendation], ScoreResult]:
    pages = _ok(list(crawl.pages.values()))
    by_url = {p.url: p for p in pages}
    inbound: Counter[str] = Counter()
    broken_internal: list[tuple[str, str]] = []

    for page in pages:
        for href in page.internal_links:
            inbound[href] += 1
            target = by_url.get(href)
            if target and ((target.status_code or 0) >= 400 or target.status == "failed"):
                broken_internal.append((page.url, href))

    orphans = [p for p in pages if p.is_orphan_candidate or inbound.get(p.url, 0) == 0]
    # Seed is exempt from orphan classification
    orphans = [p for p in orphans if p.url.rstrip("/") != crawl.seed_url.rstrip("/")]
    low_link = [p for p in pages if 0 < inbound.get(p.url, 0) <= LOW_INBOUND]
    deep = [p for p in pages if p.crawl_depth >= DEEP_DEPTH]

    # Anchor text quality proxy: many raw URL anchors / empty — we only have hrefs in crawl store,
    # so flag pages with unusually high outbound internal fanout as weak structure signal.
    excessive_out = [p for p in pages if len(p.internal_links) > 150]

    findings: list[SeoFinding] = []
    recs: list[SeoRecommendation] = []

    if orphans:
        findings.append(
            SeoFinding(
                code="orphan_pages",
                severity="critical",
                title="Orphan page candidates",
                description=f"{len(orphans)} page(s) have no inbound internal links from the crawled set.",
                category="internal_linking",
                page_urls=[p.url for p in orphans[:50]],
            )
        )
        recs.append(
            SeoRecommendation(
                code="link_orphans",
                title="Add internal links to orphan pages",
                priority="critical",
                impact=0.85,
                effort=0.45,
                confidence=0.8,
                affected_pages=[p.url for p in orphans[:50]],
                reason="Orphans are hard to discover and rarely rank well.",
                suggested_fix="Link to each orphan from relevant hubs, nav, or contextual body links.",
                category="internal_linking",
            )
        )

    if low_link:
        findings.append(
            SeoFinding(
                code="low_link_pages",
                severity="warning",
                title="Low-link pages",
                description=f"{len(low_link)} page(s) have very few inbound internal links.",
                category="internal_linking",
                page_urls=[p.url for p in low_link[:50]],
            )
        )

    if deep:
        findings.append(
            SeoFinding(
                code="excessive_depth",
                severity="warning",
                title="Excessive crawl depth",
                description=f"{len(deep)} page(s) sit at depth ≥ {DEEP_DEPTH}.",
                category="internal_linking",
                page_urls=[p.url for p in deep[:50]],
            )
        )
        recs.append(
            SeoRecommendation(
                code="reduce_depth",
                title="Bring important URLs closer to the root",
                priority="medium",
                impact=0.6,
                effort=0.5,
                confidence=0.75,
                affected_pages=[p.url for p in deep[:50]],
                reason="Deep pages receive less crawl attention and PageRank flow.",
                suggested_fix="Add hub links or navigation shortcuts to high-value deep URLs.",
                category="internal_linking",
            )
        )

    if broken_internal:
        urls = sorted({src for src, _ in broken_internal} | {dst for _, dst in broken_internal})[:50]
        findings.append(
            SeoFinding(
                code="broken_internal_links",
                severity="critical",
                title="Broken internal links",
                description=f"{len(broken_internal)} internal link(s) point to broken URLs.",
                category="internal_linking",
                page_urls=urls,
                evidence={"samples": broken_internal[:20]},
            )
        )
        recs.append(
            SeoRecommendation(
                code="fix_broken_internal_links",
                title="Repair broken internal links",
                priority="critical",
                impact=0.9,
                effort=0.4,
                confidence=0.95,
                affected_pages=urls,
                reason="Broken internal links waste equity and frustrate users.",
                suggested_fix="Update anchors to live URLs or remove obsolete links.",
                category="internal_linking",
            )
        )

    if excessive_out:
        findings.append(
            SeoFinding(
                code="anchor_text_quality",
                severity="opportunity",
                title="Possible weak link structure / over-linking",
                description=f"{len(excessive_out)} page(s) expose a very large internal link fan-out (>150).",
                category="internal_linking",
                page_urls=[p.url for p in excessive_out[:50]],
            )
        )

    penalties = [
        min(35.0, 10.0 * len(orphans)),
        min(15.0, 3.0 * len(low_link)),
        min(20.0, 5.0 * len(deep)),
        min(30.0, 8.0 * len({dst for _, dst in broken_internal})),
        min(8.0, 4.0 * len(excessive_out)),
    ]
    score = ScoreResult(
        code="internal_linking",
        label="Internal Linking",
        score=penalty_score(100.0, penalties),
        confidence=0.84 if pages else 0.2,
        inputs_used=["internal_links", "is_orphan_candidate", "crawl_depth", "status_code"],
        major_positive_factors=[
            *(["No orphan candidates"] if pages and not orphans else []),
            *(["No broken internal links"] if pages and not broken_internal else []),
        ],
        major_negative_factors=[f.title for f in findings if f.severity in {"critical", "warning"}][:6],
        recommended_actions=[r.title for r in recs[:6]],
    )
    return findings, recs, score
