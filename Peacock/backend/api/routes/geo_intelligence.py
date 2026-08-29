"""Peacock GEO Intelligence API — AI Gateway + multi-LLM extraction + platform recommendations.

Architecture:
    AI Plugins -> Peacock AI Gateway -> Multi-LLM Response Collection ->
    Peacock GEO Intelligence Layer -> Keyword/Entity/Citation Extraction ->
    Platform-Specific GEO Recommendations -> Peacock One Dashboard

These endpoints are intentionally public and DB-free — same "preview" posture
as the other module endpoints — so the dashboard's GEO Intelligence module and
its connections into the Website Audit, Blog, Keyword/Backlink, AI Visibility,
and Content Optimizer modules all work in local development with zero
credentials or a running database. Whichever AI plugins have an API key set as
an environment variable are called live through the existing LLM Gateway
adapters; the rest fall back to clearly labelled simulated content.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from api.schemas_geo_intelligence import (
    AiGatewayCatalogResponse,
    AiPluginStatusSchema,
    GeoIntelligenceAnalysisRequest,
    GeoIntelligenceResponse,
)
from geo_intelligence import (
    ENGINE_META,
    GEO_DISCLAIMER,
    METHODOLOGY_NOTE,
    DEFAULT_COMPETITORS,
    DEFAULT_SITE_TOPICS,
    PeacockAIGateway,
    run_geo_intelligence,
)
from llm_gateway.registry import LLMGateway

router = APIRouter(prefix="/geo-intelligence", tags=["geo-intelligence"])


def _gateway_from_request(request: Request) -> LLMGateway | None:
    return getattr(request.app.state, "llm_gateway", None)


def _to_response(report) -> GeoIntelligenceResponse:
    return GeoIntelligenceResponse(**report.to_dict())


@router.get("/plugins", response_model=AiGatewayCatalogResponse)
def ai_gateway_plugin_catalog(request: Request) -> AiGatewayCatalogResponse:
    """Public plugin catalog — which of the 5 AI plugins currently have a live API key."""
    llm_gateway = _gateway_from_request(request)
    ai_gateway = PeacockAIGateway(llm_gateway)
    live_codes = ai_gateway.available_engine_codes()
    return AiGatewayCatalogResponse(
        plugins=[
            AiPluginStatusSchema(
                engine_code=code,
                engine_name=meta["name"],
                provider_code=meta["provider"],
                live=code in live_codes,
            )
            for code, meta in ENGINE_META.items()
        ],
        disclaimer=GEO_DISCLAIMER,
        methodology_note=METHODOLOGY_NOTE,
    )


@router.get("/preview", response_model=GeoIntelligenceResponse)
async def geo_intelligence_preview(request: Request, brand: str = "Acme") -> GeoIntelligenceResponse:
    """Public demo run of the full AI Gateway -> GEO Intelligence -> recommendations pipeline."""
    report = await run_geo_intelligence(
        llm_gateway=_gateway_from_request(request),
        organisation_id="preview",
        client_brand=brand,
        competitors=DEFAULT_COMPETITORS,
        site_topics=DEFAULT_SITE_TOPICS,
    )
    return _to_response(report)


@router.post("/analyses", response_model=GeoIntelligenceResponse)
async def geo_intelligence_analysis(
    body: GeoIntelligenceAnalysisRequest, request: Request
) -> GeoIntelligenceResponse:
    """Run the pipeline with caller-supplied brand/competitors/topics/prompt/plugins.

    Public and stateless for now (no persistence, no auth) — consistent with the
    other module preview endpoints while auth is disabled.
    """
    report = await run_geo_intelligence(
        llm_gateway=_gateway_from_request(request),
        organisation_id="anonymous",
        client_brand=body.client_brand,
        competitors=body.competitors or DEFAULT_COMPETITORS,
        site_topics=body.site_topics or DEFAULT_SITE_TOPICS,
        research_prompt=body.research_prompt,
        engine_codes=body.engine_codes,
        client_domains=body.client_domains,
        competitor_domains=body.competitor_domains,
    )
    return _to_response(report)
