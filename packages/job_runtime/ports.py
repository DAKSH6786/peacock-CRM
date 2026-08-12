from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Protocol


class JobStatus(StrEnum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


@dataclass(slots=True)
class JobSubmission:
    """Backend-agnostic job request."""

    name: str
    organisation_id: str
    payload: dict[str, Any]
    workspace_id: str | None = None
    idempotency_key: str | None = None
    max_retries: int = 3
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class JobHandle:
    id: str
    name: str
    organisation_id: str
    status: JobStatus
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    result: dict[str, Any] | None = None
    error: str | None = None
    backend: str = "unknown"


class JobRunner(Protocol):
    """Port for asynchronous execution.

    Celery implements this now. A future TemporalJobRunner can replace it
    without changing business services.
    """

    backend_name: str

    def enqueue(self, submission: JobSubmission) -> JobHandle: ...

    def get_status(self, job_id: str) -> JobHandle: ...

    def cancel(self, job_id: str) -> JobHandle: ...
