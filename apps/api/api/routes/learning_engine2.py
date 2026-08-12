"""Peacock Learning Engine 2.0 API — closed loop + industry policies."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas_learning_engine2 import (
    ContextFactorResponse,
    CreateLearningRecordRequest,
    DimensionInsightResponse,
    ExecutionRequest,
    IndustryPolicyResponse,
    Learning2CatalogResponse,
    LearningRecordResponse,
    LearningRunRequest,
    LearningRunResponse,
    OutcomeRequest,
)
from learning_engine2 import (
    ContextFactorInput,
    ExecutionUpdate,
    Learning2CreateSpec,
    LearningEngine2Service,
    LearningRecordSpec,
    OutcomeUpdate,
    build_record_view,
    catalog,
)
from observability.audit import AuditEvent, AuditLogger

router = APIRouter(prefix="/learning2", tags=["learning2"])
audit_logger = AuditLogger()


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


def _record_response(report) -> LearningRecordResponse:
    v = report.view
    return LearningRecordResponse(
        record_id=report.record_id,
        methodology=report.methodology,
        name=v.name,
        industry=v.industry,
        record_status=v.record_status,
        context_summary=v.context_summary,
        recommendation_text=v.recommendation_text,
        expected_impact=v.expected_impact,
        expected_impact_score=v.expected_impact_score,
        confidence=v.confidence,
        execution_summary=v.execution_summary,
        execution_status=v.execution_status,
        actual_outcome=v.actual_outcome,
        actual_outcome_score=v.actual_outcome_score,
        outcome_delta=v.outcome_delta,
        topic_key=v.topic_key,
        format_key=v.format_key,
        source_key=v.source_key,
        writer_key=v.writer_key,
        intervention_key=v.intervention_key,
        engine_key=v.engine_key,
        context_factors=[ContextFactorResponse(**c.to_dict()) for c in v.context_factors],
        not_universal_geo_strategy=True,
        not_universal_geo_note=v.not_universal_geo_note,
    )


@router.get("/catalog", response_model=Learning2CatalogResponse)
def learning2_catalog(
    ctx: AuthContext = Depends(get_auth_context),
) -> Learning2CatalogResponse:
    _ = ctx
    return Learning2CatalogResponse(**catalog())


@router.post("/records", response_model=LearningRecordResponse, status_code=201)
def create_learning_record(
    body: CreateLearningRecordRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> LearningRecordResponse:
    ws = _workspace_id(ctx, body.workspace_id)
    try:
        view = build_record_view(
            LearningRecordSpec(
                name=body.name,
                industry=body.industry,
                context_summary=body.context_summary,
                recommendation_text=body.recommendation_text,
                expected_impact=body.expected_impact,
                expected_impact_score=body.expected_impact_score,
                confidence=body.confidence,
                topic_key=body.topic_key,
                format_key=body.format_key,
                source_key=body.source_key,
                writer_key=body.writer_key,
                intervention_key=body.intervention_key,
                engine_key=body.engine_key,
                context_factors=[
                    ContextFactorInput(**f.model_dump()) for f in body.context_factors
                ],
                central_recommendation_id=body.central_recommendation_id,
                notes=body.notes,
            )
        )
        report = LearningEngine2Service(db).create_record(
            organisation_id=ctx.organisation.id,
            workspace_id=ws,
            created_by=ctx.user.id,
            spec=Learning2CreateSpec(
                website_id=body.website_id,
                view=view,
                central_recommendation_id=body.central_recommendation_id,
                notes=body.notes,
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_logger.log(
        AuditEvent(
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            action="learning2.create_record",
            resource_type="learning2_record",
            resource_id=report.record_id,
            workspace_id=ws,
            metadata={
                "industry": report.view.industry,
                "not_universal_geo_strategy": True,
            },
        )
    )
    return _record_response(report)


@router.get("/records/{record_id}", response_model=LearningRecordResponse)
def get_learning_record(
    record_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> LearningRecordResponse:
    report = LearningEngine2Service(db).get_record(
        record_id=record_id, organisation_id=ctx.organisation.id
    )
    if report is None:
        raise HTTPException(status_code=404, detail="Learning record not found")
    return _record_response(report)


@router.post("/records/{record_id}/execution", response_model=LearningRecordResponse)
def record_execution(
    record_id: str,
    body: ExecutionRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> LearningRecordResponse:
    try:
        report = LearningEngine2Service(db).record_execution(
            record_id=record_id,
            organisation_id=ctx.organisation.id,
            update=ExecutionUpdate(**body.model_dump()),
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _record_response(report)


@router.post("/records/{record_id}/outcome", response_model=LearningRecordResponse)
def record_outcome(
    record_id: str,
    body: OutcomeRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> LearningRecordResponse:
    try:
        report = LearningEngine2Service(db).record_outcome(
            record_id=record_id,
            organisation_id=ctx.organisation.id,
            update=OutcomeUpdate(**body.model_dump()),
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _record_response(report)


@router.post("/runs", response_model=LearningRunResponse, status_code=201)
def run_learning(
    body: LearningRunRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> LearningRunResponse:
    ws = _workspace_id(ctx, body.workspace_id)
    report = LearningEngine2Service(db).run_learning(
        organisation_id=ctx.organisation.id,
        workspace_id=ws,
        website_id=body.website_id,
        name=body.name,
        created_by=ctx.user.id,
    )
    r = report.result
    audit_logger.log(
        AuditEvent(
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            action="learning2.run",
            resource_type="le2_learning_run",
            resource_id=report.run_id,
            workspace_id=ws,
            metadata={
                "records_considered": r.records_considered,
                "insights": len(r.insights),
                "not_universal_geo_strategy": True,
            },
        )
    )
    return LearningRunResponse(
        run_id=report.run_id,
        name=report.name,
        methodology=report.methodology,
        records_considered=r.records_considered,
        insights=[DimensionInsightResponse(**i.to_dict()) for i in r.insights],
        industry_policies=[
            IndustryPolicyResponse(**p.to_dict()) for p in r.industry_policies
        ],
        industries_touched=r.industries_touched,
        not_universal_geo_strategy=True,
        methodology_note=r.methodology_note,
        learning_questions=r.learning_questions,
        summary=r.summary,
    )


@router.get("/policies", response_model=list[IndustryPolicyResponse])
def list_industry_policies(
    workspace_id: str | None = None,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> list[IndustryPolicyResponse]:
    ws = _workspace_id(ctx, workspace_id)
    policies = LearningEngine2Service(db).list_policies(
        organisation_id=ctx.organisation.id, workspace_id=ws
    )
    return [IndustryPolicyResponse(**p.to_dict()) for p in policies]
