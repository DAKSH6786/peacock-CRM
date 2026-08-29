"""Content Digital Twin API — simulate article plans before publish."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas_content_digital_twin import (
    CreateTwinRequest,
    EvaluationHistoryItem,
    EvaluationResponse,
    FindingResponse,
    RequirementScoreResponse,
    TwinCatalogResponse,
    TwinResponse,
    UpdatePlanRequest,
)
from content_digital_twin import (
    FINDING_CATEGORIES,
    METHODOLOGY,
    METHODOLOGY_NOTE,
    SIMULATION_SURFACES,
    AiAnswerScenario,
    ArticlePlan,
    BrandGuidelines,
    CompetitorPageRef,
    ContentDigitalTwinService,
    PersonaRef,
    SimulationContext,
    TwinSpec,
)
from observability.audit import AuditEvent, AuditLogger

router = APIRouter(prefix="/content-digital-twin", tags=["content-digital-twin"])
audit_logger = AuditLogger()


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


def _plan(body) -> ArticlePlan:
    return ArticlePlan(**body.model_dump())


def _context(body) -> SimulationContext:
    data = body.model_dump()
    return SimulationContext(
        seo_requirements=data.get("seo_requirements") or [],
        aeo_requirements=data.get("aeo_requirements") or [],
        geo_requirements=data.get("geo_requirements") or [],
        competitor_pages=[
            CompetitorPageRef(**c) for c in (data.get("competitor_pages") or [])
        ],
        target_entities=data.get("target_entities") or [],
        user_personas=[PersonaRef(**p) for p in (data.get("user_personas") or [])],
        ai_answer_scenarios=[
            AiAnswerScenario(**a) for a in (data.get("ai_answer_scenarios") or [])
        ],
        citation_requirements=data.get("citation_requirements") or [],
        brand_guidelines=BrandGuidelines(**(data.get("brand_guidelines") or {})),
    )


def _finding(f) -> FindingResponse:
    return FindingResponse(
        category=f.category,
        title=f.title,
        detail=f.detail,
        severity=f.severity,
        related_surface=f.related_surface,
        related_item=f.related_item,
        priority=f.priority,
    )


def _evaluation(ev) -> EvaluationResponse:
    by_cat = {
        k: [_finding(x) for x in v] for k, v in (ev.findings_by_category or {}).items()
    }
    return EvaluationResponse(
        twin_id=ev.twin_id,
        evaluation_id=ev.evaluation_id,
        evaluation_number=ev.evaluation_number,
        plan_revision=ev.plan_revision,
        client_brand=ev.client_brand,
        methodology=ev.methodology,
        article_plan=ev.article_plan.to_dict(),
        predicted_strength_score=ev.predicted_strength_score,
        readiness_score=ev.readiness_score,
        summary=ev.summary,
        requirement_scores=[
            RequirementScoreResponse(
                surface=r.surface,
                coverage_score=r.coverage_score,
                matched_count=r.matched_count,
                missing_count=r.missing_count,
                explanation=r.explanation,
            )
            for r in ev.requirement_scores
        ],
        findings=[_finding(f) for f in ev.findings],
        findings_by_category=by_cat,
    )


def _twin(report) -> TwinResponse:
    return TwinResponse(
        twin_id=report.twin_id,
        name=report.name,
        client_brand=report.client_brand,
        methodology=report.methodology,
        plan_revision=report.plan_revision,
        evaluation_count=report.evaluation_count,
        article_plan=report.article_plan.to_dict(),
        simulation_context=report.simulation_context.to_dict(),
        latest_evaluation=(
            _evaluation(report.latest_evaluation) if report.latest_evaluation else None
        ),
        evaluation_history=[
            EvaluationHistoryItem(**h) for h in report.evaluation_history
        ],
    )


@router.get("/catalog", response_model=TwinCatalogResponse)
def twin_catalog(
    ctx: AuthContext = Depends(get_auth_context),
) -> TwinCatalogResponse:
    _ = ctx
    return TwinCatalogResponse(
        simulation_surfaces=list(SIMULATION_SURFACES),
        finding_categories=list(FINDING_CATEGORIES),
        methodology=METHODOLOGY,
        methodology_note=METHODOLOGY_NOTE,
    )


@router.post("/twins", response_model=TwinResponse, status_code=201)
def create_twin(
    body: CreateTwinRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> TwinResponse:
    ws = _workspace_id(ctx, body.workspace_id)
    try:
        report = ContentDigitalTwinService(db).create_twin(
            organisation_id=ctx.organisation.id,
            workspace_id=ws,
            created_by=ctx.user.id,
            spec=TwinSpec(
                website_id=body.website_id,
                name=body.name,
                client_brand=body.client_brand,
                topic_cluster=body.topic_cluster,
                article_plan=_plan(body.article_plan),
                simulation_context=_context(body.simulation_context),
                content_lab_proposal_id=body.content_lab_proposal_id,
                notes=body.notes,
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_logger.log(
        AuditEvent(
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            action="content_digital_twin.create",
            resource_type="content_digital_twin",
            resource_id=report.twin_id,
            workspace_id=ws,
            metadata={
                "evaluation_count": report.evaluation_count,
                "predicted_strength": (
                    report.latest_evaluation.predicted_strength_score
                    if report.latest_evaluation
                    else None
                ),
            },
        )
    )
    return _twin(report)


@router.get("/twins/{twin_id}", response_model=TwinResponse)
def get_twin(
    twin_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> TwinResponse:
    report = ContentDigitalTwinService(db).get_twin(
        twin_id=twin_id,
        organisation_id=ctx.organisation.id,
    )
    if report is None:
        raise HTTPException(status_code=404, detail="Content Digital Twin not found")
    return _twin(report)


@router.patch("/twins/{twin_id}/plan", response_model=TwinResponse)
def update_twin_plan(
    twin_id: str,
    body: UpdatePlanRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> TwinResponse:
    ws = _workspace_id(ctx, body.workspace_id)
    try:
        report = ContentDigitalTwinService(db).update_plan(
            twin_id=twin_id,
            organisation_id=ctx.organisation.id,
            article_plan=_plan(body.article_plan) if body.article_plan else None,
            simulation_context=(
                _context(body.simulation_context) if body.simulation_context else None
            ),
            name=body.name,
            notes=body.notes,
            rerun=body.rerun,
            created_by=ctx.user.id,
        )
    except ValueError as exc:
        detail = str(exc)
        status = 404 if "not found" in detail.lower() else 400
        raise HTTPException(status_code=status, detail=detail) from exc

    audit_logger.log(
        AuditEvent(
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            action="content_digital_twin.update_plan",
            resource_type="content_digital_twin",
            resource_id=report.twin_id,
            workspace_id=ws,
            metadata={
                "plan_revision": report.plan_revision,
                "rerun": body.rerun,
                "evaluation_count": report.evaluation_count,
            },
        )
    )
    return _twin(report)


@router.post("/twins/{twin_id}/evaluations", response_model=TwinResponse, status_code=201)
def rerun_twin_evaluation(
    twin_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> TwinResponse:
    try:
        report = ContentDigitalTwinService(db).rerun_evaluation(
            twin_id=twin_id,
            organisation_id=ctx.organisation.id,
            created_by=ctx.user.id,
        )
    except ValueError as exc:
        detail = str(exc)
        status = 404 if "not found" in detail.lower() else 400
        raise HTTPException(status_code=status, detail=detail) from exc

    audit_logger.log(
        AuditEvent(
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            action="content_digital_twin.rerun",
            resource_type="content_digital_twin",
            resource_id=report.twin_id,
            workspace_id=ctx.workspace.id if ctx.workspace else None,
            metadata={"evaluation_count": report.evaluation_count},
        )
    )
    return _twin(report)


@router.get(
    "/twins/{twin_id}/evaluations/{evaluation_id}",
    response_model=EvaluationResponse,
)
def get_twin_evaluation(
    twin_id: str,
    evaluation_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> EvaluationResponse:
    ev = ContentDigitalTwinService(db).get_evaluation(
        twin_id=twin_id,
        evaluation_id=evaluation_id,
        organisation_id=ctx.organisation.id,
    )
    if ev is None:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return _evaluation(ev)
