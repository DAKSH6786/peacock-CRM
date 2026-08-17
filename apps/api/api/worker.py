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


@celery_app.task(name="peacock.crawl")
def crawl_task(
    organisation_id: str,
    payload: dict,
    workspace_id: str | None = None,
    metadata: dict | None = None,
) -> dict:
    from api.routes.crawler import run_crawl_job

    crawl_id = (payload or {}).get("crawl_id")
    if not crawl_id:
        return {"ok": False, "error": "crawl_id required", "organisation_id": organisation_id}
    result = run_crawl_job(crawl_id)
    result["organisation_id"] = organisation_id
    result["workspace_id"] = workspace_id
    result["metadata"] = metadata or {}
    return result


@celery_app.task(name="peacock.monitoring.snapshot")
def monitoring_snapshot_task(
    organisation_id: str,
    payload: dict,
    workspace_id: str | None = None,
    metadata: dict | None = None,
) -> dict:
    from api.db import SessionLocal
    from monitoring_engine import MonitoringService

    project_id = (payload or {}).get("project_id")
    metrics = (payload or {}).get("metrics") or []
    emit_learning = bool((payload or {}).get("emit_learning", True))
    if not project_id or not workspace_id:
        return {"ok": False, "error": "project_id and workspace_id required"}
    db = SessionLocal()
    try:
        result = MonitoringService(db).record_snapshots(
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            project_id=project_id,
            metrics=metrics,
            emit_learning=emit_learning,
        )
        result["ok"] = True
        result["metadata"] = metadata or {}
        return result
    finally:
        db.close()


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
            _memory_runner.register(
                "peacock.crawl",
                lambda payload: crawl_task("memory", payload),
            )
            _memory_runner.register(
                "peacock.monitoring.snapshot",
                lambda payload: monitoring_snapshot_task(
                    str(payload.get("organisation_id") or "memory"),
                    payload,
                    workspace_id=payload.get("workspace_id"),
                ),
            )
        return _memory_runner
    if backend == "temporal":
        return TemporalJobRunner()
    return CeleryJobRunner(celery_app)
