"""Structured data presence and basic validation."""

from __future__ import annotations

from crawler.store import StoredCrawl, StoredPage
from scoring import ScoreResult, penalty_score, ratio_score
from seo_engine.models import SeoFinding, SeoRecommendation


def _ok(pages: list[StoredPage]) -> list[StoredPage]:
    return [p for p in pages if (p.status_code or 0) < 400 and p.status != "failed"]


def analyse_structured_data(crawl: StoredCrawl) -> tuple[list[SeoFinding], list[SeoRecommendation], ScoreResult]:
    pages = _ok(list(crawl.pages.values()))
    findings: list[SeoFinding] = []
    recs: list[SeoRecommendation] = []

    with_schema = [p for p in pages if p.schema]
    without = [p for p in pages if not p.schema]
    parse_errors = [
        p
        for p in with_schema
        if any(isinstance(block, dict) and block.get("parse_error") for block in p.schema)
    ]
    has_org = any(
        isinstance(block, dict) and str(block.get("@type", "")).lower() in {"organization", "localbusiness"}
        for p in with_schema
        for block in p.schema
    )
    has_webpage = any(
        isinstance(block, dict) and "webpage" in str(block.get("@type", "")).lower()
        for p in with_schema
        for block in p.schema
    )

    if without:
        findings.append(
            SeoFinding(
                code="schema_missing",
                severity="opportunity",
                title="Pages missing structured data",
                description=f"{len(without)} page(s) have no JSON-LD blocks.",
                category="structured_data",
                page_urls=[p.url for p in without[:50]],
            )
        )
        recs.append(
            SeoRecommendation(
                code="add_schema",
                title="Add relevant JSON-LD structured data",
                priority="medium",
                impact=0.55,
                effort=0.5,
                confidence=0.75,
                affected_pages=[p.url for p in without[:50]],
                reason="Structured data improves eligibility for rich results.",
                suggested_fix="Add Organization/WebSite on the homepage and page-type schema (Article, FAQ, Product) where accurate.",
                category="structured_data",
            )
        )

    if parse_errors:
        findings.append(
            SeoFinding(
                code="schema_invalid",
                severity="warning",
                title="Structured data parse errors",
                description=f"{len(parse_errors)} page(s) contain JSON-LD that failed basic parsing.",
                category="structured_data",
                page_urls=[p.url for p in parse_errors[:50]],
            )
        )
        recs.append(
            SeoRecommendation(
                code="fix_schema_json",
                title="Fix invalid JSON-LD",
                priority="high",
                impact=0.65,
                effort=0.35,
                confidence=0.9,
                affected_pages=[p.url for p in parse_errors[:50]],
                reason="Invalid JSON-LD cannot be consumed by search engines.",
                suggested_fix="Validate JSON-LD syntax and required properties; remove broken script blocks.",
                category="structured_data",
            )
        )

    if with_schema and not has_org:
        findings.append(
            SeoFinding(
                code="schema_opportunity_organization",
                severity="opportunity",
                title="Organization schema opportunity",
                description="No Organization/LocalBusiness entity detected in crawled JSON-LD.",
                category="structured_data",
                page_urls=[crawl.seed_url],
            )
        )

    if with_schema and not has_webpage:
        findings.append(
            SeoFinding(
                code="schema_opportunity_webpage",
                severity="info",
                title="WebPage schema opportunity",
                description="Consider WebPage/WebSite schema on key templates.",
                category="structured_data",
            )
        )

    presence = ratio_score(len(with_schema), len(pages), empty=40.0)
    penalties = [min(25.0, 8.0 * len(parse_errors))]
    if not with_schema and pages:
        penalties.append(30.0)
    score = ScoreResult(
        code="structured_data",
        label="Structured Data",
        score=penalty_score(presence, penalties),
        confidence=0.8 if pages else 0.2,
        inputs_used=["schema_blocks", "parse_error", f"pages_with_schema={len(with_schema)}"],
        major_positive_factors=[
            *(["JSON-LD present on some pages"] if with_schema else []),
            *(["Organization entity detected"] if has_org else []),
        ],
        major_negative_factors=[
            *(["Many pages lack schema"] if without else []),
            *(["JSON-LD parse errors"] if parse_errors else []),
        ],
        recommended_actions=[r.title for r in recs[:5]],
    )
    return findings, recs, score
