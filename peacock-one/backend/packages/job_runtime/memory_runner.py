from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, Callable

from job_runtime.ports import JobHandle, JobStatus, JobSubmission


class InMemoryJobRunner:
    """Deterministic runner for tests and local sync execution."""

    backend_name = "memory"

    def __init__(self) -> None:
        self._jobs: dict[str, JobHandle] = {}
        self._handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {}

    def register(
        self, name: str, handler: Callable[[dict[str, Any]], dict[str, Any]]
    ) -> None:
        self._handlers[name] = handler

    def enqueue(self, submission: JobSubmission) -> JobHandle:
        job_id = str(uuid.uuid4())
        handle = JobHandle(
            id=job_id,
            name=submission.name,
            organisation_id=submission.organisation_id,
            status=JobStatus.RUNNING,
            backend=self.backend_name,
        )
        self._jobs[job_id] = handle
        handler = self._handlers.get(submission.name)
        try:
            result = handler(submission.payload) if handler else {"accepted": True}
            handle.status = JobStatus.SUCCEEDED
            handle.result = result
        except Exception as exc:  # noqa: BLE001 — surface to job status
            handle.status = JobStatus.FAILED
            handle.error = str(exc)
        handle.updated_at = datetime.now(UTC)
        return handle

    def get_status(self, job_id: str) -> JobHandle:
        if job_id not in self._jobs:
            raise KeyError(f"Unknown job: {job_id}")
        return self._jobs[job_id]

    def cancel(self, job_id: str) -> JobHandle:
        handle = self.get_status(job_id)
        if handle.status in {JobStatus.PENDING, JobStatus.QUEUED, JobStatus.RUNNING}:
            handle.status = JobStatus.CANCELLED
            handle.updated_at = datetime.now(UTC)
        return handle
