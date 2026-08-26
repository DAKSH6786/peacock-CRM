"""Peacock GEO Intelligence orchestrator.

Wires the architecture end to end:

    AI Plugins -> Peacock AI Gateway -> Multi-LLM Response Collection ->
    Peacock GEO Intelligence Layer -> Keyword/Entity/Citation Extraction ->
    Platform-Specific GEO Recommendations -> Peacock One Dashboard
"""

from __future__ import annotations

from llm_gateway.registry import LLMGateway

from geo_intelligence.demo_content import default_simulated_responses
from geo_intelligence.extraction import extract_geo_intelligence
from geo_intelligence.gateway import DEFAULT_ENGINE_CODES, PeacockAIGateway
from geo_intelligence.models import GeoIntelligenceReport
from geo_intelligence.recommendations import build_platform_recommendations

DEFAULT_COMPETITORS: list[str] = ["Semrush", "Ahrefs"]
DEFAULT_SITE_TOPICS: list[str] = [
    "seo audits",
    "keyword research",
    "backlink analysis",
    "rank tracking",
    "technical seo",
]


def build_research_prompt(client_brand: str, competitors: list[str]) -> str:
    competitor_clause = ", ".join(competitors) if competitors else "its main competitors"
    return (
        f"I'm researching AI visibility and generative engine optimisation (GEO) tools. "
        f"How does {client_brand} compare to {competitor_clause}? What questions do people ask "
        f"about this category, which sources do you rely on, and which brand would you "
        f"recommend for tracking AI search visibility and why?"
    )


async def run_geo_intelligence(
    *,
    llm_gateway: LLMGateway | None,
    organisation_id: str,
    client_brand: str = "Acme",
    competitors: list[str] | None = None,
    site_topics: list[str] | None = None,
    research_prompt: str | None = None,
    engine_codes: list[str] | None = None,
    client_domains: list[str] | None = None,
    competitor_domains: list[str] | None = None,
    workspace_id: str | None = None,
) -> GeoIntelligenceReport:
    brand = (client_brand or "Acme").strip() or "Acme"
    competitors = [c.strip() for c in (competitors or DEFAULT_COMPETITORS) if c and c.strip()]
    site_topics = [t.strip() for t in (site_topics or DEFAULT_SITE_TOPICS) if t and t.strip()]
    codes = [c for c in (engine_codes or list(DEFAULT_ENGINE_CODES)) if c]
    prompt = (research_prompt or "").strip() or build_research_prompt(brand, competitors)

    gateway = PeacockAIGateway(llm_gateway)
    provider_responses = await gateway.broadcast(
        organisation_id=organisation_id,
        workspace_id=workspace_id,
        research_prompt=prompt,
        engine_codes=codes,
        simulated_responses=default_simulated_responses(brand, competitors),
    )

    extraction = extract_geo_intelligence(
        client_brand=brand,
        competitors=competitors,
        site_topics=site_topics,
        responses=provider_responses,
        client_domains=client_domains,
        competitor_domains=competitor_domains,
    )

    recommendations = build_platform_recommendations(
        client_brand=brand,
        responses=provider_responses,
        extraction=extraction,
    )

    return GeoIntelligenceReport(
        client_brand=brand,
        research_prompt=prompt,
        competitors=competitors,
        site_topics=site_topics,
        provider_responses=provider_responses,
        extraction=extraction,
        recommendations=recommendations,
    )
