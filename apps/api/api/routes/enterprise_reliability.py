"""Peacock Enterprise Reliability API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from enterprise_reliability import (
    EnterpriseReliabilityCreateSpec,
    EnterpriseReliabilityService,
    ReliabilityRunSpec,
    catalog,
    demo_run,
)
from db_models.enterprise_reliability import DEFAULT_AI_ENGINES
from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas_enterprise_reliability import (
    CircuitStateResponse,
    ControlActivationResponse,
    DeadLetterResponse,
    ProviderMeasurementResponse,
    ReliabilityCatalogResponse,
    ReliabilityPreviewResponse,
    ReliabilityRunCreateRequest,
    ReliabilityRunResponse,
    WorkflowCheckpointResponse,
)
from observability.audit import AuditEvent, AuditLogger

router = APIRouter(prefix="/enterprise-reliability", tags=["enterprise-reliability"])
audit_logger = AuditLogger()


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


def _result_fields(result) -> dict:
    return {
        "report_status": result.report_status,
        "engines_attempted": result.engines_attempted,
        "engines_succeeded": result.engines_succeeded,
        "engines_failed": result.engines_failed,
        "partial_result_summary": result.partial_result_summary,
        "unavailable_providers": list(result.unavailable_providers),
        "idempotency_key": result.idempotency_key,
        "cancelled": result.cancelled,
        "recovered_from_checkpoint": result.recovered_from_checkpoint,
        "cost_limit_usd_micros": result.cost_limit_usd_micros,
        "cost_used_usd_micros": result.cost_used_usd_micros,
        "rate_limit_rpm": result.rate_limit_rpm,
        "dlq_events_count": result.dlq_events_count,
        "controls_active_count": result.controls_active_count,
        "provider_measurements": [
            ProviderMeasurementResponse(**p.to_dict()) for p in result.provider_measurements
        ],
        "control_activations": [
            ControlActivationResponse(**c.to_dict()) for c in result.control_activations
        ],
        "dead_letter_events": [
            DeadLetterResponse(**d.to_dict()) for d in result.dead_letter_events
        ],
        "circuit_states": [
            CircuitStateResponse(**c.to_dict()) for c in result.circuit_states
        ],
        "workflow_checkpoints": [
            WorkflowCheckpointResponse(**w.to_dict()) for w in result.workflow_checkpoints
        ],
        "reliability_positioning": result.reliability_positioning,
        "partial_results_policy": result.partial_results_policy,
        "methodology_note": result.methodology_note,
        "summary": result.summary,
        "analysed_at": result.analysed_at.isoformat(),
    }


def _to_response(report) -> ReliabilityRunResponse:
    return ReliabilityRunResponse(
        run_id=report.run_id,
        name=report.name,
        client_brand=report.client_brand,
        methodology=report.methodology,
        **_result_fields(report.result),
    )


@router.get("/catalog", response_model=ReliabilityCatalogResponse)
def reliability_catalog(
    ctx: AuthContext = Depends(get_auth_context),
) -> ReliabilityCatalogResponse:
    _ = ctx
    return ReliabilityCatalogResponse(**catalog())


@router.get("/preview", response_model=ReliabilityPreviewResponse)
def reliability_preview(brand: str = "Acme") -> ReliabilityPreviewResponse:
    """Demo: 4/5 AI engines succeed; DeepSeek unavailable — report still completes."""
    result = demo_run(brand)
    return ReliabilityPreviewResponse(
        client_brand=result.client_brand,
        **_result_fields(result),
    )


@router.post("/runs", response_model=ReliabilityRunResponse, status_code=201)
def create_reliability_run(
    body: ReliabilityRunCreateRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> ReliabilityRunResponse:
    ws = _workspace_id(ctx, body.workspace_id)
    engines = body.brief.engines or list(DEFAULT_AI_ENGINES)
    try:
        report = EnterpriseReliabilityService(db).run(
            organisation_id=ctx.organisation.id,
            workspace_id=ws,
            created_by=ctx.user.id,
            spec=EnterpriseReliabilityCreateSpec(
                website_id=body.website_id,
                name=body.name,
                run=ReliabilityRunSpec(
                    client_brand=body.brief.client_brand,
                    engines=engines,
                    unavailable_engines=body.brief.unavailable_engines,
                    idempotency_key=body.brief.idempotency_key,
                    cancel_requested=body.brief.cancel_requested,
                    recover_from_checkpoint=body.brief.recover_from_checkpoint,
                    cost_limit_usd_micros=body.brief.cost_limit_usd_micros,
                    rate_limit_rpm=body.brief.rate_limit_rpm,
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
            action="enterprise_reliability.run",
            resource_type="enterprise_reliability_run",
            resource_id=report.run_id,
            workspace_id=ws,
            metadata={
                "report_status": report.result.report_status,
                "engines_succeeded": report.result.engines_succeeded,
                "engines_attempted": report.result.engines_attempted,
                "partial_result_summary": report.result.partial_result_summary,
            },
        )
    )
    return _to_response(report)


@router.get("/runs/{run_id}", response_model=ReliabilityRunResponse)
def get_reliability_run(
    run_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> ReliabilityRunResponse:
    report = EnterpriseReliabilityService(db).get_run(
        run_id=run_id,
        organisation_id=ctx.organisation.id,
    )
    if report is None:
        raise HTTPException(status_code=404, detail="Reliability run not found")
    return _to_response(report)
