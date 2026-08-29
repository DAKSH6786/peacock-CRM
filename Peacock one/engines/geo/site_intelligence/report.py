"""Peacock Site Intelligence — the enterprise SEO + GEO report orchestrator.

Workflow: Crawl -> Understand -> Benchmark -> Query LLMs -> Extract AI
Signals -> Compare Competitors -> Identify Gaps -> Prioritize Opportunities
-> Generate Exact Fixes -> Track Improvement.

This module composes already-real building blocks (the crawler, the SEO/AEO
engines, and the Peacock AI Gateway + GEO Intelligence Layer) and the new
site_intelligence modules (GEO score, information gain, page opportunities,
competitor diff, LLM keyword map, impact ranking). It never fabricates a
number: anything not backed by a real crawl or a real/plugin-backed signal is
explicitly marked unavailable in ``data_availability``.
"""

from __future__ import annotations

from urllib.parse import urlparse

from aeo_engine.scoring import aggregate_scores as aeo_aggregate_scores
from aeo_engine.scoring import analyse_page as aeo_analyse_page
from crawler.policy import CrawlPolicy
from crawler.service import CrawlerService
from crawler.store import InMemoryCrawlStore, StoredCrawl, StoredPage
from crawler.url_utils import UrlValidationError
from geo_intelligence import run_geo_intelligence
from geo_intelligence.extraction import tokenize, top_ngrams
from geo_intelligence.gateway import DEFAULT_ENGINE_CODES, ENGINE_META
from llm_gateway.registry import LLMGateway
from seo_engine import PeacockSeoEngine

from site_intelligence.competitor import compare_competitor
from site_intelligence.impact import build_top_actions, score_page_opportunities, thirty_sixty_ninety_plan
from site_intelligence.llm_geo_score import score_llm_geo
from site_intelligence.llm_keyword_map import build_llm_keyword_map
from site_intelligence.models import DATA_UNAVAILABLE, DataAvailability, SiteIntelligenceReport
from site_intelligence.page_scoring import build_page_opportunity

DEFAULT_MAX_PAGES = 8


async def _run_crawl(url: str, *, max_pages: int) -> StoredCrawl:
    service = CrawlerService(organisation_id="site-intelligence", store=InMemoryCrawlStore())
    policy = CrawlPolicy(
        max_pages=max(1, min(max_pages, 25)),
        max_depth=2,
        fetch_timeout_seconds=10.0,
        allow_js_render=False,  # keep the report fast and dependency-free; a JS-render pass can be added later
        concurrency=4,
    )
    return await service.ingest_and_crawl(workspace_id="site-intelligence", url=url, policy=policy)


_GENERIC_TITLE_PREFIXES = ("welcome to", "home", "homepage", "index")


def _infer_brand(crawl: StoredCrawl) -> str:
    host = (urlparse(crawl.seed_url).hostname or crawl.seed_url).replace("www.", "")
    host_brand = host.split(".")[0].title()

    home = (
        crawl.pages.get(crawl.seed_url)
        or next((p for p in crawl.pages.values() if p.crawl_depth == 0), None)
        or next(iter(crawl.pages.values()), None)
    )
    if home and home.title:
        title = home.title.strip()
        for sep in (" | ", " – ", " — ", " - ", ": "):
            if sep in title:
                candidate = title.split(sep)[0].strip()
                if candidate and not candidate.lower().startswith(_GENERIC_TITLE_PREFIXES) and len(candidate.split()) <= 4:
                    return candidate
        if not title.lower().startswith(_GENERIC_TITLE_PREFIXES) and len(title.split()) <= 4:
            return title[:60]
    return host_brand


def _build_industry_prompt(brand: str, site_key_terms: list[str], competitor_url: str | None) -> str:
    topic_clause = ", ".join(site_key_terms[:6]) if site_key_terms else "its main products and services"
    competitor_clause = f" How does it compare to {urlparse(competitor_url).hostname}?" if competitor_url else ""
    return (
        f"I'm researching companies in the space covering {topic_clause}. What is {brand}, what does it "
        f"offer, who are the leading providers in this space, and what questions do people commonly ask "
        f"about this category?{competitor_clause}"
    )


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


