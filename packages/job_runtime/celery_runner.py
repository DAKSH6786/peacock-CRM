from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from job_runtime.ports import JobHandle, JobStatus, JobSubmission


class CeleryJobRunner:
    """Celery adapter implementing the JobRunner port.

    Business code depends on JobRunner, not Celery APIs, so Temporal can
    replace this class later.
    """

    backend_name = "celery"

    def __init__(self, celery_app: Any) -> None:
        self._app = celery_app
        self._local: dict[str, JobHandle] = {}

    def enqueue(self, submission: JobSubmission) -> JobHandle:
        job_id = submission.idempotency_key or str(uuid.uuid4())
        async_result = self._app.send_task(
            submission.name,
            kwargs={
                "organisation_id": submission.organisation_id,
                "workspace_id": submission.workspace_id,
                "payload": submission.payload,
                "metadata": submission.metadata,
            },
            task_id=job_id,
            retries=submission.max_retries,
        )
        handle = JobHandle(
            id=async_result.id,
            name=submission.name,
            organisation_id=submission.organisation_id,
            status=JobStatus.QUEUED,
            backend=self.backend_name,
        )
        self._local[handle.id] = handle
        return handle

    def get_status(self, job_id: str) -> JobHandle:
        result = self._app.AsyncResult(job_id)
        status_map = {
            "PENDING": JobStatus.PENDING,
            "RECEIVED": JobStatus.QUEUED,
            "STARTED": JobStatus.RUNNING,
            "SUCCESS": JobStatus.SUCCEEDED,
            "FAILURE": JobStatus.FAILED,
            "RETRY": JobStatus.RETRYING,
            "REVOKED": JobStatus.CANCELLED,
        }
        handle = self._local.get(job_id) or JobHandle(
            id=job_id,
            name=str(result.name or "unknown"),
            organisation_id="unknown",
            status=JobStatus.PENDING,
            backend=self.backend_name,
        )
        handle.status = status_map.get(result.status, JobStatus.PENDING)
        handle.updated_at = datetime.now(UTC)
        if result.successful():
            handle.result = result.result if isinstance(result.result, dict) else {"value": result.result}
        if result.failed():
            handle.error = str(result.result)
        self._local[job_id] = handle
        return handle

    def cancel(self, job_id: str) -> JobHandle:
        self._app.control.revoke(job_id, terminate=False)
        handle = self.get_status(job_id)
        handle.status = JobStatus.CANCELLED
        handle.updated_at = datetime.now(UTC)
        return handle
