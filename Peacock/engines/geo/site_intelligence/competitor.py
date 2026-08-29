"""Competitor Intelligence — real crawl-based diff when a competitor URL is supplied,
plus AI-mention-based signals from the multi-LLM broadcast (always available).

No backlink API, no rank-tracking API, and no keyword-volume API is
configured anywhere in Peacock One, so every metric that would require one is
explicitly reported as "Data unavailable" rather than estimated.
"""

from __future__ import annotations

from crawler.store import StoredCrawl
from geo_intelligence.extraction import extract_title_case_entities, split_sentences, top_ngrams
from geo_intelligence.models import GeoExtractionResult

from site_intelligence.models import DATA_UNAVAILABLE, CompetitorComparison


def _site_entities(crawl: StoredCrawl) -> set[str]:
    entities: set[str] = set()
    for page in crawl.pages.values():
        entities.update(extract_title_case_entities(page.body_text or ""))
    return entities


def _site_terms(crawl: StoredCrawl, top_k: int = 60) -> set[str]:
    terms: set[str] = set()
    for page in crawl.pages.values():
        terms.update(t for t, _f in top_ngrams(page.body_text or "", top_k=top_k))
    return terms


def _question_count(crawl: StoredCrawl) -> int:
    count = 0
    for page in crawl.pages.values():
        count += sum(1 for s in split_sentences(page.body_text or "") if s.strip().endswith("?"))
    return count


