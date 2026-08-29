"""Future Temporal adapter stub — swap CeleryJobRunner without rewriting services."""

from __future__ import annotations

from job_runtime.ports import JobHandle, JobStatus, JobSubmission


class TemporalJobRunner:
    """Placeholder for Temporal implementation.

    Keep the same JobRunner port. Wire via JOB_BACKEND=temporal when ready.
    """

    backend_name = "temporal"

    def enqueue(self, submission: JobSubmission) -> JobHandle:
        raise NotImplementedError(
            "Temporal backend is reserved. Use JOB_BACKEND=celery or memory."
        )

    def get_status(self, job_id: str) -> JobHandle:
        raise NotImplementedError("Temporal backend is reserved.")

    def cancel(self, job_id: str) -> JobHandle:
        raise NotImplementedError("Temporal backend is reserved.")
