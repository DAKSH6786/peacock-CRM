"""Peacock GEO Score — 7 transparent, independently-explained factors.

    GEO Score = (Entity Authority + Citation Readiness + Answerability +
                 Evidence + Topical Coverage + Technical AI Accessibility +
                 Brand Authority) / 7

Every factor is computed from data actually present on the crawled page
(headings, links, schema.org blocks, HTTP/meta signals, body text patterns).
Nothing here is LLM-invented — the multi-LLM signals live in
``geo_intelligence`` and are combined separately at the report level.
"""

from __future__ import annotations

import re

from citation_graph.classify import classify_source, host_from_url
from crawler.store import StoredPage
from geo_intelligence.extraction import extract_title_case_entities, split_sentences, top_ngrams

from site_intelligence.information_gain import score_information_gain
from site_intelligence.models import ExplainedScore, GeoScoreBreakdown, ScoreFactor

_AUTHORITATIVE_SOURCE_CLASSES = frozenset({"government", "academic", "news", "industry_publication"})
_AUTHOR_BYLINE_RE = re.compile(
    r"\b(by\s+[A-Z][a-z]+\s+[A-Z][a-z]+|written by|author\s*:|reviewed by)\b", re.IGNORECASE
)
_SOURCES_SECTION_RE = re.compile(r"\b(sources?|references?)\s*:", re.IGNORECASE)
_ABOUT_LINK_RE = re.compile(r"/(about|team|company|leadership)(/|$)", re.IGNORECASE)


def _clamp100(value: float) -> float:
    return max(0.0, min(100.0, value))


def _has_schema_type(page: StoredPage, types: frozenset[str]) -> bool:
    for block in page.schema:
        block_type = block.get("@type")
        candidates = block_type if isinstance(block_type, list) else [block_type]
        if any(str(c).lower() in types for c in candidates if c):
            return True
    return False


def entity_authority(page: StoredPage) -> ExplainedScore:
    entities = extract_title_case_entities(page.body_text or "")
    distinct = sorted({e for e in entities if len(e) > 2})
    has_entity_schema = _has_schema_type(page, frozenset({"organization", "person", "product", "localbusiness"}))

    density_score = _clamp100(len(distinct) * 4.0)
    schema_bonus = 20.0 if has_entity_schema else 0.0
    score = _clamp100(0.8 * density_score + schema_bonus)

    factors = [
        ScoreFactor(
            metric="distinct_named_entities_on_page",
            observed_value=len(distinct),
            benchmark=">= 15 distinct entities for strong entity clarity",
            weight=0.8,
            score_contribution=round(0.8 * density_score, 2),
            evidence=(
                f"Detected {len(distinct)} distinct capitalised entity mention(s)"
                + (f": {', '.join(distinct[:8])}" if distinct else "")
                + "."
            ),
            confidence="medium",
        ),
        ScoreFactor(
            metric="organization_person_product_schema_present",
            observed_value=has_entity_schema,
            benchmark="Organization/Person/Product schema.org block present",
            weight=0.2,
            score_contribution=schema_bonus,
            evidence=f"{'Found' if has_entity_schema else 'Did not find'} an Organization/Person/Product schema.org block in page HTML.",
            confidence="high",
        ),
    ]
    return ExplainedScore(
        score=round(score, 2),
        label="Entity Authority",
        factors=factors,
        summary="How clearly this page names and structures entities that AI systems can recognise and attribute.",
    )


