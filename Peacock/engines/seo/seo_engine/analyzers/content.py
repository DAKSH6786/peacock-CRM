"""Content quality, structure, freshness, overlap, and cannibalisation signals."""

from __future__ import annotations

import re

from crawler.store import StoredCrawl, StoredPage
from scoring import ScoreResult, penalty_score
from seo_engine.models import SeoFinding, SeoRecommendation

THIN_WORDS = 150


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]{3,}", (text or "").lower()))


def _ok(pages: list[StoredPage]) -> list[StoredPage]:
    return [p for p in pages if (p.status_code or 0) < 400 and p.status != "failed"]


def analyse_content(crawl: StoredCrawl) -> tuple[list[SeoFinding], list[SeoRecommendation], ScoreResult]:
    pages = _ok(list(crawl.pages.values()))
    findings: list[SeoFinding] = []
    recs: list[SeoRecommendation] = []

    thin = [p for p in pages if p.word_count < THIN_WORDS]
    dups = [p for p in pages if p.is_near_duplicate or p.near_duplicate_of]
    missing_h1 = [p for p in pages if not p.h1]
    multi_h1 = [p for p in pages if len(p.h1) > 1]
    poor_structure = [p for p in pages if p.h1 and not p.h2 and p.word_count > 300]

    # Naive freshness: lack of date-like tokens in body
    stale_candidates = [
        p
        for p in pages
        if p.word_count > 100 and not re.search(r"\b(20\d{2}|updated|published|last\s+modified)\b", p.body_text or "", re.I)
    ]

    # Topic overlap / cannibalisation: similar titles or high token overlap
    cannibal: list[tuple[str, str]] = []
    for i, a in enumerate(pages):
        ta = _tokens((a.title or "") + " " + " ".join(a.h1))
        if len(ta) < 3:
            continue
        for b in pages[i + 1 :]:
            tb = _tokens((b.title or "") + " " + " ".join(b.h1))
            if not tb:
                continue
            overlap = len(ta & tb) / len(ta | tb)
            if overlap >= 0.7:
                cannibal.append((a.url, b.url))

    if thin:
        findings.append(
            SeoFinding(
                code="thin_pages",
                severity="warning",
                title="Thin content pages",
                description=f"{len(thin)} page(s) have fewer than {THIN_WORDS} words.",
                category="content",
                page_urls=[p.url for p in thin[:50]],
            )
        )
        recs.append(
            SeoRecommendation(
                code="expand_thin_content",
                title="Expand thin pages",
                priority="high",
                impact=0.75,
                effort=0.6,
                confidence=0.85,
                affected_pages=[p.url for p in thin[:50]],
                reason="Thin pages struggle to satisfy intent and earn rankings.",
                suggested_fix="Add substantive, unique copy that answers the primary query and related sub-intents.",
                category="content_quality",
            )
        )

    if dups:
        findings.append(
            SeoFinding(
                code="duplicated_pages",
                severity="critical",
                title="Duplicated / near-duplicate pages",
                description=f"{len(dups)} page(s) were flagged as duplicate or near-duplicate.",
                category="content",
                page_urls=[p.url for p in dups[:50]],
            )
        )
        recs.append(
            SeoRecommendation(
                code="resolve_duplicates",
                title="Resolve duplicate content",
                priority="critical",
                impact=0.9,
                effort=0.55,
                confidence=0.9,
                affected_pages=[p.url for p in dups[:50]],
                reason="Duplicate clusters dilute rankings and confuse canonicalisation.",
                suggested_fix="Consolidate to one preferred URL, 301 the rest, and align canonicals.",
                category="content_quality",
            )
        )

    if missing_h1 or multi_h1:
        urls = [p.url for p in missing_h1 + multi_h1][:50]
        findings.append(
            SeoFinding(
                code="heading_problems",
                severity="warning",
                title="Heading problems",
                description=f"Missing H1 on {len(missing_h1)} page(s); multiple H1 on {len(multi_h1)} page(s).",
                category="content",
                page_urls=urls,
            )
        )
        recs.append(
            SeoRecommendation(
                code="fix_headings",
                title="Fix H1 hierarchy",
                priority="medium",
                impact=0.55,
                effort=0.3,
                confidence=0.9,
                affected_pages=urls,
                reason="Clear H1s help crawlers and users understand page topics.",
                suggested_fix="Use exactly one descriptive H1 per page, then structured H2/H3 sections.",
                category="content_quality",
            )
        )

    if poor_structure:
        findings.append(
            SeoFinding(
                code="poor_structure",
                severity="opportunity",
                title="Poor content structure",
                description=f"{len(poor_structure)} long page(s) lack H2 subheadings.",
                category="content",
                page_urls=[p.url for p in poor_structure[:50]],
            )
        )

    if stale_candidates:
        findings.append(
            SeoFinding(
                code="content_freshness",
                severity="opportunity",
                title="Weak content freshness indicators",
                description=f"{len(stale_candidates)} page(s) show no obvious date/update markers in body text.",
                category="content",
                page_urls=[p.url for p in stale_candidates[:50]],
            )
        )

    if cannibal:
        urls = sorted({u for pair in cannibal for u in pair})[:50]
        findings.append(
            SeoFinding(
                code="cannibalisation_candidates",
                severity="warning",
                title="Keyword cannibalisation candidates",
                description=f"{len(cannibal)} page pair(s) share highly overlapping titles/H1 topics.",
                category="content",
                page_urls=urls,
                evidence={"pairs": cannibal[:20]},
            )
        )
        recs.append(
            SeoRecommendation(
                code="resolve_cannibalisation",
                title="Differentiate or consolidate overlapping topics",
                priority="high",
                impact=0.8,
                effort=0.65,
                confidence=0.7,
                affected_pages=urls,
                reason="Overlapping intents split ranking signals across URLs.",
                suggested_fix="Merge near-identical intents into one hub page or clearly differentiate targeting.",
                category="content_quality",
            )
        )

    penalties = [
        min(30.0, 6.0 * len(thin)),
        min(35.0, 10.0 * len(dups)),
        min(15.0, 4.0 * len(missing_h1)),
        min(10.0, 3.0 * len(multi_h1)),
        min(8.0, 2.0 * len(poor_structure)),
        min(12.0, 3.0 * len(cannibal)),
    ]
    score = ScoreResult(
        code="content_quality",
        label="Content Quality",
        score=penalty_score(100.0, penalties),
        confidence=0.86 if pages else 0.2,
        inputs_used=["word_count", "h1", "h2", "body_text", "is_near_duplicate", "content_hash", f"thin_threshold={THIN_WORDS}"],
        major_positive_factors=[
            *(["No thin pages detected"] if pages and not thin else []),
            *(["No near-duplicates flagged"] if pages and not dups else []),
        ],
        major_negative_factors=[f.title for f in findings if f.severity in {"critical", "warning"}][:6],
        recommended_actions=[r.title for r in recs[:6]],
    )
    return findings, recs, score
