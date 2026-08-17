"""Monitoring API — projects, snapshots, search performance, anomaly feeds."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import AuthContext, get_auth_context, require_writer
from api.schemas_monitoring import (
    MonitoringProjectRequest,
    MonitoringProjectResponse,
    SearchPerformanceRequest,
    SnapshotRequest,
    SnapshotResponse,
)
from api.worker import get_job_runner
from job_runtime import JobSubmission
from monitoring_engine import MonitoringEngine, MonitoringService
from observability.audit import AuditEvent, AuditLogger

router = APIRouter(prefix="/monitoring", tags=["monitoring"])
audit = AuditLogger()


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


@router.get("/catalog")
def monitoring_catalog(ctx: AuthContext = Depends(get_auth_context)) -> dict:
    return {
        **MonitoringEngine(ctx.organisation.id).status(),
        "endpoints": [
            "POST /monitoring/projects",
            "POST /monitoring/projects/{id}/snapshots",
            "GET /monitoring/projects/{id}/snapshots",
            "POST /monitoring/projects/{id}/search-performance",
            "GET /monitoring/projects/{id}/anomaly-observations",
        ],
    }


@router.get("/status")
def monitoring_status(ctx: AuthContext = Depends(get_auth_context)) -> dict:
    return MonitoringEngine(ctx.organisation.id).status()


@router.post("/projects", response_model=MonitoringProjectResponse, status_code=201)
def create_project(
    body: MonitoringProjectRequest,
    ctx: AuthContext = Depends(require_writer),
    db: Session = Depends(get_db),
) -> MonitoringProjectResponse:
    ws = _workspace_id(ctx, body.workspace_id)
    project = MonitoringService(db).create_project(
        organisation_id=ctx.organisation.id,
        workspace_id=ws,
        website_id=body.website_id,
        name=body.name,
        cadence=body.cadence,
        created_by=ctx.user.id,
    )
    audit.log(
        AuditEvent(
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            action="monitoring.project.create",
            resource_type="monitoring_project",
            resource_id=project.id,
            workspace_id=ws,
            metadata={"cadence": project.cadence},
        )
    )
    return MonitoringProjectResponse(
        project_id=project.id,
        website_id=project.website_id,
        name=project.name,
        cadence=project.cadence,
        is_active=project.is_active,
    )


@router.get("/projects/{project_id}", response_model=MonitoringProjectResponse)
def get_project(
    project_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> MonitoringProjectResponse:
    project = MonitoringService(db).get_project(
        organisation_id=ctx.organisation.id, project_id=project_id
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Monitoring project not found")
    return MonitoringProjectResponse(
        project_id=project.id,
        website_id=project.website_id,
        name=project.name,
        cadence=project.cadence,
        is_active=project.is_active,
    )


@router.post("/projects/{project_id}/snapshots", response_model=SnapshotResponse, status_code=201)
def create_snapshots(
    project_id: str,
    body: SnapshotRequest,
    ctx: AuthContext = Depends(require_writer),
    db: Session = Depends(get_db),
) -> SnapshotResponse:
    ws = _workspace_id(ctx, None)
    job_id = None
    if body.run_async:
        runner = get_job_runner()
        handle = runner.enqueue(
            JobSubmission(
                name="peacock.monitoring.snapshot",
                organisation_id=ctx.organisation.id,
                workspace_id=ws,
                payload={
                    "organisation_id": ctx.organisation.id,
                    "workspace_id": ws,
                    "project_id": project_id,
                    "metrics": [m.model_dump() for m in body.metrics],
                    "emit_learning": body.emit_learning,
                },
            )
        )
        job_id = handle.id
        return SnapshotResponse(
            project_id=project_id,
            snapshots=[],
            learning_hooks=[],
            learning_record_ids=[],
            job_id=job_id,
        )

    try:
        result = MonitoringService(db).record_snapshots(
            organisation_id=ctx.organisation.id,
            workspace_id=ws,
            project_id=project_id,
            metrics=[m.model_dump() for m in body.metrics],
            created_by=ctx.user.id,
            emit_learning=body.emit_learning,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit.log(
        AuditEvent(
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            action="monitoring.snapshots",
            resource_type="monitoring_project",
            resource_id=project_id,
            workspace_id=ws,
            metadata={"count": len(result["snapshots"])},
        )
    )
    return SnapshotResponse(**result, job_id=None)


@router.get("/projects/{project_id}/snapshots")
def list_snapshots(
    project_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict:
    try:
        rows = MonitoringService(db).list_snapshots(
            organisation_id=ctx.organisation.id, project_id=project_id
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"project_id": project_id, "snapshots": rows}


@router.post("/projects/{project_id}/search-performance", status_code=201)
def search_performance(
    project_id: str,
    body: SearchPerformanceRequest,
    ctx: AuthContext = Depends(require_writer),
    db: Session = Depends(get_db),
) -> dict:
    ws = _workspace_id(ctx, None)
    try:
        return MonitoringService(db).record_search_performance(
            organisation_id=ctx.organisation.id,
            workspace_id=ws,
            project_id=project_id,
            clicks=body.clicks,
            impressions=body.impressions,
            ctr=body.ctr,
            avg_position=body.avg_position,
            created_by=ctx.user.id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/projects/{project_id}/anomaly-observations")
def anomaly_observations(
    project_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict:
    project = MonitoringService(db).get_project(
        organisation_id=ctx.organisation.id, project_id=project_id
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Monitoring project not found")
    observations = MonitoringService(db).anomaly_observations(
        organisation_id=ctx.organisation.id, project_id=project_id
    )
    return {"project_id": project_id, "observations": observations}
