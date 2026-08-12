"""Image SEO analysis."""

from __future__ import annotations

from crawler.store import StoredCrawl, StoredPage
from scoring import ScoreResult, penalty_score
from seo_engine.models import SeoFinding, SeoRecommendation


def _ok(pages: list[StoredPage]) -> list[StoredPage]:
    return [p for p in pages if (p.status_code or 0) < 400 and p.status != "failed"]


def analyse_images(crawl: StoredCrawl) -> tuple[list[SeoFinding], list[SeoRecommendation], list[float]]:
    """Return findings, recommendations, and penalties to fold into on-page/technical scores."""
    pages = _ok(list(crawl.pages.values()))
    findings: list[SeoFinding] = []
    recs: list[SeoRecommendation] = []

    missing_alt_pages: list[str] = []
    missing_alt_count = 0
    oversized_candidates: list[str] = []
    broken_image_pages: list[str] = []

    crawled_urls = {p.url for p in crawl.pages.values()}
    for page in pages:
        for image in page.images or []:
            alt = image.get("alt")
            src = image.get("src") or ""
            if alt is None or str(alt).strip() == "":
                missing_alt_count += 1
                if page.url not in missing_alt_pages:
                    missing_alt_pages.append(page.url)
            # Oversized heuristic: query hints or huge path names / known heavy formats without size
            lower = src.lower()
            if any(token in lower for token in ("original", "fullsize", "4000", "5000", "uncompressed")):
                if page.url not in oversized_candidates:
                    oversized_candidates.append(page.url)
            if src in crawled_urls:
                target = crawl.pages.get(src)
                if target and ((target.status_code or 0) >= 400 or target.status == "failed"):
                    if page.url not in broken_image_pages:
                        broken_image_pages.append(page.url)

    if missing_alt_count:
        findings.append(
            SeoFinding(
                code="missing_alt",
                severity="warning",
                title="Images missing ALT attributes",
                description=f"{missing_alt_count} image(s) across {len(missing_alt_pages)} page(s) lack ALT text.",
                category="images",
                page_urls=missing_alt_pages[:50],
            )
        )
        recs.append(
            SeoRecommendation(
                code="add_image_alt",
                title="Add descriptive ALT text",
                priority="medium",
                impact=0.5,
                effort=0.35,
                confidence=0.9,
                affected_pages=missing_alt_pages[:50],
                reason="ALT text improves accessibility and image search relevance.",
                suggested_fix="Write concise, descriptive ALT attributes for informative images; mark decorative images appropriately.",
                category="on_page_seo",
            )
        )

    if oversized_candidates:
        findings.append(
            SeoFinding(
                code="oversized_assets",
                severity="opportunity",
                title="Possibly oversized image assets",
                description=f"{len(oversized_candidates)} page(s) reference assets that look unoptimised by URL heuristics.",
                category="images",
                page_urls=oversized_candidates[:50],
            )
        )
        recs.append(
            SeoRecommendation(
                code="compress_images",
                title="Compress and properly size images",
                priority="medium",
                impact=0.55,
                effort=0.45,
                confidence=0.55,
                affected_pages=oversized_candidates[:50],
                reason="Heavy images hurt LCP and performance scores.",
                suggested_fix="Serve modern formats (WebP/AVIF), responsive sizes, and compressed binaries.",
                category="performance",
            )
        )

    if broken_image_pages:
        findings.append(
            SeoFinding(
                code="broken_images",
                severity="warning",
                title="Broken image references",
                description=f"{len(broken_image_pages)} page(s) reference image URLs that failed in the crawl.",
                category="images",
                page_urls=broken_image_pages[:50],
            )
        )

    penalties = [
        min(15.0, 0.5 * missing_alt_count),
        min(8.0, 3.0 * len(oversized_candidates)),
        min(12.0, 4.0 * len(broken_image_pages)),
    ]
    return findings, recs, penalties