def citation_readiness(page: StoredPage) -> ExplainedScore:
    authoritative_domains: list[str] = []
    for url in page.external_links:
        domain = host_from_url(url)
        source_class, _is_comp, _is_client, authority = classify_source(url=url, domain=domain)
        if source_class in _AUTHORITATIVE_SOURCE_CLASSES and authority >= 0.7:
            authoritative_domains.append(domain)
    authoritative_domains = sorted(set(authoritative_domains))
    has_sources_section = bool(_SOURCES_SECTION_RE.search(page.body_text or ""))

    link_score = _clamp100(len(authoritative_domains) * 20.0)
    section_bonus = 15.0 if has_sources_section else 0.0
    score = _clamp100(0.85 * link_score + section_bonus)

    factors = [
        ScoreFactor(
            metric="outbound_links_to_authoritative_domains",
            observed_value=len(authoritative_domains),
            benchmark=">= 3 outbound links to government/academic/news/industry sources",
            weight=0.85,
            score_contribution=round(0.85 * link_score, 2),
            evidence=(
                f"{len(authoritative_domains)} outbound link(s) classified as authoritative "
                f"(gov/academic/news/industry): {', '.join(authoritative_domains[:5]) or 'none'}. "
                f"Total outbound links on page: {len(page.external_links)}."
            ),
            confidence="high",
        ),
        ScoreFactor(
            metric="sources_or_references_section_present",
            observed_value=has_sources_section,
            benchmark="Explicit 'Sources:' / 'References:' section",
            weight=0.15,
            score_contribution=section_bonus,
            evidence=f"{'Found' if has_sources_section else 'Did not find'} an explicit Sources/References label in page text.",
            confidence="medium",
        ),
    ]
    return ExplainedScore(
        score=round(score, 2),
        label="Citation Readiness",
        factors=factors,
        summary="Whether this page cites authoritative third parties the way AI answers tend to cite sources.",
    )


def answerability(page: StoredPage) -> ExplainedScore:
    headings = list(page.h2) + list(page.h3)
    question_headings = [h for h in headings if h.strip().endswith("?")]
    has_faq_schema = _has_schema_type(page, frozenset({"faqpage", "qapage"}))
    sentences = split_sentences(page.body_text or "")
    question_sentences = [s for s in sentences if s.strip().endswith("?")]
    question_ratio = (len(question_sentences) / len(sentences)) if sentences else 0.0

    heading_score = _clamp100(len(question_headings) * 25.0)
    schema_bonus = 30.0 if has_faq_schema else 0.0
    ratio_bonus = _clamp100(question_ratio * 300.0) * 0.2

    score = _clamp100(0.5 * heading_score + schema_bonus + ratio_bonus)

    factors = [
        ScoreFactor(
            metric="question_phrased_headings",
            observed_value=len(question_headings),
            benchmark=">= 3 question-phrased H2/H3 headings",
            weight=0.5,
            score_contribution=round(0.5 * heading_score, 2),
            evidence=f"{len(question_headings)} of {len(headings)} H2/H3 heading(s) are phrased as questions"
            + (f" (e.g. \"{question_headings[0]}\")." if question_headings else "."),
            confidence="high",
        ),
        ScoreFactor(
            metric="faq_or_qa_schema_present",
            observed_value=has_faq_schema,
            benchmark="FAQPage/QAPage schema.org block present",
            weight=0.3,
            score_contribution=schema_bonus,
            evidence=f"{'Found' if has_faq_schema else 'Did not find'} an FAQPage/QAPage schema.org block.",
            confidence="high",
        ),
        ScoreFactor(
            metric="question_sentence_ratio",
            observed_value=round(question_ratio, 3),
            benchmark=">= 5% of sentences phrased as direct questions",
            weight=0.2,
            score_contribution=round(ratio_bonus, 2),
            evidence=f"{len(question_sentences)} of {len(sentences)} sentence(s) in body text end in a question mark.",
            confidence="medium",
        ),
    ]
    return ExplainedScore(
        score=round(score, 2),
        label="Answerability",
        factors=factors,
        summary="How directly the page answers likely questions in a quotable, extractable format.",
    )


def evidence_factor(page: StoredPage, *, competitor_text: str | None = None) -> ExplainedScore:
    ig_score, signals, evidence_notes = score_information_gain(page.body_text or "", competitor_text=competitor_text)
    factors = [
        ScoreFactor(
            metric=sig.signal_code,
            observed_value=round(sig.strength, 2),
            benchmark="reward signal present" if sig.polarity == "reward" else "penalty signal absent",
            weight=1.0 / max(1, len(signals)),
            score_contribution=round(sig.strength * (100.0 / max(1, len(signals))), 2),
            evidence=sig.evidence,
            confidence="medium",
        )
        for sig in signals
    ]
    return ExplainedScore(
        score=round(ig_score, 2),
        label="Evidence",
        factors=factors,
        summary="Whether the page contains original data, statistics, expert input, or other citation-worthy evidence.",
    )


