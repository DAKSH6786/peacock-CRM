"""Peacock Revenue Attribution API — visibility → revenue with uncertainty."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas_revenue_attribution import (
    ChainLinkResponse,
    RevenueAttributionCatalogResponse,
    RevenueAttributionRequest,
    RevenueAttributionResponse,
    SourceSnapshotResponse,
    StageResponse,
)
from observability.audit import AuditEvent, AuditLogger
from revenue_attribution import (
    CAUSALITY_LEVELS,
    CAUSALITY_WARNING,
    DATA_SOURCES,
    FUNNEL_STAGES,
    METHODOLOGY,
    METHODOLOGY_NOTE,
    SOURCE_LABELS,
    STAGE_LABELS,
    AttributionSpec,
    RevenueAttributionService,
    RevenueAttributionSpec,
    SourceAvailability,
    StageObservation,
)

router = APIRouter(prefix="/revenue-attribution", tags=["revenue-attribution"])
audit_logger = AuditLogger()


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


def _to_response(report) -> RevenueAttributionResponse:
    r = report.result
    return RevenueAttributionResponse(
        analysis_id=report.analysis_id,
        name=report.name,
        client_brand=report.client_brand,
        methodology=report.methodology,
        currency=r.currency,
        horizon_days=r.horizon_days,
        stages=[StageResponse(**s.to_dict()) for s in r.stages],
        links=[ChainLinkResponse(**l.to_dict()) for l in r.links],
        source_snapshots=[
            SourceSnapshotResponse(**s.to_dict()) for s in r.source_snapshots
        ],
        attributed_revenue_low=r.attributed_revenue_low,
        attributed_revenue_high=r.attributed_revenue_high,
        attributed_revenue_mid=r.attributed_revenue_mid,
        overall_causality_level=r.overall_causality_level,
        overall_uncertainty=r.overall_uncertainty,
        data_completeness=r.data_completeness,
        causality_warning=r.causality_warning,
        methodology_note=r.methodology_note,
        sources_available=r.sources_available,
        sources_missing=r.sources_missing,
        funnel_path=r.funnel_path,
        summary=r.summary,
    )


@router.get("/catalog", response_model=RevenueAttributionCatalogResponse)
def revenue_attribution_catalog(
    ctx: AuthContext = Depends(get_auth_context),
) -> RevenueAttributionCatalogResponse:
    _ = ctx
    return RevenueAttributionCatalogResponse(
        funnel_stages=dict(STAGE_LABELS),
        funnel_path=[STAGE_LABELS[c] for c in FUNNEL_STAGES],
        data_sources=dict(SOURCE_LABELS),
        causality_levels=list(CAUSALITY_LEVELS),
        causality_warning=CAUSALITY_WARNING,
        methodology=METHODOLOGY,
        methodology_note=METHODOLOGY_NOTE,
    )


@router.post("/analyses", response_model=RevenueAttributionResponse, status_code=201)
def create_revenue_attribution_analysis(
    body: RevenueAttributionRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> RevenueAttributionResponse:
    ws = _workspace_id(ctx, body.workspace_id)
    try:
        report = RevenueAttributionService(db).analyse(
            organisation_id=ctx.organisation.id,
            workspace_id=ws,
            created_by=ctx.user.id,
            spec=RevenueAttributionSpec(
                website_id=body.website_id,
                name=body.name,
                attribution=AttributionSpec(
                    client_brand=body.brief.client_brand,
                    currency=body.brief.currency,
                    horizon_days=body.brief.horizon_days,
                    sources=SourceAvailability(**body.brief.sources.model_dump()),
                    observations=[
                        StageObservation(**o.model_dump())
                        for o in body.brief.observations
                    ],
                    recommendation_ref=body.brief.recommendation_ref,
                    content_ref=body.brief.content_ref,
                ),
                notes=body.notes,
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_logger.log(
        AuditEvent(
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            action="revenue_attribution.analyse",
            resource_type="revenue_attribution_analysis",
            resource_id=report.analysis_id,
            workspace_id=ws,
            metadata={
                "overall_causality_level": report.result.overall_causality_level,
                "overall_uncertainty": report.result.overall_uncertainty,
                "do_not_overclaim_causality": True,
            },
        )
    )
    return _to_response(report)


@router.get("/analyses/{analysis_id}", response_model=RevenueAttributionResponse)
def get_revenue_attribution_analysis(
    analysis_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> RevenueAttributionResponse:
    report = RevenueAttributionService(db).get_analysis(
        analysis_id=analysis_id,
        organisation_id=ctx.organisation.id,
    )
    if report is None:
        raise HTTPException(status_code=404, detail="Revenue attribution analysis not found")
    return _to_response(report)
