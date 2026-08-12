"""Peacock 90 2.0 API — adaptive 90-day roadmap optimisation."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas_peacock90 import (
    CapacityRefusalResponse,
    DependencyResponse,
    InitiativeResponse,
    Peacock90CatalogResponse,
    Peacock90PlanRequest,
    Peacock90PlanResponse,
    TaskResponse,
)
from observability.audit import AuditEvent, AuditLogger
from peacock90 import (
    CAPACITY_GUARDRAIL,
    HORIZON_DAYS,
    METHODOLOGY,
    METHODOLOGY_NOTE,
    PRIORITY_CODES,
    RISK_TOLERANCE_LEVELS,
    TASK_KINDS,
    Peacock90Service,
    Peacock90Spec,
    PlanSpec,
    ResourceConstraints,
)

router = APIRouter(prefix="/peacock90", tags=["peacock90"])
audit_logger = AuditLogger()


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


def _to_response(report) -> Peacock90PlanResponse:
    r = report.result
    return Peacock90PlanResponse(
        plan_id=report.plan_id,
        name=report.name,
        client_brand=report.client_brand,
        methodology=report.methodology,
        horizon_days=r.horizon_days,
        constraints=r.constraints,
        initiatives=[InitiativeResponse(**i.to_dict()) for i in r.initiatives],
        tasks=[TaskResponse(**t.to_dict()) for t in r.tasks],
        dependencies=[DependencyResponse(**d.to_dict()) for d in r.dependencies],
        capacity_refusals=[
            CapacityRefusalResponse(**c.to_dict()) for c in r.capacity_refusals
        ],
        total_impact_score=r.total_impact_score,
        budget_used=r.budget_used,
        articles_planned=r.articles_planned,
        initiatives_selected=r.initiatives_selected,
        initiatives_rejected=r.initiatives_rejected,
        tasks_scheduled=r.tasks_scheduled,
        utilisation_summary=r.utilisation_summary,
        capacity_guardrail=r.capacity_guardrail,
        methodology_note=r.methodology_note,
        dependency_example=r.dependency_example,
        summary=r.summary,
    )


@router.get("/catalog", response_model=Peacock90CatalogResponse)
def peacock90_catalog(
    ctx: AuthContext = Depends(get_auth_context),
) -> Peacock90CatalogResponse:
    _ = ctx
    return Peacock90CatalogResponse(
        methodology=METHODOLOGY,
        methodology_note=METHODOLOGY_NOTE,
        capacity_guardrail=CAPACITY_GUARDRAIL,
        horizon_days=HORIZON_DAYS,
        priority_codes=list(PRIORITY_CODES),
        risk_tolerance_levels=list(RISK_TOLERANCE_LEVELS),
        task_kinds=list(TASK_KINDS),
        example_resources={
            "developers": 2,
            "writers": 5,
            "seo_specialists": 1,
            "articles_per_month_max": 25,
            "budget_currency": "INR",
            "budget_amount": "₹X",
        },
        dependency_example=[
            "Fix canonical issue",
            "Recrawl",
            "Update content",
            "Request indexing",
            "Monitor",
        ],
    )


@router.post("/plans", response_model=Peacock90PlanResponse, status_code=201)
def create_peacock90_plan(
    body: Peacock90PlanRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> Peacock90PlanResponse:
    ws = _workspace_id(ctx, body.workspace_id)
    try:
        report = Peacock90Service(db).generate(
            organisation_id=ctx.organisation.id,
            workspace_id=ws,
            created_by=ctx.user.id,
            spec=Peacock90Spec(
                website_id=body.website_id,
                name=body.name,
                plan=PlanSpec(
                    client_brand=body.brief.client_brand,
                    horizon_days=body.brief.horizon_days,
                    constraints=ResourceConstraints(**body.brief.constraints.model_dump()),
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
            action="peacock90.generate",
            resource_type="peacock90_plan",
            resource_id=report.plan_id,
            workspace_id=ws,
            metadata={
                "initiatives_selected": report.result.initiatives_selected,
                "initiatives_rejected": report.result.initiatives_rejected,
                "articles_planned": report.result.articles_planned,
                "capacity_refusals": len(report.result.capacity_refusals),
            },
        )
    )
    return _to_response(report)


@router.get("/plans/{plan_id}", response_model=Peacock90PlanResponse)
def get_peacock90_plan(
    plan_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> Peacock90PlanResponse:
    report = Peacock90Service(db).get_plan(
        plan_id=plan_id,
        organisation_id=ctx.organisation.id,
    )
    if report is None:
        raise HTTPException(status_code=404, detail="Peacock 90 plan not found")
    return _to_response(report)
