"""Peacock Growth Loop orchestrator.

    SEO + AEO + GEO -> AI Visibility -> LLM Intelligence -> Citation +
    Competitor Gap -> Opportunity Engine -> Content Strategy -> Content
    Creation -> Optimization -> AI Agents -> Human Experts -> Publishing
    (preview) -> Measurement -> Experiments -> Learning -> Repeat

Composes every engine built for Peacock One into the single flagship
workflow. Every stage is real: a crawl, a live/simulated AI plugin
broadcast, or a deterministic scoring formula already used elsewhere.
Nothing here fabricates a metric, and nothing publishes/deletes/modifies a
production system without a later, explicit human approval step.
"""

from __future__ import annotations

from urllib.parse import urlparse

from ai_visibility import run_ai_visibility_scan
from citation_intelligence.gap import analyse_citation_gaps
from citation_intelligence.models import CitationGapReport
from content_intelligence import (
    build_content_graph,
    generate_content_brief,
    recommend_content_types,
    simulate_multi_llm_readiness,
)
from geo_intelligence.models import CitationSignal
from llm_gateway.registry import LLMGateway
from measurement import capture_snapshot
from peacock_agents import (
    run_aeo_agent,
    run_citation_agent,
    run_competitor_agent,
    run_content_strategist_agent,
    run_geo_agent,
    run_internal_linking_agent,
    run_research_agent,
    run_seo_agent,
    run_technical_seo_agent,
)
from peacock_experts import create_task
from peacock_learning import log_recommendation
from peacock_opportunity import build_opportunity, rank_opportunities
from peacock_publishing import PublishRequest, get_connector
from site_intelligence import run_site_intelligence_report
from site_intelligence.models import SiteIntelligenceReport

from growth_loop.models import GrowthLoopReport, GrowthLoopStage


def _stage(name: str, status: str, detail: str) -> GrowthLoopStage:
    return GrowthLoopStage(stage=name, status=status, detail=detail)


def _derive_topics(site_report: SiteIntelligenceReport) -> list[str]:
    topics = list(site_report.keyword_opportunities.universal_terms[:4])
    if not topics:
        topics = [t for t, in ((p.title,) for p in site_report.top_performing_pages) if t][:3]
    return topics or [site_report.brand]