async def run_site_intelligence_report(
    *,
    llm_gateway: LLMGateway | None,
    url: str,
    competitor_url: str | None = None,
    max_pages: int = DEFAULT_MAX_PAGES,
    engine_codes: list[str] | None = None,
) -> SiteIntelligenceReport:
    measured: list[str] = []
    unavailable: list[str] = []

    try:
        crawl = await _run_crawl(url, max_pages=max_pages)
    except UrlValidationError as exc:
        raise ValueError(f"Could not crawl {url}: {exc}") from exc

    if not crawl.pages:
        raise ValueError(
            f"Crawl of {url} completed with status '{crawl.status}' but returned zero pages "
            f"({crawl.error_summary or 'robots.txt may disallow crawling, or the site is unreachable'})."
        )
    measured.append(f"Real crawl of {len(crawl.pages)} page(s) from {url} (HTTP status, headers, HTML).")

    competitor_crawl: StoredCrawl | None = None
    if competitor_url:
        try:
            competitor_crawl = await _run_crawl(competitor_url, max_pages=max_pages)
            if not competitor_crawl.pages:
                competitor_crawl = None
                unavailable.append(f"Competitor crawl of {competitor_url} returned zero pages.")
            else:
                measured.append(f"Real crawl of {len(competitor_crawl.pages)} page(s) from {competitor_url}.")
        except UrlValidationError as exc:
            unavailable.append(f"Competitor URL {competitor_url} could not be crawled: {exc}")

    brand = _infer_brand(crawl)

    seo_engine = PeacockSeoEngine()
    seo_report = await seo_engine.audit_crawl(crawl, fetch_connectors=False)
    measured.append("Technical + on-page SEO audit (Peacock SEO Engine) from real crawl data.")
    unavailable.append(
        "Core Web Vitals (field/lab data) and PageSpeed metrics: no PageSpeed Insights/CrUX API key "
        "configured — only crawl-derived proxy indicators (page size, script count) are used."
    )
    unavailable.append("Backlink profile and domain authority: no backlink data source configured.")
    unavailable.append("Search volume / keyword demand: no keyword-volume data source configured.")

    site_text = " ".join(p.body_text or "" for p in crawl.pages.values())
    site_key_terms = [t for t, _f in top_ngrams(site_text, top_k=30)]
    site_topics = sorted({h for p in crawl.pages.values() for h in (list(p.h1) + list(p.h2))})[:20] or [brand]

    codes = [c for c in (engine_codes or list(DEFAULT_ENGINE_CODES)) if c in ENGINE_META]
    research_prompt = _build_industry_prompt(brand, site_key_terms, competitor_url)
    client_host = urlparse(url).hostname or ""
    competitor_host = urlparse(competitor_url).hostname or "" if competitor_url else ""

    geo_intel = await run_geo_intelligence(
        llm_gateway=llm_gateway,
        organisation_id="site-intelligence",
        client_brand=brand,
        competitors=[],
        site_topics=site_topics,
        research_prompt=research_prompt,
        engine_codes=codes,
        client_domains=[client_host] if client_host else [],
        competitor_domains=[competitor_host] if competitor_host else [],
        # Never inject unrelated canned marketing copy into a real site's report — a plugin
        # with no live API key simply has no observed content, not fabricated content.
        simulated_responses={},
    )
    live_engines = [r.engine_name for r in geo_intel.provider_responses if not r.simulated]
    if live_engines:
        measured.append(f"Live multi-LLM broadcast via Peacock AI Gateway: {', '.join(live_engines)}.")
    simulated_engines = [r.engine_name for r in geo_intel.provider_responses if r.simulated]
    if simulated_engines:
        unavailable.append(
            f"Live LLM responses for {', '.join(simulated_engines)}: no API key configured, so no "
            "response was collected and no GEO Score, keyword, or citation signal was fabricated for "
            "them. Set the corresponding environment variable to enable a real measurement."
        )

    competitor_text = (
        " ".join(p.body_text or "" for p in competitor_crawl.pages.values()) if competitor_crawl else None
    )
    competitor_comparison = compare_competitor(
        client_crawl=crawl,
        client_brand=brand,
        competitor_crawl=competitor_crawl,
        competitor_url=competitor_url,
        extraction=geo_intel.extraction,
    )

    depth_by_url: dict[str, int] = {}
    page_tokens_by_url: dict[str, set[str]] = {}
    pages = []
    geo_breakdowns = {}
    for page in crawl.pages.values():
        depth_by_url[page.url] = page.crawl_depth
        page_tokens_by_url[page.url] = set(tokenize(page.body_text or ""))
        opportunity, geo_breakdown = build_page_opportunity(
            page,
            site_key_terms=site_key_terms,
            competitor_text=competitor_text,
            competitor_summary="; ".join(competitor_comparison.why_competitor_is_winning)
            if competitor_comparison.available
            else DATA_UNAVAILABLE,
        )
        pages.append(opportunity)
        geo_breakdowns[page.url] = geo_breakdown

    keyword_map = build_llm_keyword_map(
        extraction=geo_intel.extraction,
        responses=geo_intel.provider_responses,
        site_text=site_text,
        client_brand=brand,
    )

    score_page_opportunities(
        pages,
        depth_by_url=depth_by_url,
        page_tokens_by_url=page_tokens_by_url,
        missing_topics=geo_intel.extraction.missing_topics,
    )
    top_actions = build_top_actions(
        pages=pages,
        keyword_map=keyword_map,
        extraction=geo_intel.extraction,
        recommendations=geo_intel.recommendations,
    )
    plan = thirty_sixty_ninety_plan(top_actions)

    recs_by_engine = {r.engine_code: r for r in geo_intel.recommendations}
    ai_visibility = []
    for response in geo_intel.provider_responses:
        per_llm = score_llm_geo(response, brand=brand, extraction=geo_intel.extraction)
        rec = recs_by_engine.get(response.engine_code)
        if rec:
            per_llm.opportunities = rec.opportunities
        ai_visibility.append(per_llm)

    site_seo_score = seo_report.peacock_seo_score.score
    aeo_scores = [aeo_analyse_page(_page_to_aeo_dict(p)) for p in crawl.pages.values()]
    site_aeo_score = aeo_aggregate_scores(aeo_scores)["aeo_score"]
    site_geo_score = round(sum(g.geo_score for g in geo_breakdowns.values()) / len(geo_breakdowns), 2) if geo_breakdowns else 0.0
    peacock_visibility_score = round((site_seo_score + site_aeo_score + site_geo_score) / 3.0, 2)

    homepage = crawl.pages.get(crawl.seed_url) or next(iter(crawl.pages.values()))
    representative_geo_breakdown = geo_breakdowns.get(homepage.url) or next(iter(geo_breakdowns.values()))

    site_ig_score = round(
        sum(g.evidence.score for g in geo_breakdowns.values()) / len(geo_breakdowns), 2
    ) if geo_breakdowns else 0.0

    client_domain_cited = client_host and any(client_host in c.domain for c in geo_intel.extraction.citations)
    ai_citation_presence = {
        "own_domain_cited_by_ai": bool(client_domain_cited),
        "total_citations_observed_across_platforms": len(geo_intel.extraction.citations),
        "note": (
            f"{'Your domain was observed as a cited source' if client_domain_cited else 'Your domain was not observed as a cited source'} "
            "in the collected LLM responses for this research prompt."
        ),
    }

    critical_issues = [
        f"{p.url}: {p.whats_wrong[0]}" for p in pages if p.priority == "Critical" and p.whats_wrong
    ]
    critical_issues.extend(f"{f.title}: {f.description}" for f in seo_report.critical_issues[:10])

    top_sorted = sorted(pages, key=lambda p: (p.seo_score + p.aeo_score + p.geo_score), reverse=True)
    top_performing_pages = top_sorted[:5]
    weak_pages = list(reversed(top_sorted))[:5]

    technical_health = {
        "peacock_seo_score": seo_report.peacock_seo_score.to_dict(),
        "section_scores": {k: v.to_dict() for k, v in seo_report.scores.items()},
        "core_web_vitals": DATA_UNAVAILABLE + " (no PageSpeed Insights/CrUX API key configured)",
        "pages_with_broken_status": sum(1 for p in crawl.pages.values() if (p.status_code or 0) >= 400),
        "pages_js_heavy": sum(1 for p in crawl.pages.values() if p.is_js_heavy),
        "pages_missing_schema": sum(1 for p in crawl.pages.values() if not p.schema),
        "robots_txt_present": bool(crawl.robots_raw),
        "sitemap_urls_found": len(crawl.sitemap_urls),
    }

    executive_summary = (
        f"Peacock analysed {len(crawl.pages)} page(s) of {brand} ({url}). Peacock Visibility Score "
        f"{peacock_visibility_score}/100 (SEO {site_seo_score}, AEO {site_aeo_score}, GEO {site_geo_score}). "
        f"{len(critical_issues)} critical issue(s) found. "
        f"{'Your domain was observed as an AI-cited source.' if client_domain_cited else 'Your domain was not observed as an AI-cited source for this research prompt.'} "
        f"Top opportunity: {top_actions[0].title if top_actions else 'no ranked opportunity available'}."
    )

    entity_opportunities = keyword_map.missing_semantic_entities
    content_gaps = geo_intel.extraction.missing_topics
    citation_opportunities = sorted({c.domain for c in geo_intel.extraction.citations})[:10]
    raw_citations = [c.to_dict() for c in geo_intel.extraction.citations]

    data_availability = DataAvailability(measured=measured, unavailable=unavailable)

    return SiteIntelligenceReport(
        url=url,
        brand=brand,
        crawled_pages_count=len(crawl.pages),
        total_word_count=sum(p.word_count for p in crawl.pages.values()),
        crawl_status=crawl.status,
        executive_summary=executive_summary,
        site_text_sample=site_text[:20000],
        peacock_visibility_score=peacock_visibility_score,
        seo_score=site_seo_score,
        aeo_score=site_aeo_score,
        geo_score=site_geo_score,
        geo_score_breakdown=representative_geo_breakdown,
        technical_health=technical_health,
        ai_visibility=ai_visibility,
        ai_citation_presence=ai_citation_presence,
        information_gain_score=site_ig_score,
        competitor_gap=competitor_comparison,
        llm_by_llm_visibility=[r.to_dict() for r in geo_intel.recommendations],
        critical_issues=critical_issues[:15],
        top_actions=top_actions,
        keyword_opportunities=keyword_map,
        entity_opportunities=entity_opportunities,
        site_key_terms=site_key_terms,
        content_gaps=content_gaps,
        citation_opportunities=citation_opportunities,
        raw_citations=raw_citations,
        backlink_opportunities=DATA_UNAVAILABLE + " — no backlink data source configured for this deployment.",
        top_performing_pages=top_performing_pages,
        weak_pages=weak_pages,
        thirty_day_plan=plan.get("30_day", []),
        sixty_day_plan=plan.get("60_day", []),
        ninety_day_plan=plan.get("90_day", []),
        data_availability=data_availability,
        pages=pages,
    )
