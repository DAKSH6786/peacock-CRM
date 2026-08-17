"""Answer Engine Optimisation (AEO) API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from aeo_engine import AeoAnalysisService, AeoEngine
from api.db import get_db
from api.deps import AuthContext, get_auth_context, require_writer
from api.schemas_aeo import AeoAnalysisRequest, AeoAnalysisResponse
from observability.audit import AuditEvent, AuditLogger

router = APIRouter(prefix="/aeo", tags=["aeo"])
audit = AuditLogger()


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


@router.get("/catalog")
def aeo_catalog(ctx: AuthContext = Depends(get_auth_context)) -> dict:
    return {
        **AeoEngine(ctx.organisation.id).status(),
        "score_components": [
            "answerability_score",
            "faq_coverage_score",
            "citation_readiness_score",
            "entity_coverage",
            "question_coverage",
        ],
    }


@router.get("/status")
def aeo_status(ctx: AuthContext = Depends(get_auth_context)) -> dict:
    return AeoEngine(ctx.organisation.id).status()


@router.post("/analyses", response_model=AeoAnalysisResponse, status_code=201)
def create_aeo_analysis(
    body: AeoAnalysisRequest,
    ctx: AuthContext = Depends(require_writer),
    db: Session = Depends(get_db),
) -> AeoAnalysisResponse:
    ws = _workspace_id(ctx, body.workspace_id)
    try:
        result = AeoAnalysisService(db).analyse_crawl(
            organisation_id=ctx.organisation.id,
            workspace_id=ws,
            website_id=body.website_id,
            crawl_id=body.crawl_id,
            name=body.name,
            page_urls=body.page_urls or None,
            created_by=ctx.user.id,
            notes=body.notes,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit.log(
        AuditEvent(
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            action="aeo.analyse",
            resource_type="aeo_observation",
            resource_id=result["analysis_id"],
            workspace_id=ws,
            metadata={"crawl_id": body.crawl_id, "aeo_score": result["aeo_score"]},
        )
    )
    return AeoAnalysisResponse(
        analysis_id=result["analysis_id"],
        name=result["name"],
        website_id=result["website_id"],
        crawl_id=result["crawl_id"],
        page_count=result["page_count"],
        aeo_score=result["aeo_score"],
        answerability_score=result["answerability_score"],
        faq_coverage_score=result["faq_coverage_score"],
        citation_readiness_score=result["citation_readiness_score"],
        entity_coverage=result["entity_coverage"],
        question_coverage=result["question_coverage"],
        pages=result.get("pages") or [],
        recommendations=result.get("recommendations") or [],
    )


@router.get("/analyses/{analysis_id}", response_model=AeoAnalysisResponse)
def get_aeo_analysis(
    analysis_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> AeoAnalysisResponse:
    result = AeoAnalysisService(db).get_analysis(
        organisation_id=ctx.organisation.id,
        analysis_id=analysis_id,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="AEO analysis not found")
    return AeoAnalysisResponse(
        analysis_id=result["analysis_id"],
        name=result.get("name") or "AEO analysis",
        website_id=result["website_id"],
        crawl_id=result.get("crawl_id") or "",
        page_count=int(result.get("page_count") or 0),
        aeo_score=float(result.get("aeo_score") or 0),
        answerability_score=float(result.get("answerability_score") or 0),
        faq_coverage_score=float(result.get("faq_coverage_score") or 0),
        citation_readiness_score=float(result.get("citation_readiness_score") or 0),
        entity_coverage=float(result.get("entity_coverage") or 0),
        question_coverage=float(result.get("question_coverage") or 0),
        pages=result.get("pages") or [],
        recommendations=result.get("recommendations") or [],
    )
