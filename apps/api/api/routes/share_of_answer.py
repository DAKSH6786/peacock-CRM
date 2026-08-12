"""Share of Answer API — multi-indicator generative influence (not token-only)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas_share_of_answer import (
    BrandShareResponse,
    ShareOfAnswerRequest,
    ShareOfAnswerResponse,
    SoaCatalogResponse,
)
from db_models.share_of_answer import COMPARISON_OUTCOMES, SOA_INDICATORS
from observability.audit import AuditEvent, AuditLogger
from share_of_answer import (
    AnswerObservationSpec,
    DEFAULT_INDICATOR_WEIGHTS,
    ShareOfAnswerService,
    ShareOfAnswerSpec,
)

router = APIRouter(prefix="/share-of-answer", tags=["share-of-answer"])
audit_logger = AuditLogger()


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


def _to_response(report) -> ShareOfAnswerResponse:
    brands = [BrandShareResponse(**b.to_dict()) for b in report.brands]
    example_display = [
        {
            "brand": b.entity_name,
            "share_of_answer_pct": round(b.share_of_answer, 1),
            "is_client": b.is_client,
        }
        for b in report.brands
    ]
    return ShareOfAnswerResponse(
        analysis_id=report.analysis_id,
        query_cluster=report.query_cluster,
        client_brand=report.client_brand,
        methodology=report.methodology,
        token_count_alone_rejected=report.token_count_alone_rejected,
        observation_count=report.observation_count,
        brands=brands,
        indicator_weights=report.indicator_weights,
        example_display=example_display,
    )


@router.get("/catalog", response_model=SoaCatalogResponse)
def soa_catalog(ctx: AuthContext = Depends(get_auth_context)) -> SoaCatalogResponse:
    _ = ctx
    return SoaCatalogResponse(
        indicators=list(SOA_INDICATORS),
        default_weights=dict(DEFAULT_INDICATOR_WEIGHTS),
        comparison_outcomes=list(COMPARISON_OUTCOMES),
        methodology_note=(
            "Share of Answer uses multiple indicators. Token span is diagnostic only "
            "and never treated as influence by itself."
        ),
    )


@router.post("/analyses", response_model=ShareOfAnswerResponse, status_code=201)
def create_share_of_answer_analysis(
    body: ShareOfAnswerRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> ShareOfAnswerResponse:
    ws = _workspace_id(ctx, body.workspace_id)
    try:
        report = ShareOfAnswerService(db).analyse(
            organisation_id=ctx.organisation.id,
            workspace_id=ws,
            created_by=ctx.user.id,
            spec=ShareOfAnswerSpec(
                website_id=body.website_id,
                name=body.name,
                query_cluster=body.query_cluster,
                client_brand=body.client_brand,
                competitor_brands=body.competitor_brands,
                observations=[
                    AnswerObservationSpec(**o.model_dump()) for o in body.observations
                ],
                notes=body.notes,
                indicator_weights=body.indicator_weights,
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_logger.log(
        AuditEvent(
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            action="share_of_answer.analyse",
            resource_type="share_of_answer_analysis",
            resource_id=report.analysis_id,
            workspace_id=ws,
            metadata={
                "query_cluster": report.query_cluster,
                "brands": len(report.brands),
                "token_count_alone_rejected": True,
            },
        )
    )
    return _to_response(report)


@router.get("/analyses/{analysis_id}", response_model=ShareOfAnswerResponse)
def get_share_of_answer_analysis(
    analysis_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> ShareOfAnswerResponse:
    report = ShareOfAnswerService(db).get_report(
        analysis_id=analysis_id,
        organisation_id=ctx.organisation.id,
    )
    if report is None:
        raise HTTPException(status_code=404, detail="Share of Answer analysis not found")
    return _to_response(report)
