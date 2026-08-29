"""Peacock Site Intelligence API — the enterprise SEO + GEO reporting engine.

Public and stateless for now (no DB, no auth — consistent with auth being
disabled for the rest of the application at this stage). Performs a REAL
crawl of the requested URL (and, optionally, a competitor URL) through the
existing Peacock Crawler, so responses take a few seconds and depend on
outbound network access to the target site.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request

from api.schemas_site_intelligence import SiteIntelligenceAnalyzeRequest
from llm_gateway.registry import LLMGateway
from site_intelligence import run_site_intelligence_report

router = APIRouter(prefix="/site-intelligence", tags=["site-intelligence"])


def _gateway_from_request(request: Request) -> LLMGateway | None:
    return getattr(request.app.state, "llm_gateway", None)


@router.post("/analyze")
async def analyze_site(body: SiteIntelligenceAnalyzeRequest, request: Request) -> dict[str, Any]:
    """Crawl -> Understand -> Benchmark -> Query LLMs -> Extract AI Signals ->
    Compare Competitors -> Identify Gaps -> Prioritize Opportunities ->
    Generate Exact Fixes.
    """
    try:
        report = await run_site_intelligence_report(
            llm_gateway=_gateway_from_request(request),
            url=body.url,
            competitor_url=body.competitor_url,
            max_pages=body.max_pages,
            engine_codes=body.engine_codes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 — surface as a clean error, never a bare 500 stack trace
        raise HTTPException(status_code=502, detail=f"Site analysis failed: {exc}") from exc
    return report.to_dict()
