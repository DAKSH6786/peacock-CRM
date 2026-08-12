from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas import JobEnqueueRequest, JobStatusResponse
from api.worker import get_job_runner
from db_models import BackgroundJob
from job_runtime import JobSubmission
from observability.audit import AuditEvent, AuditLogger

router = APIRouter(prefix="/jobs", tags=["jobs"])
audit = AuditLogger()


@router.post("", response_model=JobStatusResponse, status_code=202)
def enqueue_job(
    body: JobEnqueueRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> JobStatusResponse:
    runner = get_job_runner()
    submission = JobSubmission(
        name=body.name,
        organisation_id=ctx.organisation.id,
        workspace_id=body.workspace_id or (ctx.workspace.id if ctx.workspace else None),
        payload=body.payload,
    )
    handle = runner.enqueue(submission)

    job = BackgroundJob(
        id=handle.id,
        organisation_id=ctx.organisation.id,
        workspace_id=submission.workspace_id,
        name=handle.name,
        status=handle.status.value,
        backend=handle.backend,
        payload=body.payload,
    )
    db.add(job)
    db.commit()

    audit.log(
        AuditEvent(
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            action="jobs.enqueue",
            resource_type="background_job",
            resource_id=handle.id,
            workspace_id=submission.workspace_id,
            metadata={"name": body.name},
        )
    )

    return JobStatusResponse(
        id=handle.id,
        name=handle.name,
        organisation_id=handle.organisation_id,
        status=handle.status.value,
        backend=handle.backend,
        result=handle.result,
        error=handle.error,
    )


@router.get("/{job_id}", response_model=JobStatusResponse)
def get_job(
    job_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> JobStatusResponse:
    job = db.get(BackgroundJob, job_id)
    if not job or job.organisation_id != ctx.organisation.id:
        raise HTTPException(status_code=404, detail="Job not found")

    runner = get_job_runner()
    try:
        handle = runner.get_status(job_id)
        job.status = handle.status.value
        job.result = handle.result
        job.error = handle.error
        db.commit()
        return JobStatusResponse(
            id=handle.id,
            name=handle.name or job.name,
            organisation_id=ctx.organisation.id,
            status=handle.status.value,
            backend=handle.backend,
            result=handle.result,
            error=handle.error,
        )
    except Exception:  # noqa: BLE001
        return JobStatusResponse(
            id=job.id,
            name=job.name,
            organisation_id=job.organisation_id,
            status=job.status,
            backend=job.backend,
            result=job.result,
            error=job.error,
        )


@router.post("/demo/ping", response_model=JobStatusResponse, status_code=202)
def demo_ping(ctx: AuthContext = Depends(get_auth_context), db: Session = Depends(get_db)) -> JobStatusResponse:
    """Enqueue a harmless ping job to prove background execution + status tracking."""
    return enqueue_job(
        JobEnqueueRequest(name="peacock.ping", payload={"message": "pong", "nonce": str(uuid.uuid4())}),
        ctx,
        db,
    )
