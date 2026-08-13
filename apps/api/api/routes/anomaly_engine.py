"""Peacock Anomaly Engine API — impact-ranked anomaly detection."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from anomaly_engine import (
    AnomalyEngineService,
    AnomalyEngineSpec,
    AnomalyScanSpec,
    MetricObservation,
    catalog,
)
from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas_anomaly_engine import (
    AnomalyCatalogResponse,
    AnomalyResponse,
    AnomalyScanRequest,
    AnomalyScanResponse,
)
from observability.audit import AuditEvent, AuditLogger

router = APIRouter(prefix="/anomalies", tags=["anomalies"])
audit_logger = AuditLogger()


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


def _to_response(report) -> AnomalyScanResponse:
    r = report.result
    return AnomalyScanResponse(
        scan_id=report.scan_id,
        name=report.name,
        client_brand=report.client_brand,
        methodology=report.methodology,
        window_start=r.window_start.isoformat(),
        window_end=r.window_end.isoformat(),
        anomalies=[AnomalyResponse(**a.to_dict()) for a in r.anomalies],
        anomalies_detected=r.anomalies_detected,
        critical_count=r.critical_count,
        high_count=r.high_count,
        top_anomaly_type=r.top_anomaly_type,
        top_impact_score=r.top_impact_score,
        methodology_note=r.methodology_note,
        summary=r.summary,
    )


@router.get("/catalog", response_model=AnomalyCatalogResponse)
def anomalies_catalog(
    ctx: AuthContext = Depends(get_auth_context),
) -> AnomalyCatalogResponse:
    _ = ctx
    return AnomalyCatalogResponse(**catalog())


@router.post("/scans", response_model=AnomalyScanResponse, status_code=201)
def create_anomaly_scan(
    body: AnomalyScanRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> AnomalyScanResponse:
    ws = _workspace_id(ctx, body.workspace_id)
    try:
        report = AnomalyEngineService(db).scan(
            organisation_id=ctx.organisation.id,
            workspace_id=ws,
            created_by=ctx.user.id,
            spec=AnomalyEngineSpec(
                website_id=body.website_id,
                name=body.name,
                scan=AnomalyScanSpec(
                    client_brand=body.brief.client_brand,
                    window_start=body.brief.window_start,
                    window_end=body.brief.window_end,
                    observations=[
                        MetricObservation(
                            metric_key=o.metric_key,
                            anomaly_type=o.anomaly_type,
                            points=[(p.occurred_at, p.value) for p in o.points],
                            revenue_exposure=o.revenue_exposure,
                            label_hint=o.label_hint,
                        )
                        for o in body.brief.observations
                    ],
                    default_revenue_exposure=body.brief.default_revenue_exposure,
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
            action="anomaly_engine.scan",
            resource_type="anomaly_scan",
            resource_id=report.scan_id,
            workspace_id=ws,
            metadata={
                "anomalies_detected": report.result.anomalies_detected,
                "top_anomaly_type": report.result.top_anomaly_type,
                "top_impact_score": report.result.top_impact_score,
            },
        )
    )
    return _to_response(report)


@router.get("/scans/{scan_id}", response_model=AnomalyScanResponse)
def get_anomaly_scan(
    scan_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> AnomalyScanResponse:
    report = AnomalyEngineService(db).get_scan(
        scan_id=scan_id,
        organisation_id=ctx.organisation.id,
    )
    if report is None:
        raise HTTPException(status_code=404, detail="Anomaly scan not found")
    return _to_response(report)
