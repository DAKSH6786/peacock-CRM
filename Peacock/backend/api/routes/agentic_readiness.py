"""Peacock Agentic Web Readiness API — Agent Discoverability + Agent Readiness Score."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from agentic_readiness import (
    CHECK_LABELS,
    DISCOVERABILITY_CHECKS,
    METHODOLOGY,
    METHODOLOGY_NOTE,
    NOT_INDUSTRY_STANDARD,
    SURFACE_SEPARATION,
    AgenticReadinessService,
    AgenticReadinessSpec,
    CheckSignal,
    ReadinessSpec,
)
from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas_agentic_readiness import (
    AgenticReadinessCatalogResponse,
    AgenticReadinessRequest,
    AgenticReadinessResponse,
    CheckResultResponse,
    GapResponse,
)
from observability.audit import AuditEvent, AuditLogger

router = APIRouter(prefix="/agentic-readiness", tags=["agentic-readiness"])
audit_logger = AuditLogger()


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


def _to_response(report) -> AgenticReadinessResponse:
    r = report.result
    return AgenticReadinessResponse(
        analysis_id=report.analysis_id,
        name=report.name,
        client_brand=report.client_brand,
        methodology=report.methodology,
        agent_readiness_score=r.agent_readiness_score,
        readiness_band=r.readiness_band,
        checks=[CheckResultResponse(**c.to_dict()) for c in r.checks],
        gaps=[GapResponse(**g.to_dict()) for g in r.gaps],
        checks_passed=r.checks_passed,
        checks_total=r.checks_total,
        separate_from_seo_aeo_geo=True,
        surface_separation_note=r.surface_separation_note,
        not_industry_standard=True,
        not_industry_standard_note=r.not_industry_standard_note,
        methodology_note=r.methodology_note,
        summary=r.summary,
    )


@router.get("/catalog", response_model=AgenticReadinessCatalogResponse)
def agentic_readiness_catalog(
    ctx: AuthContext = Depends(get_auth_context),
) -> AgenticReadinessCatalogResponse:
    _ = ctx
    return AgenticReadinessCatalogResponse(
        discoverability_checks=dict(CHECK_LABELS),
        check_codes=list(DISCOVERABILITY_CHECKS),
        methodology=METHODOLOGY,
        methodology_note=METHODOLOGY_NOTE,
        surface_separation_note=SURFACE_SEPARATION,
        not_industry_standard_note=NOT_INDUSTRY_STANDARD,
        separate_from_seo_aeo_geo=True,
        not_industry_standard=True,
        readiness_bands=["nascent", "emerging", "operable", "agent_ready"],
    )


@router.post("/analyses", response_model=AgenticReadinessResponse, status_code=201)
def create_agentic_readiness_analysis(
    body: AgenticReadinessRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> AgenticReadinessResponse:
    ws = _workspace_id(ctx, body.workspace_id)
    try:
        report = AgenticReadinessService(db).analyse(
            organisation_id=ctx.organisation.id,
            workspace_id=ws,
            created_by=ctx.user.id,
            spec=AgenticReadinessSpec(
                website_id=body.website_id,
                name=body.name,
                readiness=ReadinessSpec(
                    client_brand=body.brief.client_brand,
                    industry=body.brief.industry,
                    business_type=body.brief.business_type,
                    signals=[
                        CheckSignal(**s.model_dump()) for s in body.brief.signals
                    ],
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
            action="agentic_readiness.analyse",
            resource_type="agentic_readiness_analysis",
            resource_id=report.analysis_id,
            workspace_id=ws,
            metadata={
                "agent_readiness_score": report.result.agent_readiness_score,
                "readiness_band": report.result.readiness_band,
                "separate_from_seo_aeo_geo": True,
                "not_industry_standard": True,
            },
        )
    )
    return _to_response(report)


@router.get("/analyses/{analysis_id}", response_model=AgenticReadinessResponse)
def get_agentic_readiness_analysis(
    analysis_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> AgenticReadinessResponse:
    report = AgenticReadinessService(db).get_analysis(
        analysis_id=analysis_id,
        organisation_id=ctx.organisation.id,
    )
    if report is None:
        raise HTTPException(status_code=404, detail="Agentic readiness analysis not found")
    return _to_response(report)
