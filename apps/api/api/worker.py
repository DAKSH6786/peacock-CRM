from __future__ import annotations

from celery import Celery

from api.config import get_settings
from job_runtime import CeleryJobRunner, InMemoryJobRunner, JobRunner
from job_runtime.temporal_runner import TemporalJobRunner

settings = get_settings()

celery_app = Celery(
    "peacock_one",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)
celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    worker_prefetch_multiplier=1,
)


@celery_app.task(name="peacock.ping")
def ping_task(
    organisation_id: str,
    payload: dict,
    workspace_id: str | None = None,
    metadata: dict | None = None,
) -> dict:
    return {
        "ok": True,
        "organisation_id": organisation_id,
        "workspace_id": workspace_id,
        "payload": payload,
        "metadata": metadata or {},
    }


_memory_runner: InMemoryJobRunner | None = None


def get_job_runner() -> JobRunner:
    global _memory_runner
    current = get_settings()
    backend = current.job_backend.lower()
    if backend == "memory":
        if _memory_runner is None:
            _memory_runner = InMemoryJobRunner()
            _memory_runner.register(
                "peacock.ping",
                lambda payload: {"ok": True, "payload": payload},
            )
        return _memory_runner
    if backend == "temporal":
        return TemporalJobRunner()
    return CeleryJobRunner(celery_app)