async def run_growth_loop(
    *,
    llm_gateway: LLMGateway | None,
    url: str,
    competitor_url: str | None = None,
    max_pages: int = 8,
    engine_codes: list[str] | None = None,
) -> GrowthLoopReport:
    stages: list[GrowthLoopStage] = []

    # 1) SEO + AEO + GEO + Competitor + Opportunity discovery (real crawl)
    site_report = await run_site_intelligence_report(
        llm_gateway=llm_gateway, url=url, competitor_url=competitor_url, max_pages=max_pages, engine_codes=engine_codes
    )
    stages.append(_stage("seo_aeo_geo_intelligence", "completed", f"Crawled {site_report.crawled_pages_count} page(s) of {site_report.brand}."))

    brand = site_report.brand
    topics = _derive_topics(site_report)
    client_host = urlparse(url).hostname or ""
    competitor_host = urlparse(competitor_url).hostname or "" if competitor_url else ""
    competitors = [competitor_host] if competitor_host else []

    # 2) AI Visibility Command Center
    ai_visibility_report = await run_ai_visibility_scan(
        llm_gateway=llm_gateway,
        brand=brand,
        topics=topics,
        competitors=competitors,
        client_domains=[client_host] if client_host else [],
        competitor_domains=[competitor_host] if competitor_host else [],
        engine_codes=engine_codes,
    )
    live_engines = [e.engine_name for e in ai_visibility_report.engine_reports if e.available]
    stages.append(
        _stage(
            "ai_visibility",
            "completed" if live_engines else "completed",
            f"Ran {len(ai_visibility_report.queries)} representative queries; {len(live_engines)} live plugin(s): {', '.join(live_engines) or 'none configured'}.",
        )
    )

    # 3) LLM Intelligence Extraction + Citation Gap Engine
    citations = [CitationSignal(**c) for c in site_report.raw_citations]
    citation_gap_report: CitationGapReport = await analyse_citation_gaps(
        client_brand=brand, citations=citations, client_site_text=site_report.site_text_sample
    )
    stages.append(
        _stage(
            "citation_gap_analysis",
            "completed" if citations else "skipped",
            f"Analysed {citation_gap_report.citations_analysed} of {citation_gap_report.citations_observed} observed citation(s)."
            if citations
            else "No citations were observed across the available AI plugins for this research prompt.",
        )
    )

    # 4) Opportunity Engine — TOP ACTIONS TO TAKE (generalised Peacock Impact Score)
    opportunities = []
    for action in site_report.top_actions[:10]:
        opportunities.append(
            build_opportunity(
                action=action.title,
                reason=action.detail,
                affected_page=url,
                seo_opportunity=action.seo_opportunity,
                aeo_opportunity="Medium",
                geo_opportunity=action.geo_opportunity,
                ai_visibility_opportunity="High" if ai_visibility_report.universal_share_of_answer is not None and ai_visibility_report.universal_share_of_answer < 0.5 else "Medium",
                business_value="High" if action.competitors_winning else "Medium",
                competitor_gap="High" if action.competitors_winning else "Low",
                implementation_difficulty=action.difficulty,
                confidence=action.confidence,
            )
        )
    top_opportunities = rank_opportunities(opportunities, limit=10)
    stages.append(_stage("opportunity_engine", "completed", f"Ranked {len(top_opportunities)} opportunit(y/ies) by Peacock Impact Score."))

    # 5) Content Strategy Engine — graph + recommendations
    content_recs = recommend_content_types(
        missing_topics=site_report.content_gaps,
        missing_entities=site_report.entity_opportunities,
        competitor_names=competitors,
        has_information_gain_gap=site_report.information_gain_score < 50,
    )
    content_graph = build_content_graph(
        brand=brand,
        topics=topics,
        entities=site_report.entity_opportunities,
        keywords=site_report.keyword_opportunities.universal_terms,
        queries=[(q.query_text, q.intent) for q in ai_visibility_report.queries],
        pages=[(p.url, p.title or p.url) for p in site_report.pages],
    )
    stages.append(_stage("content_strategy", "completed", f"Proposed {len(content_recs)} content item(s); built a {len(content_graph.nodes)}-node relationship graph."))

    # 6) Content Creation Studio — CREATE WITH PEACOCK (top recommendation only)
    top_brief = None
    content_simulation = None
    if content_recs:
        top_rec = content_recs[0]
        top_brief = generate_content_brief(
            topic=top_rec.target_topics[0] if top_rec.target_topics else top_rec.title,
            brand=brand,
            related_entities=site_report.entity_opportunities[:5],
            related_questions=[q.query_text for q in ai_visibility_report.queries if q.intent == "informational"],
            internal_link_candidates=[p.url for p in site_report.pages[:5]],
            content_type=top_rec.content_type,
        )
        stages.append(_stage("content_creation", "completed", f"Generated a content brief for '{top_brief.topic}' (CREATE WITH PEACOCK)."))

        # 7) Multi-LLM Content Simulator + Optimizer readiness
        content_simulation = await simulate_multi_llm_readiness(
            llm_gateway=llm_gateway,
            draft_text=top_brief.draft_skeleton,
            topic=top_brief.topic,
            brand=brand,
            site_key_terms=site_report.site_key_terms,
            engine_codes=engine_codes,
        )
        stages.append(
            _stage(
                "multi_llm_simulation_and_optimization",
                "completed",
                f"GEO readiness estimate {content_simulation['geo_score_breakdown']['geo_score']}/100 for the draft brief.",
            )
        )
    else:
        stages.append(_stage("content_creation", "skipped", "No content gaps detected to brief."))
        stages.append(_stage("multi_llm_simulation_and_optimization", "skipped", "No draft available to simulate."))

    # 8) AI Agents — analyse, recommend, prepare tasks/drafts (never destructive)
    agent_results = {
        "seo_agent": run_seo_agent(site_report).to_dict(),
        "aeo_agent": run_aeo_agent(site_report).to_dict(),
        "geo_agent": run_geo_agent(site_report).to_dict(),
        "research_agent": run_research_agent(ai_visibility_report).to_dict(),
        "content_strategist_agent": run_content_strategist_agent(content_recs).to_dict(),
        "competitor_agent": run_competitor_agent(site_report.competitor_gap).to_dict(),
        "citation_agent": run_citation_agent(citation_gap_report).to_dict(),
        "internal_linking_agent": run_internal_linking_agent(site_report).to_dict(),
        "technical_seo_agent": run_technical_seo_agent(site_report.technical_health).to_dict(),
    }
    stages.append(_stage("ai_agents", "completed", f"{len(agent_results)} agent(s) analysed the results and prepared recommendations/tasks."))

    # 9) Human Experts — create a pending review task for the top opportunity/brief
    expert_task = None
    if top_brief is not None:
        task = create_task(
            title=f"Review content brief: {top_brief.topic}",
            task_type="content_brief",
            content=top_brief.draft_skeleton,
        )
        expert_task = task.to_dict()
        stages.append(_stage("human_experts", "completed", f"Created review task '{task.title}' (status: {task.status}) — awaiting human assignment."))
    else:
        stages.append(_stage("human_experts", "skipped", "No content brief was generated this run."))

    # 10) Publishing — preview only, always requires explicit confirmation
    publishing_preview = None
    if top_brief is not None:
        connector = get_connector("manual")
        result = await connector.publish(
            PublishRequest(title=top_brief.suggested_title, body=top_brief.draft_skeleton, meta_description=top_brief.suggested_meta_description),
            confirm=False,
        )
        publishing_preview = result.to_dict()
        stages.append(_stage("publishing", "completed", "Publishing preview prepared — requires explicit human confirmation before anything is marked ready."))
    else:
        stages.append(_stage("publishing", "skipped", "No draft available to preview for publishing."))

    # 11) Measurement — capture this run's real snapshot for future before/after comparison
    snapshot = capture_snapshot(
        url=url,
        seo_score=site_report.seo_score,
        aeo_score=site_report.aeo_score,
        geo_score=site_report.geo_score,
        information_gain_score=site_report.information_gain_score,
        word_count=site_report.total_word_count,
        content_hash=None,
        citations_count=len(citations),
        universal_share_of_answer=ai_visibility_report.universal_share_of_answer,
    )
    stages.append(_stage("measurement", "completed", f"Captured a Peacock-computed snapshot at {snapshot.captured_at.isoformat()} for future before/after comparison."))

    # 12) Experiments — suggested, not auto-run (kept as a top opportunity list; see experiment_engine to log one)
    stages.append(_stage("experiments", "completed", "Top opportunities are ready to be logged as experiments (see /growth-loop/experiments)."))

    # 13) Learning — log the top recommendation for future outcome tracking
    learning_record = None
    if top_opportunities:
        top = top_opportunities[0]
        record = log_recommendation(
            recommendation=top.action,
            recommendation_type="growth_loop_top_action",
            page_url=url,
            baseline_score=site_report.peacock_visibility_score,
            confidence_at_log_time=top.confidence,
        )
        learning_record = record.to_dict()
        stages.append(_stage("learning", "completed", f"Logged '{top.action}' for outcome tracking (baseline {site_report.peacock_visibility_score}/100)."))
    else:
        stages.append(_stage("learning", "skipped", "No opportunities were ranked this run."))

    executive_summary = {
        "peacock_visibility_score": site_report.peacock_visibility_score,
        "seo": site_report.seo_score,
        "aeo": site_report.aeo_score,
        "geo": site_report.geo_score,
        "ai_visibility": ai_visibility_report.universal_share_of_answer,
        "citation_authority": len(citation_gap_report.gaps),
        "entity_authority": site_report.geo_score_breakdown.entity_authority.score,
        "content_authority": site_report.geo_score_breakdown.evidence.score,
        "technical_health": site_report.technical_health.get("peacock_seo_score", {}).get("score"),
        "information_gain": site_report.information_gain_score,
        "competitive_position": "See competitor_gap" if site_report.competitor_gap.available else "Data unavailable — no competitor URL supplied",
        "what_changed": "This is the first Growth Loop run captured for this URL in this session — re-run later to see before/after.",
        "why": site_report.executive_summary,
        "what_should_we_do_next": top_opportunities[0].action if top_opportunities else "No ranked opportunity available.",
        "highest_impact_opportunity": top_opportunities[0].to_dict() if top_opportunities else None,
        "which_agent_is_working": list(agent_results.keys()),
        "requires_human_approval": [expert_task] if expert_task else [],
        "what_worked": "Data unavailable — requires at least one completed experiment or learning outcome.",
        "what_failed": "Data unavailable — requires at least one completed experiment or learning outcome.",
    }

    return GrowthLoopReport(
        url=url,
        brand=brand,
        stages=stages,
        site_intelligence=site_report.to_dict(),
        ai_visibility=ai_visibility_report.to_dict(),
        citation_gaps=citation_gap_report.to_dict(),
        content_recommendations=[r.to_dict() for r in content_recs],
        content_graph=content_graph.to_dict(),
        top_content_brief=top_brief.to_dict() if top_brief else None,
        content_simulation=content_simulation,
        top_opportunities=[o.to_dict() for o in top_opportunities],
        agent_results=agent_results,
        expert_task=expert_task,
        publishing_preview=publishing_preview,
        measurement_snapshot=snapshot.to_dict(),
        learning_record=learning_record,
        executive_summary=executive_summary,
    )