def topical_coverage(page: StoredPage, *, site_key_terms: list[str]) -> ExplainedScore:
    if not site_key_terms:
        return ExplainedScore(
            score=50.0,
            label="Topical Coverage",
            factors=[
                ScoreFactor(
                    metric="site_key_terms_available",
                    observed_value=0,
                    benchmark="site-wide key terms derived from crawl",
                    weight=1.0,
                    score_contribution=50.0,
                    evidence="No site-wide key terms were available for comparison (single-page or thin crawl).",
                    confidence="experimental",
                )
            ],
            summary="Neutral score — not enough crawled pages to derive a site-wide topic set.",
        )
    page_terms = {t for t, _freq in top_ngrams(page.body_text or "", sizes=(1, 2), top_k=60)}
    covered = [t for t in site_key_terms if t in page_terms]
    coverage_ratio = len(covered) / len(site_key_terms)
    score = _clamp100(coverage_ratio * 100.0)
    factors = [
        ScoreFactor(
            metric="site_key_terms_covered",
            observed_value=f"{len(covered)}/{len(site_key_terms)}",
            benchmark="Cover the majority of the site's important topical terms",
            weight=1.0,
            score_contribution=round(score, 2),
            evidence=f"Covers {len(covered)} of {len(site_key_terms)} important topical term(s) identified across the crawled site: "
            + (", ".join(covered[:8]) or "none"),
            confidence="medium",
        )
    ]
    return ExplainedScore(
        score=round(score, 2),
        label="Topical Coverage",
        factors=factors,
        summary="Breadth of important site-wide topics actually covered on this specific page.",
    )


def technical_ai_accessibility(page: StoredPage) -> ExplainedScore:
    is_indexable = page.indexability == "indexable"
    is_noindex = bool(page.robots and "noindex" in page.robots.lower())
    has_schema = bool(page.schema)
    status_ok = bool(page.status_code and 200 <= page.status_code < 300)
    has_viewport = bool(page.viewport_meta)

    penalty = 0.0
    notes: list[str] = []
    if is_noindex:
        penalty += 40.0
        notes.append("robots directive includes noindex")
    if page.is_js_heavy:
        penalty += 25.0
        notes.append("page looks JavaScript-heavy — many AI crawlers do not execute JS")
    if not status_ok:
        penalty += 20.0
        notes.append(f"HTTP status {page.status_code} is not in the 200 range")
    if not has_schema:
        penalty += 10.0
        notes.append("no schema.org structured data found")
    if not has_viewport:
        penalty += 5.0
        notes.append("no viewport meta tag found (mobile readiness signal)")

    score = _clamp100(100.0 - penalty)
    factors = [
        ScoreFactor(
            metric="indexable_no_noindex",
            observed_value=is_indexable and not is_noindex,
            benchmark="indexable, no noindex directive",
            weight=0.4,
            score_contribution=0.0 if is_noindex else 40.0,
            evidence=f"indexability={page.indexability}; robots directive={page.robots or 'none'}.",
            confidence="high",
        ),
        ScoreFactor(
            metric="not_js_render_dependent",
            observed_value=not page.is_js_heavy,
            benchmark="content available without executing JavaScript",
            weight=0.25,
            score_contribution=0.0 if page.is_js_heavy else 25.0,
            evidence="Page looks JavaScript-heavy." if page.is_js_heavy else "Page content is present in server-rendered HTML.",
            confidence="high",
        ),
        ScoreFactor(
            metric="http_status_2xx",
            observed_value=page.status_code,
            benchmark="200-299",
            weight=0.2,
            score_contribution=0.0 if not status_ok else 20.0,
            evidence=f"Observed HTTP status code {page.status_code}.",
            confidence="high",
        ),
        ScoreFactor(
            metric="structured_data_present",
            observed_value=len(page.schema),
            benchmark=">= 1 schema.org block",
            weight=0.1,
            score_contribution=0.0 if not has_schema else 10.0,
            evidence=f"Found {len(page.schema)} schema.org block(s) on the page.",
            confidence="high",
        ),
        ScoreFactor(
            metric="viewport_meta_present",
            observed_value=page.viewport_meta,
            benchmark="viewport meta tag present (mobile readiness)",
            weight=0.05,
            score_contribution=0.0 if not has_viewport else 5.0,
            evidence=f"viewport meta = {page.viewport_meta or 'not found'}.",
            confidence="high",
        ),
    ]
    if notes:
        factors.append(
            ScoreFactor(
                metric="accessibility_notes",
                observed_value=notes,
                benchmark="no accessibility blockers",
                weight=0.0,
                score_contribution=0.0,
                evidence="; ".join(notes),
                confidence="high",
            )
        )
    return ExplainedScore(
        score=round(score, 2),
        label="Technical AI Accessibility",
        factors=factors,
        summary="Whether AI crawlers can actually fetch and parse this page's content without executing JavaScript.",
    )


