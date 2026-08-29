"""Page-Level Opportunity Engine — 8 real scores + exact-fix narrative per page.

SEO / AEO / GEO / Content / Technical / Authority / Information Gain /
AI Citation Potential are each built from data actually observed on the
crawled page. No score here is a placeholder — if a signal genuinely cannot
be measured (e.g. no competitor page to diff against), the relevant field
says so explicitly.
"""

from __future__ import annotations

from aeo_engine.scoring import aggregate_scores as aeo_aggregate_scores
from aeo_engine.scoring import analyse_page as aeo_analyse_page
from crawler.store import StoredPage

from site_intelligence.fix_generator import (
    fix_faq,
    fix_h1,
    fix_meta_description,
    fix_schema,
    fix_title,
)
from site_intelligence.geo_score import compute_page_geo_score
from site_intelligence.information_gain import freshness_signal, score_information_gain
from site_intelligence.models import (
    DATA_UNAVAILABLE,
    PRIORITY_CRITICAL,
    PRIORITY_HIGH,
    PRIORITY_LOW,
    PRIORITY_MEDIUM,
    GeoScoreBreakdown,
    PageOpportunity,
)


def _clamp100(value: float) -> float:
    return max(0.0, min(100.0, value))


def _page_to_aeo_dict(page: StoredPage) -> dict:
    return {
        "url": page.url,
        "title": page.title,
        "meta_description": page.meta_description,
        "h1": page.h1,
        "h2": page.h2,
        "h3": page.h3,
        "body_text": page.body_text,
        "word_count": page.word_count,
        "external_links": page.external_links,
        "canonical": page.canonical,
        "schema_blocks": page.schema,
    }


def compute_seo_score(page: StoredPage) -> tuple[float, list[str]]:
    """Real on-page + technical SEO health for THIS page (0-100)."""
    checks: list[tuple[bool, float, str]] = []

    title_len = len(page.title or "")
    checks.append((30 <= title_len <= 65, 15.0, f"title length {title_len} chars"))
    meta_len = len(page.meta_description or "")
    checks.append((70 <= meta_len <= 160, 15.0, f"meta description length {meta_len} chars"))
    checks.append((len(page.h1) == 1, 15.0, f"{len(page.h1)} H1 tag(s) found"))
    checks.append((bool(page.canonical), 10.0, f"canonical={'present' if page.canonical else 'missing'}"))
    checks.append((page.indexability == "indexable", 15.0, f"indexability={page.indexability}"))
    checks.append((bool(page.status_code) and page.status_code < 400, 10.0, f"status_code={page.status_code}"))
    checks.append((page.word_count >= 300, 10.0, f"word_count={page.word_count}"))
    alt_ratio = (
        sum(1 for img in page.images if img.get("alt")) / len(page.images) if page.images else 1.0
    )
    checks.append((alt_ratio >= 0.8, 10.0, f"image alt-text coverage {alt_ratio:.0%} ({len(page.images)} image(s))"))

    score = sum(weight for passed, weight, _note in checks if passed)
    evidence = [note for _passed, _weight, note in checks]
    return round(_clamp100(score), 2), evidence


def compute_content_score(page: StoredPage) -> tuple[float, list[str]]:
    freshness_label, freshness_note = freshness_signal(page.body_text or "")
    heading_ok = len(page.h1) == 1 and len(page.h2) >= 1
    is_thin = page.word_count < 250
    is_duplicate = page.is_near_duplicate

    score = 100.0
    evidence: list[str] = [freshness_note]
    if is_thin:
        score -= 35.0
        evidence.append(f"Thin content: only {page.word_count} word(s).")
    if is_duplicate:
        score -= 30.0
        evidence.append(f"Flagged as (near-)duplicate of {page.near_duplicate_of}.")
    if not heading_ok:
        score -= 15.0
        evidence.append("Heading structure is not a clean single-H1 + H2 hierarchy.")
    if freshness_label == "stale":
        score -= 10.0
    elif freshness_label == "unknown":
        score -= 5.0
    return round(_clamp100(score), 2), evidence


