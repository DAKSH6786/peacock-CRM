"""Peacock One Quality Bar API — module completeness gates."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from quality_bar import (
    GateAnswer,
    QualityBarCreateSpec,
    QualityBarService,
    QualityBarSpec,
    assess_quality_bar,
    catalog,
    demo_assessment,
)
from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas_quality_bar import (
    GateResultResponse,
    QualityBarAssessmentResponse,
    QualityBarCatalogResponse,
    QualityBarCreateRequest,
    QualityBarPreviewResponse,
    RemediationActionResponse,
)
from observability.audit import AuditEvent, AuditLogger

router = APIRouter(prefix="/quality-bar", tags=["quality-bar"])
audit_logger = AuditLogger()


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


def _result_fields(result) -> dict:
    return {
        "module_key": result.module_key,
        "module_label": result.module_label,
        "completeness_verdict": result.completeness_verdict,
        "gates_total": result.gates_total,
        "gates_passed": result.gates_passed,
        "gates_failed": result.gates_failed,
        "completeness_score": result.completeness_score,
        "blocked_by": list(result.blocked_by),
        "improvement_summary": result.improvement_summary,
        "gate_results": [GateResultResponse(**g.to_dict()) for g in result.gate_results],
        "remediation_actions": [
            RemediationActionResponse(**r.to_dict()) for r in result.remediation_actions
        ],
        "quality_positioning": result.quality_positioning,
        "methodology_note": result.methodology_note,
        "summary": result.summary,
        "analysed_at": result.analysed_at.isoformat(),
    }


def _to_response(report) -> QualityBarAssessmentResponse:
    return QualityBarAssessmentResponse(
        assessment_id=report.assessment_id,
        name=report.name,
        client_brand=report.client_brand,
        methodology=report.methodology,
        **_result_fields(report.result),
    )


@router.get("/catalog", response_model=QualityBarCatalogResponse)
def quality_bar_catalog(
    ctx: AuthContext = Depends(get_auth_context),
) -> QualityBarCatalogResponse:
    _ = ctx
    return QualityBarCatalogResponse(**catalog())


@router.get("/preview", response_model=QualityBarPreviewResponse)
def quality_bar_preview(
    brand: str = "Acme",
    module_key: str = Query(default="llm_only_recommender"),
) -> QualityBarPreviewResponse:
    """Demo Quality Bar — LLM-only recommender fails multiple gates."""
    try:
        if module_key == "llm_only_recommender":
            result = demo_assessment(brand)
        else:
            result = assess_quality_bar(
                QualityBarSpec(client_brand=brand, module_key=module_key)
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return QualityBarPreviewResponse(
        client_brand=result.client_brand,
        **_result_fields(result),
    )


@router.post("/assessments", response_model=QualityBarAssessmentResponse, status_code=201)
def create_quality_bar_assessment(
    body: QualityBarCreateRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> QualityBarAssessmentResponse:
    ws = _workspace_id(ctx, body.workspace_id)
    try:
        report = QualityBarService(db).assess(
            organisation_id=ctx.organisation.id,
            workspace_id=ws,
            created_by=ctx.user.id,
            spec=QualityBarCreateSpec(
                website_id=body.website_id,
                name=body.name,
                assessment=QualityBarSpec(
                    client_brand=body.brief.client_brand,
                    module_key=body.brief.module_key,
                    module_label=body.brief.module_label,
                    gate_answers=[
                        GateAnswer(
                            gate_key=a.gate_key,
                            answer_yes_problem=a.answer_yes_problem,
                            rationale=a.rationale,
                            evidence_note=a.evidence_note,
                        )
                        for a in body.brief.gate_answers
                    ],
                    analysed_at=body.brief.analysed_at,
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
            action="quality_bar.assess",
            resource_type="quality_bar_assessment",
            resource_id=report.assessment_id,
            workspace_id=ws,
            metadata={
                "module_key": report.result.module_key,
                "completeness_verdict": report.result.completeness_verdict,
                "gates_passed": report.result.gates_passed,
                "gates_failed": report.result.gates_failed,
            },
        )
    )
    return _to_response(report)


@router.get("/assessments/{assessment_id}", response_model=QualityBarAssessmentResponse)
def get_quality_bar_assessment(
    assessment_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> QualityBarAssessmentResponse:
    report = QualityBarService(db).get_assessment(
        assessment_id=assessment_id,
        organisation_id=ctx.organisation.id,
    )
    if report is None:
        raise HTTPException(status_code=404, detail="Quality Bar assessment not found")
    return _to_response(report)