def brand_authority(page: StoredPage) -> ExplainedScore:
    has_byline = bool(_AUTHOR_BYLINE_RE.search(page.body_text or ""))
    has_person_or_org_schema = _has_schema_type(page, frozenset({"person", "organization"}))
    is_https = page.url.lower().startswith("https://")
    has_about_link = any(_ABOUT_LINK_RE.search(link) for link in page.internal_links)

    score = _clamp100(
        (30.0 if has_byline else 0.0)
        + (30.0 if has_person_or_org_schema else 0.0)
        + (20.0 if is_https else 0.0)
        + (20.0 if has_about_link else 0.0)
    )
    factors = [
        ScoreFactor(
            metric="author_byline_detected",
            observed_value=has_byline,
            benchmark="visible author/reviewer byline",
            weight=0.3,
            score_contribution=30.0 if has_byline else 0.0,
            evidence="Found an author/reviewer byline pattern in page text." if has_byline else "No author/reviewer byline pattern found.",
            confidence="medium",
        ),
        ScoreFactor(
            metric="person_or_organization_schema",
            observed_value=has_person_or_org_schema,
            benchmark="Person/Organization schema.org block present",
            weight=0.3,
            score_contribution=30.0 if has_person_or_org_schema else 0.0,
            evidence=f"{'Found' if has_person_or_org_schema else 'Did not find'} a Person/Organization schema.org block.",
            confidence="high",
        ),
        ScoreFactor(
            metric="https",
            observed_value=is_https,
            benchmark="served over HTTPS",
            weight=0.2,
            score_contribution=20.0 if is_https else 0.0,
            evidence=f"Page URL scheme is {'https' if is_https else 'http'}.",
            confidence="high",
        ),
        ScoreFactor(
            metric="about_or_team_page_linked",
            observed_value=has_about_link,
            benchmark="internal link to /about, /team, or /company",
            weight=0.2,
            score_contribution=20.0 if has_about_link else 0.0,
            evidence=f"{'Found' if has_about_link else 'Did not find'} an internal link to an about/team/company page.",
            confidence="medium",
        ),
    ]
    return ExplainedScore(
        score=round(score, 2),
        label="Brand Authority",
        factors=factors,
        summary="E-E-A-T-style signals: authorship, organisational identity, and transport security.",
    )


def compute_page_geo_score(
    page: StoredPage,
    *,
    site_key_terms: list[str],
    competitor_text: str | None = None,
) -> GeoScoreBreakdown:
    ea = entity_authority(page)
    cr = citation_readiness(page)
    ans = answerability(page)
    ev = evidence_factor(page, competitor_text=competitor_text)
    tc = topical_coverage(page, site_key_terms=site_key_terms)
    tech = technical_ai_accessibility(page)
    ba = brand_authority(page)

    geo_score = round((ea.score + cr.score + ans.score + ev.score + tc.score + tech.score + ba.score) / 7.0, 2)

    return GeoScoreBreakdown(
        geo_score=geo_score,
        entity_authority=ea,
        citation_readiness=cr,
        answerability=ans,
        evidence=ev,
        topical_coverage=tc,
        technical_ai_accessibility=tech,
        brand_authority=ba,
    )