def compute_technical_score(page: StoredPage) -> tuple[float, list[str]]:
    score = 100.0
    evidence: list[str] = []
    if page.status_code and page.status_code >= 400:
        score -= 60.0
        evidence.append(f"HTTP {page.status_code}.")
    if len(page.redirect_chain) > 1:
        score -= 15.0
        evidence.append(f"Redirect chain length {len(page.redirect_chain)}.")
    if page.robots and "noindex" in page.robots.lower():
        score -= 25.0
        evidence.append("noindex directive present.")
    if page.is_js_heavy:
        score -= 15.0
        evidence.append("Page looks JavaScript-heavy.")
    if not page.viewport_meta:
        score -= 10.0
        evidence.append("No viewport meta tag (mobile readiness).")
    if page.is_orphan_candidate:
        score -= 10.0
        evidence.append("No inbound internal links found from the crawled set (orphan candidate).")
    if not evidence:
        evidence.append("No technical blockers detected in this crawl.")
    return round(_clamp100(score), 2), evidence


def compute_authority_score(page: StoredPage, geo: GeoScoreBreakdown) -> tuple[float, list[str]]:
    """On-page E-E-A-T signals only — real backlink-based domain authority is unavailable."""
    score = round(0.5 * geo.brand_authority.score + 0.5 * geo.citation_readiness.score, 2)
    evidence = [
        f"Brand authority (on-page E-E-A-T signals): {geo.brand_authority.score}/100.",
        f"Citation readiness (outbound authoritative links): {geo.citation_readiness.score}/100.",
        "Backlink-based domain authority is unavailable (no backlink data source configured).",
    ]
    return score, evidence


