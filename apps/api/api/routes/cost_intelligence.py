"""Peacock Cost Intelligence API — Intelligence Budget Engine."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from cost_intelligence import (
    BudgetEstimateSpec,
    CostIntelligenceCreateSpec,
    CostIntelligenceService,
    catalog,
    estimate_budget,
)
from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas_cost_intelligence import (
    BudgetCatalogResponse,
    BudgetEstimateCreateRequest,
    BudgetEstimateResponse,
    BudgetPreviewResponse,
    MethodCandidateResponse,
)
from observability.audit import AuditEvent, AuditLogger

router = APIRouter(prefix="/cost-intelligence", tags=["cost-intelligence"])
audit_logger = AuditLogger()


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


def _result_fields(result) -> dict:
    return {
        "workflow_intent": result.workflow_intent,
        "decision_value": result.decision_value,
        "question": result.question,
        "selected_method_kind": result.selected_method_kind,
        "selected_method_label": result.selected_method_label,
        "selected_peacock_mode": result.selected_peacock_mode,
        "selection_rationale": result.selection_rationale,
        "rejected_expensive": result.rejected_expensive,
        "expected_calls": result.expected_calls,
        "expected_tokens": result.expected_tokens,
        "expected_searches": result.expected_searches,
        "expected_runtime_seconds": result.expected_runtime_seconds,
        "expected_cost_usd_micros": result.expected_cost_usd_micros,
        "candidates": [MethodCandidateResponse(**c.to_dict()) for c in result.candidates],
        "candidates_count": result.candidates_count,
        "cost_positioning": result.cost_positioning,
        "policy_note": result.policy_note,
        "methodology_note": result.methodology_note,
        "summary": result.summary,
        "analysed_at": result.analysed_at.isoformat(),
    }


def _to_response(report) -> BudgetEstimateResponse:
    return BudgetEstimateResponse(
        estimate_id=report.estimate_id,
        name=report.name,
        client_brand=report.client_brand,
        methodology=report.methodology,
        **_result_fields(report.result),
    )


@router.get("/catalog", response_model=BudgetCatalogResponse)
def cost_intelligence_catalog(
    ctx: AuthContext = Depends(get_auth_context),
) -> BudgetCatalogResponse:
    _ = ctx
    return BudgetCatalogResponse(**catalog())


@router.get("/preview", response_model=BudgetPreviewResponse)
def cost_intelligence_preview(
    brand: str = "Acme",
    intent: str = Query(default="page_title_recommendation"),
    decision_value: str | None = None,
    question: str | None = None,
) -> BudgetPreviewResponse:
    """Public demo — page-title defaults to deterministic, not Council."""
    q = question or (
        "Recommend a better title for /pricing"
        if intent == "page_title_recommendation"
        else f"Estimate budget for {intent}"
    )
    try:
        result = estimate_budget(
            BudgetEstimateSpec(
                client_brand=brand,
                workflow_intent=intent,
                decision_value=decision_value,
                question=q,
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return BudgetPreviewResponse(
        client_brand=result.client_brand,
        **_result_fields(result),
    )


@router.post("/estimates", response_model=BudgetEstimateResponse, status_code=201)
def create_budget_estimate(
    body: BudgetEstimateCreateRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> BudgetEstimateResponse:
    ws = _workspace_id(ctx, body.workspace_id)
    try:
        report = CostIntelligenceService(db).estimate(
            organisation_id=ctx.organisation.id,
            workspace_id=ws,
            created_by=ctx.user.id,
            spec=CostIntelligenceCreateSpec(
                website_id=body.website_id,
                name=body.name,
                estimate=BudgetEstimateSpec(
                    client_brand=body.brief.client_brand,
                    question=body.brief.question,
                    workflow_intent=body.brief.workflow_intent,
                    decision_value=body.brief.decision_value,
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
            action="cost_intelligence.estimate",
            resource_type="intelligence_budget_estimate",
            resource_id=report.estimate_id,
            workspace_id=ws,
            metadata={
                "selected_method_kind": report.result.selected_method_kind,
                "expected_cost_usd_micros": report.result.expected_cost_usd_micros,
                "decision_value": report.result.decision_value,
                "workflow_intent": report.result.workflow_intent,
            },
        )
    )
    return _to_response(report)


@router.get("/estimates/{estimate_id}", response_model=BudgetEstimateResponse)
def get_budget_estimate(
    estimate_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> BudgetEstimateResponse:
    report = CostIntelligenceService(db).get_estimate(
        estimate_id=estimate_id,
        organisation_id=ctx.organisation.id,
    )
    if report is None:
        raise HTTPException(status_code=404, detail="Budget estimate not found")
    return _to_response(report)
