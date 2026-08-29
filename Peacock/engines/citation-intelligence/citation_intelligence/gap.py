"""Citation Gap Engine — who is cited, for what, and what the client's site lacks.

For each distinct URL actually cited in the collected AI plugin responses,
attempts a real HTTP fetch of that page (same fetcher the crawler uses) to
compare its real topical terms and evidence signals against the client's own
crawled content. If the page cannot be fetched (network error, blocked,
timeout), the gap is reported as unavailable rather than guessed.
"""

from __future__ import annotations

from collections import defaultdict

from crawler.adapters.httpx_fetcher import HttpxFetcher
from crawler.extract import extract_page
from geo_intelligence.extraction import extract_title_case_entities, top_ngrams
from geo_intelligence.models import CitationSignal
from site_intelligence.information_gain import score_information_gain

from citation_intelligence.models import DATA_UNAVAILABLE, CitationGapReport, CitationGapResult


async def _fetch_page_text(url: str, *, timeout_seconds: float = 8.0) -> tuple[str | None, str | None, int]:
    """Best-effort real fetch of a cited page. Returns (title, body_text, word_count)."""
    fetcher = HttpxFetcher()
    result = await fetcher.fetch(url, timeout_seconds=timeout_seconds)
    if result.error or not result.html or result.status_code >= 400:
        return None, None, 0
    extraction = extract_page(
        request_url=url,
        final_url=result.url or url,
        status_code=result.status_code,
        html=result.html,
        headers=result.headers,
        seed_host_url=url,
    )
    return extraction.title, extraction.body_text, extraction.word_count


async def analyse_citation_gaps(
    *,
    client_brand: str,
    citations: list[CitationSignal],
    client_site_text: str,
    max_citations: int = 6,
    fetch_timeout_seconds: float = 8.0,
) -> CitationGapReport:
    client_terms = {t for t, _f in top_ngrams(client_site_text, top_k=80)}
    client_entities = set(extract_title_case_entities(client_site_text))

    by_url: dict[str, list[CitationSignal]] = defaultdict(list)
    for c in citations:
        by_url[c.url].append(c)

    top_urls = list(by_url.items())[:max_citations]
    gaps: list[CitationGapResult] = []

    for url, signals in top_urls:
        engine_codes = sorted({s.engine_code for s in signals})
        source_class = signals[0].source_class
        domain = signals[0].domain

        try:
            title, body_text, word_count = await _fetch_page_text(url, timeout_seconds=fetch_timeout_seconds)
        except Exception:  # noqa: BLE001 — never let one bad URL break the whole report
            title, body_text, word_count = None, None, 0

        if body_text is None:
            gaps.append(
                CitationGapResult(
                    cited_url=url,
                    cited_domain=domain,
                    source_class=source_class,
                    engine_codes=engine_codes,
                    topic_context="; ".join(sorted({s.engine_code for s in signals})),
                    fetch_status="fetch_failed",
                    cited_page_title=None,
                    cited_page_word_count=None,
                    entity_gap=[],
                    evidence_gap=DATA_UNAVAILABLE + " — could not fetch the cited page.",
                    source_gap=True,
                    statistics_gap=DATA_UNAVAILABLE,
                    authority_gap=f"Source class: {source_class}.",
                    content_gap=[],
                    recommended_fix=[
                        f"Consider referencing or earning coverage from {domain}, which AI platforms "
                        "cited for this topic (page could not be fetched to compare content)."
                    ],
                )
            )
            continue

        cited_terms = {t for t, _f in top_ngrams(body_text, top_k=80)}
        cited_entities = set(extract_title_case_entities(body_text))
        missing_terms = sorted(cited_terms - client_terms)[:8]
        missing_entities = sorted(cited_entities - client_entities)[:8]

        cited_ig_score, _signals, _evidence = score_information_gain(body_text)
        client_ig_score, _signals2, _evidence2 = score_information_gain(client_site_text)
        evidence_gap = (
            f"Cited page Information Gain {cited_ig_score:.0f}/100 vs your site {client_ig_score:.0f}/100."
        )

        gaps.append(
            CitationGapResult(
                cited_url=url,
                cited_domain=domain,
                source_class=source_class,
                engine_codes=engine_codes,
                topic_context=title or url,
                fetch_status="fetched",
                cited_page_title=title,
                cited_page_word_count=word_count,
                entity_gap=missing_entities,
                evidence_gap=evidence_gap,
                source_gap=domain not in client_terms,
                statistics_gap=(
                    "Cited page shows stronger original-data signals."
                    if cited_ig_score > client_ig_score + 10
                    else "No material statistics gap detected."
                ),
                authority_gap=f"Source class: {source_class}.",
                content_gap=missing_terms,
                recommended_fix=[
                    f"Cover the topic(s) {', '.join(missing_terms[:3]) or '(none detected)'} that {domain} "
                    f"addresses and AI platforms cited.",
                    f"Consider naming the entities {', '.join(missing_entities[:3]) or '(none detected)'} "
                    "that appear on the cited page but not on your site.",
                ],
            )
        )

    return CitationGapReport(
        client_brand=client_brand,
        citations_observed=len(citations),
        citations_analysed=len(gaps),
        gaps=gaps,
    )