def build_page_opportunity(
    page: StoredPage,
    *,
    site_key_terms: list[str],
    competitor_text: str | None,
    competitor_summary: str,
) -> tuple[PageOpportunity, GeoScoreBreakdown]:
    seo_score, seo_evidence = compute_seo_score(page)

    aeo_single = aeo_analyse_page(_page_to_aeo_dict(page))
    aeo_score = aeo_aggregate_scores([aeo_single])["aeo_score"]

    geo = compute_page_geo_score(page, site_key_terms=site_key_terms, competitor_text=competitor_text)

    content_score, content_evidence = compute_content_score(page)
    technical_score, technical_evidence = compute_technical_score(page)
    authority_score, authority_evidence = compute_authority_score(page, geo)
    ig_score = geo.evidence.score  # same real information-gain measurement, exposed at top level too

    ai_citation_potential = round(
        0.35 * geo.citation_readiness.score
        + 0.25 * geo.answerability.score
        + 0.25 * geo.evidence.score
        + 0.15 * geo.technical_ai_accessibility.score,
        2,
    )

    whats_wrong: list[str] = []
    why_it_matters: list[str] = []
    evidence_found: list[str] = []
    exact_fix: list[str] = []
    priority = PRIORITY_LOW

    if not page.title:
        whats_wrong.append("Missing <title> tag.")
        why_it_matters.append("Search engines and AI answer engines both rely on the title to understand page topic.")
        exact_fix.append(fix_title(page).draft)
        priority = PRIORITY_CRITICAL
    elif not (30 <= len(page.title) <= 65):
        whats_wrong.append(f"Title length is {len(page.title)} characters (recommended 30-65).")
        why_it_matters.append("Titles outside this range are often truncated in search results or diluted for topical clarity.")
        exact_fix.append(fix_title(page).draft)
        priority = max(priority, PRIORITY_MEDIUM, key=_priority_rank)

    if not page.meta_description:
        whats_wrong.append("Missing meta description.")
        why_it_matters.append("A missing meta description lets the search engine choose a snippet, reducing click-through control.")
        exact_fix.append(fix_meta_description(page).draft)
        priority = max(priority, PRIORITY_HIGH, key=_priority_rank)

    if len(page.h1) != 1:
        whats_wrong.append(f"{len(page.h1)} H1 tag(s) found (expected exactly 1).")
        why_it_matters.append("Zero or multiple H1s weaken the page's single clear topical signal.")
        exact_fix.append(fix_h1(page).draft)
        priority = max(priority, PRIORITY_MEDIUM, key=_priority_rank)

    if page.word_count < 250:
        whats_wrong.append(f"Thin content — only {page.word_count} word(s).")
        why_it_matters.append("Thin pages rarely carry enough topical depth to rank or to be cited as an authoritative answer.")
        priority = max(priority, PRIORITY_HIGH, key=_priority_rank)

    if geo.answerability.score < 40:
        whats_wrong.append("Low answerability — few direct question-answer patterns detected.")
        why_it_matters.append("AI answer engines strongly prefer pages that answer a question directly and concisely.")
        exact_fix.append(fix_faq(page).draft.split("\n\n")[0])
        priority = max(priority, PRIORITY_HIGH, key=_priority_rank)

    if geo.evidence.score < 35:
        whats_wrong.append("Low evidence/information-gain score — little original data or statistics detected.")
        why_it_matters.append("Pages that only restate common knowledge are less likely to be cited by AI engines seeking original evidence.")
        priority = max(priority, PRIORITY_MEDIUM, key=_priority_rank)

    if not page.schema:
        whats_wrong.append("No schema.org structured data found.")
        why_it_matters.append("Structured data helps both search engines and AI systems parse entities and answers unambiguously.")
        exact_fix.append(fix_schema(page).draft[:200] + ("…" if len(fix_schema(page).draft) > 200 else ""))
        priority = max(priority, PRIORITY_MEDIUM, key=_priority_rank)

    if page.is_js_heavy:
        whats_wrong.append("Page looks JavaScript-heavy — content may not be visible to non-JS AI crawlers.")
        why_it_matters.append("Several AI/answer-engine crawlers do not execute JavaScript, so JS-rendered content may be invisible to them.")
        priority = max(priority, PRIORITY_HIGH, key=_priority_rank)

    if not whats_wrong:
        whats_wrong.append("No critical issues detected in this crawl.")
        why_it_matters.append("Page meets the technical/on-page baselines checked by this analysis.")

    evidence_found = [*seo_evidence, *content_evidence, *technical_evidence, *authority_evidence]
    if not exact_fix:
        exact_fix.append("No template fix generated — page already meets the checked baselines.")

    expected_impact = (
        "High — addresses a foundational discoverability signal."
        if priority in (PRIORITY_CRITICAL, PRIORITY_HIGH)
        else "Moderate — incremental improvement to an already-functioning page."
    )
    difficulty = "Low" if priority in (PRIORITY_CRITICAL,) else ("Medium" if priority == PRIORITY_HIGH else "Low")
    confidence = "high" if priority in (PRIORITY_CRITICAL, PRIORITY_HIGH) else "medium"

    opportunity = PageOpportunity(
        url=page.url,
        title=page.title,
        seo_score=seo_score,
        aeo_score=aeo_score,
        geo_score=geo.geo_score,
        content_score=content_score,
        technical_score=technical_score,
        authority_score=authority_score,
        information_gain_score=ig_score,
        ai_citation_potential=ai_citation_potential,
        whats_wrong=whats_wrong,
        why_it_matters=why_it_matters,
        evidence_found=evidence_found,
        competitor_doing_better=competitor_summary or DATA_UNAVAILABLE,
        exact_fix=exact_fix,
        expected_impact=expected_impact,
        difficulty=difficulty,
        priority=priority,
        confidence=confidence,
        peacock_impact_score=0.0,  # filled in by impact.py once site-wide context is known
    )
    return opportunity, geo


_PRIORITY_RANK = {PRIORITY_LOW: 0, PRIORITY_MEDIUM: 1, PRIORITY_HIGH: 2, PRIORITY_CRITICAL: 3}


def _priority_rank(value: str) -> int:
    return _PRIORITY_RANK.get(value, 0)
