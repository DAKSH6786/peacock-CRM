"""Deep Competitor Intelligence API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas_deep_competitor import (
    ContentDiffResponse,
    DeepCompetitorCatalogResponse,
    DeepCompetitorRequest,
    DeepCompetitorResponse,
    DeltaResponse,
    DiscoveredCompetitorResponse,
    StrategyResponse,
)
from deep_competitor import (
    COMPETITOR_CATEGORIES,
    CONTENT_COMPARE_DIMENSIONS,
    DISCOVERY_SIGNALS,
    FORBIDDEN_RECOMMENDATION_MODES,
    DeepCompetitorService,
)
from deep_competitor.delta import DimensionScoreInput
from deep_competitor.discovery import DiscoverySignalInput
from deep_competitor.models import DeepCompetitorSpec
from deep_competitor.reverse_content import ContentDimensionInput
from observability.audit import AuditEvent, AuditLogger

router = APIRouter(prefix="/deep-competitors", tags=["deep-competitors"])
audit_logger = AuditLogger()


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


def _to_response(report) -> DeepCompetitorResponse:
    return DeepCompetitorResponse(
        analysis_id=report.analysis_id,
        client_brand=report.client_brand,
        client_domain=report.client_domain,
        methodology=report.methodology,
        copy_competitor_content_rejected=True,
        competitors=[DiscoveredCompetitorResponse(**c.to_dict()) for c in report.competitors],
        deltas=[DeltaResponse(**d.to_dict()) for d in report.deltas],
        content_diffs=[ContentDiffResponse(**c.to_dict()) for c in report.content_diffs],
        strategies=[StrategyResponse(**s.to_dict()) for s in report.strategies],
        category_breakdown=report.category_breakdown,
        example_discovery=report.example_discovery,
        example_delta=report.example_delta,
    )


@router.get("/catalog", response_model=DeepCompetitorCatalogResponse)
def deep_competitor_catalog(
    ctx: AuthContext = Depends(get_auth_context),
) -> DeepCompetitorCatalogResponse:
    _ = ctx
    return DeepCompetitorCatalogResponse(
        competitor_categories=list(COMPETITOR_CATEGORIES),
        discovery_signals=list(DISCOVERY_SIGNALS),
        content_compare_dimensions=list(CONTENT_COMPARE_DIMENSIONS),
        forbidden_recommendation_modes=list(FORBIDDEN_RECOMMENDATION_MODES),
        methodology_note=(
            "Deep Competitor Intelligence discovers rivals dynamically across "
            "business/search/content/AI/citation/entity/SERP categories. "
            "A strong SEO competitor need not be a direct business competitor. "
            "Strategies are differentiated — never copy competitor content."
        ),
    )


@router.post("/analyses", response_model=DeepCompetitorResponse, status_code=201)
def create_deep_competitor_analysis(
    body: DeepCompetitorRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> DeepCompetitorResponse:
    ws = _workspace_id(ctx, body.workspace_id)
    try:
        report = DeepCompetitorService(db).analyse(
            organisation_id=ctx.organisation.id,
            workspace_id=ws,
            created_by=ctx.user.id,
            spec=DeepCompetitorSpec(
                website_id=body.website_id,
                name=body.name,
                client_brand=body.client_brand,
                client_domain=body.client_domain,
                topic_cluster=body.topic_cluster,
                discovery_candidates=[
                    DiscoverySignalInput(**c.model_dump()) for c in body.discovery_candidates
                ],
                dimension_scores=[
                    DimensionScoreInput(**d.model_dump()) for d in body.dimension_scores
                ],
                content_comparisons=[
                    ContentDimensionInput(**c.model_dump()) for c in body.content_comparisons
                ],
                notes=body.notes,
                min_rivalry=body.min_rivalry,
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_logger.log(
        AuditEvent(
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            action="deep_competitor.analyse",
            resource_type="deep_competitor_analysis",
            resource_id=report.analysis_id,
            workspace_id=ws,
            metadata={
                "discovered": len(report.competitors),
                "copy_rejected": True,
            },
        )
    )
    return _to_response(report)


@router.get("/analyses/{analysis_id}", response_model=DeepCompetitorResponse)
def get_deep_competitor_analysis(
    analysis_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> DeepCompetitorResponse:
    report = DeepCompetitorService(db).get_report(
        analysis_id=analysis_id,
        organisation_id=ctx.organisation.id,
    )
    if report is None:
        raise HTTPException(status_code=404, detail="Deep Competitor analysis not found")
    return _to_response(report)
