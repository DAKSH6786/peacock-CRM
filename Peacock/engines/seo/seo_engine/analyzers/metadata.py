"""On-page metadata analysis."""

from __future__ import annotations

from collections import defaultdict

from crawler.store import StoredCrawl, StoredPage
from scoring import ScoreResult, penalty_score
from seo_engine.models import SeoFinding, SeoRecommendation

TITLE_MIN = 30
TITLE_MAX = 65
DESC_MIN = 70
DESC_MAX = 160


def _ok(pages: list[StoredPage]) -> list[StoredPage]:
    return [p for p in pages if (p.status_code or 0) < 400 and p.status != "failed"]


def analyse_metadata(crawl: StoredCrawl) -> tuple[list[SeoFinding], list[SeoRecommendation], ScoreResult]:
    pages = _ok(list(crawl.pages.values()))
    findings: list[SeoFinding] = []
    recs: list[SeoRecommendation] = []

    missing_title = [p for p in pages if not (p.title or "").strip()]
    short_title = [p for p in pages if p.title and len(p.title.strip()) < TITLE_MIN]
    long_title = [p for p in pages if p.title and len(p.title.strip()) > TITLE_MAX]
    title_map: dict[str, list[str]] = defaultdict(list)
    for p in pages:
        if p.title:
            title_map[p.title.strip().lower()].append(p.url)
    dup_titles = {t: urls for t, urls in title_map.items() if len(urls) > 1}

    missing_desc = [p for p in pages if not (p.meta_description or "").strip()]
    dup_desc_map: dict[str, list[str]] = defaultdict(list)
    for p in pages:
        if p.meta_description:
            dup_desc_map[p.meta_description.strip().lower()].append(p.url)
    dup_descs = {d: urls for d, urls in dup_desc_map.items() if len(urls) > 1}

    def _add(
        code: str,
        severity: str,
        title: str,
        description: str,
        urls: list[str],
        *,
        rec_title: str,
        impact: float,
        effort: float,
        fix: str,
        priority: str = "high",
    ) -> None:
        if not urls:
            return
        findings.append(
            SeoFinding(
                code=code,
                severity=severity,  # type: ignore[arg-type]
                title=title,
                description=description,
                category="metadata",
                page_urls=urls[:50],
            )
        )
        recs.append(
            SeoRecommendation(
                code=f"rec_{code}",
                title=rec_title,
                priority=priority,  # type: ignore[arg-type]
                impact=impact,
                effort=effort,
                confidence=0.9,
                affected_pages=urls[:50],
                reason=description,
                suggested_fix=fix,
                category="on_page_seo",
            )
        )

    _add(
        "title_missing",
        "critical",
        "Missing titles",
        f"{len(missing_title)} page(s) have no title tag.",
        [p.url for p in missing_title],
        rec_title="Add unique title tags",
        impact=0.95,
        effort=0.35,
        fix="Write a unique, descriptive <title> (roughly 30–65 characters) for each page.",
        priority="critical",
    )
    _add(
        "title_duplicated",
        "warning",
        "Duplicated titles",
        f"{len(dup_titles)} title value(s) are shared across multiple URLs.",
        [u for urls in dup_titles.values() for u in urls][:50],
        rec_title="Deduplicate title tags",
        impact=0.8,
        effort=0.4,
        fix="Give each URL a distinct title that reflects its primary intent.",
    )
    _add(
        "title_too_short",
        "opportunity",
        "Titles too short",
        f"{len(short_title)} title(s) are under {TITLE_MIN} characters.",
        [p.url for p in short_title],
        rec_title="Expand short titles",
        impact=0.45,
        effort=0.25,
        fix=f"Lengthen titles toward {TITLE_MIN}–{TITLE_MAX} characters with primary keywords.",
        priority="medium",
    )
    _add(
        "title_too_long",
        "opportunity",
        "Titles too long",
        f"{len(long_title)} title(s) exceed {TITLE_MAX} characters.",
        [p.url for p in long_title],
        rec_title="Shorten long titles",
        impact=0.4,
        effort=0.2,
        fix=f"Trim titles to about {TITLE_MAX} characters to reduce SERP truncation.",
        priority="low",
    )
    _add(
        "description_missing",
        "warning",
        "Missing meta descriptions",
        f"{len(missing_desc)} page(s) lack a meta description.",
        [p.url for p in missing_desc],
        rec_title="Add meta descriptions",
        impact=0.7,
        effort=0.35,
        fix=f"Write unique descriptions (~{DESC_MIN}–{DESC_MAX} characters) summarising page value.",
    )
    _add(
        "description_duplicated",
        "warning",
        "Duplicated meta descriptions",
        f"{len(dup_descs)} description(s) are reused across URLs.",
        [u for urls in dup_descs.values() for u in urls][:50],
        rec_title="Deduplicate meta descriptions",
        impact=0.65,
        effort=0.4,
        fix="Create unique descriptions aligned to each page's intent.",
        priority="medium",
    )

    penalties = [
        min(40.0, 12.0 * len(missing_title)),
        min(25.0, 8.0 * len(dup_titles)),
        min(12.0, 3.0 * len(short_title)),
        min(10.0, 2.0 * len(long_title)),
        min(25.0, 6.0 * len(missing_desc)),
        min(15.0, 5.0 * len(dup_descs)),
    ]
    score = ScoreResult(
        code="on_page_seo",
        label="On-Page SEO",
        score=penalty_score(100.0, penalties),
        confidence=0.92 if pages else 0.2,
        inputs_used=["title", "meta_description", f"pages={len(pages)}", f"title_min={TITLE_MIN}", f"title_max={TITLE_MAX}"],
        major_positive_factors=[
            *(["All crawled pages have titles"] if pages and not missing_title else []),
            *(["No duplicated titles"] if pages and not dup_titles else []),
        ],
        major_negative_factors=[f.title for f in findings if f.severity in {"critical", "warning"}][:6],
        recommended_actions=[r.title for r in recs[:6]],
    )
    return findings, recs, score