def compare_competitor(
    *,
    client_crawl: StoredCrawl,
    client_brand: str,
    competitor_crawl: StoredCrawl | None,
    competitor_url: str | None,
    extraction: GeoExtractionResult,
) -> CompetitorComparison:
    ai_mentions = next(
        (e.frequency for e in extraction.competitor_mentions if competitor_url and competitor_url.lower().find(e.name) >= 0),
        None,
    )
    top_ai_competitor = extraction.competitor_mentions[0] if extraction.competitor_mentions else None
    ai_citation_domains = sorted({c.domain for c in extraction.citations})

    if competitor_crawl is None:
        why: list[str] = []
        if top_ai_competitor:
            why.append(
                f"AI platforms mention '{top_ai_competitor.name}' {top_ai_competitor.frequency}× across "
                f"{len(top_ai_competitor.engine_codes)} platform(s) when discussing this category — no "
                f"competitor URL was crawled to confirm why."
            )
        return CompetitorComparison(
            competitor_url=competitor_url,
            available=False,
            reason_unavailable=(
                "No competitor URL was crawled — supply one to compare content, entity, and topical coverage "
                "directly. SEO visibility, backlink signals, and keyword-volume comparisons additionally "
                "require a rank-tracking / backlink data source, which is not configured."
            ),
            seo_visibility=DATA_UNAVAILABLE,
            content_coverage=DATA_UNAVAILABLE,
            keyword_coverage=DATA_UNAVAILABLE,
            entity_coverage=DATA_UNAVAILABLE,
            backlink_signals=DATA_UNAVAILABLE,
            topical_authority=DATA_UNAVAILABLE,
            structured_data=DATA_UNAVAILABLE,
            question_coverage=DATA_UNAVAILABLE,
            ai_mentions=(
                f"{top_ai_competitor.name}: {top_ai_competitor.frequency} mention(s) across "
                f"{len(top_ai_competitor.engine_codes)} AI platform(s)."
                if top_ai_competitor
                else "No competitor entity detected in AI platform responses."
            ),
            ai_citations=f"{len(extraction.citations)} citation(s) observed across all AI platform responses.",
            cited_domain_overlap=", ".join(ai_citation_domains[:5]) or "None observed.",
            source_authority=DATA_UNAVAILABLE,
            content_freshness=DATA_UNAVAILABLE,
            page_depth=DATA_UNAVAILABLE,
            information_gain_comparison=DATA_UNAVAILABLE,
            why_competitor_is_winning=why or ["Not enough data to determine why — crawl a competitor URL for a direct comparison."],
        )

    client_entities = _site_entities(client_crawl)
    competitor_entities = _site_entities(competitor_crawl)
    missing_entities = sorted(competitor_entities - client_entities)

    client_terms = _site_terms(client_crawl)
    competitor_terms = _site_terms(competitor_crawl)
    missing_terms = sorted(competitor_terms - client_terms)

    client_questions = _question_count(client_crawl)
    competitor_questions = _question_count(competitor_crawl)

    client_pages_with_schema = sum(1 for p in client_crawl.pages.values() if p.schema)
    competitor_pages_with_schema = sum(1 for p in competitor_crawl.pages.values() if p.schema)

    client_word_total = sum(p.word_count for p in client_crawl.pages.values())
    competitor_word_total = sum(p.word_count for p in competitor_crawl.pages.values())

    why_winning: list[str] = []
    if missing_entities:
        why_winning.append(
            f"Covers {len(missing_entities)} entit{'y' if len(missing_entities) == 1 else 'ies'} absent from your "
            f"crawled content: {', '.join(missing_entities[:6])}."
        )
    if competitor_questions > client_questions:
        why_winning.append(
            f"Answers {competitor_questions} question-phrased sentences across its crawled pages versus "
            f"{client_questions} on your site."
        )
    if competitor_word_total > client_word_total * 1.2:
        why_winning.append(
            f"Has {competitor_word_total} total crawled words versus {client_word_total} on your site — "
            "broader content depth."
        )
    if competitor_pages_with_schema > client_pages_with_schema:
        why_winning.append(
            f"{competitor_pages_with_schema} of its crawled pages carry schema.org structured data versus "
            f"{client_pages_with_schema} of yours."
        )
    if top_ai_competitor:
        why_winning.append(
            f"AI platforms mention it {top_ai_competitor.frequency}× across {len(top_ai_competitor.engine_codes)} "
            "platform(s) when discussing this category."
        )
    if not why_winning:
        why_winning.append("No clear content, entity, or structural gap detected in this crawl-based comparison.")

    return CompetitorComparison(
        competitor_url=competitor_url,
        available=True,
        reason_unavailable=None,
        seo_visibility=DATA_UNAVAILABLE + " (requires a rank-tracking data source)",
        content_coverage=f"Client {client_word_total} words vs competitor {competitor_word_total} words (crawled pages).",
        keyword_coverage=DATA_UNAVAILABLE + " (requires a search-volume data source; topical term overlap shown instead)",
        entity_coverage=f"Client {len(client_entities)} distinct entities vs competitor {len(competitor_entities)}; "
        f"{len(missing_entities)} competitor entit{'y' if len(missing_entities) == 1 else 'ies'} not found on your site.",
        backlink_signals=DATA_UNAVAILABLE + " (no backlink data source configured)",
        topical_authority=f"{len(missing_terms)} topical term(s) present on competitor pages but not yours.",
        structured_data=f"Client {client_pages_with_schema}/{len(client_crawl.pages)} pages with schema.org data vs "
        f"competitor {competitor_pages_with_schema}/{len(competitor_crawl.pages)}.",
        question_coverage=f"Client answers {client_questions} question-phrased sentence(s) vs competitor {competitor_questions}.",
        ai_mentions=(
            f"{top_ai_competitor.name}: {top_ai_competitor.frequency} mention(s) across "
            f"{len(top_ai_competitor.engine_codes)} AI platform(s)."
            if top_ai_competitor
            else "No competitor entity detected in AI platform responses."
        ),
        ai_citations=f"{len(extraction.citations)} citation(s) observed across all AI platform responses.",
        cited_domain_overlap=", ".join(ai_citation_domains[:5]) or "None observed.",
        source_authority=DATA_UNAVAILABLE + " (requires a domain-authority data source)",
        content_freshness=DATA_UNAVAILABLE + " (publish dates not reliably present in crawled HTML)",
        page_depth=f"Client crawled {len(client_crawl.pages)} page(s) vs competitor {len(competitor_crawl.pages)}.",
        information_gain_comparison="See per-page Information Gain scores — competitor text is diffed against each client page for near-duplicate detection.",
        why_competitor_is_winning=why_winning,
    )
