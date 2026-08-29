"""Peacock Executive Brain API — CEO/CMO executive view."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from executive_brain import (
    ExecutiveBrainCreateSpec,
    ExecutiveBrainService,
    ExecutiveBrainSpec,
    ExecutiveSignal,
    catalog,
    synthesise_executive_brain,
)
from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas_executive_brain import (
    ExecutiveAnswerResponse,
    ExecutiveBrainCatalogResponse,
    ExecutiveBrainCreateRequest,
    ExecutiveBrainPreviewResponse,
    ExecutiveBrainResponse,
    RoleSummaryResponse,
)
from observability.audit import AuditEvent, AuditLogger

router = APIRouter(prefix="/executive-brain", tags=["executive-brain"])
audit_logger = AuditLogger()


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


def _result_fields(result) -> dict:
    return {
        "generated_at": result.generated_at.isoformat(),
        "horizon_days": result.horizon_days,
        "budget_label": result.budget_label,
        "overall_confidence": result.overall_confidence,
        "headline": result.headline,
        "answers": [ExecutiveAnswerResponse(**a.to_dict()) for a in result.answers],
        "role_summaries": [
            RoleSummaryResponse(**r.to_dict()) for r in result.role_summaries
        ],
        "methodology_note": result.methodology_note,
        "summary": result.summary,
    }


def _to_response(report) -> ExecutiveBrainResponse:
    return ExecutiveBrainResponse(
        brief_id=report.brief_id,
        name=report.name,
        client_brand=report.client_brand,
        methodology=report.methodology,
        **_result_fields(report.result),
    )


@router.get("/catalog", response_model=ExecutiveBrainCatalogResponse)
def executive_brain_catalog(
    ctx: AuthContext = Depends(get_auth_context),
) -> ExecutiveBrainCatalogResponse:
    _ = ctx
    return ExecutiveBrainCatalogResponse(**catalog())


@router.get("/preview", response_model=ExecutiveBrainPreviewResponse)
def executive_brain_preview(
    brand: str = "Acme",
    competitor: str = "Competitor A",
    budget: str = "₹10 lakh",
    horizon_days: int = 90,
) -> ExecutiveBrainPreviewResponse:
    """Public demo brief for the executive UI."""
    result = synthesise_executive_brain(
        ExecutiveBrainSpec(
            client_brand=brand,
            competitor_name=competitor,
            budget_label=budget,
            horizon_days=horizon_days,
        )
    )
    return ExecutiveBrainPreviewResponse(
        client_brand=result.client_brand,
        **_result_fields(result),
    )


@router.post("/briefs", response_model=ExecutiveBrainResponse, status_code=201)
def create_executive_brief(
    body: ExecutiveBrainCreateRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> ExecutiveBrainResponse:
    ws = _workspace_id(ctx, body.workspace_id)
    try:
        report = ExecutiveBrainService(db).create_brief(
            organisation_id=ctx.organisation.id,
            workspace_id=ws,
            created_by=ctx.user.id,
            spec=ExecutiveBrainCreateSpec(
                website_id=body.website_id,
                name=body.name,
                brief=ExecutiveBrainSpec(
                    client_brand=body.brief.client_brand,
                    competitor_name=body.brief.competitor_name,
                    budget_label=body.brief.budget_label,
                    horizon_days=body.brief.horizon_days,
                    signals=[
                        ExecutiveSignal(
                            key=s.key,
                            value=s.value,
                            polarity=s.polarity,
                            weight=s.weight,
                        )
                        for s in body.brief.signals
                    ],
                    generated_at=body.brief.generated_at,
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
            action="executive_brain.brief",
            resource_type="executive_brain_brief",
            resource_id=report.brief_id,
            workspace_id=ws,
            metadata={
                "overall_confidence": report.result.overall_confidence,
                "horizon_days": report.result.horizon_days,
            },
        )
    )
    return _to_response(report)


@router.get("/briefs/{brief_id}", response_model=ExecutiveBrainResponse)
def get_executive_brief(
    brief_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> ExecutiveBrainResponse:
    report = ExecutiveBrainService(db).get_brief(
        brief_id=brief_id,
        organisation_id=ctx.organisation.id,
    )
    if report is None:
        raise HTTPException(status_code=404, detail="Executive Brain brief not found")
    return _to_response(report)
