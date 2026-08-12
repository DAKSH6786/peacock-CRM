from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.config import get_settings
from api.db import get_db
from api.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    settings = get_settings()
    db_status = "ok"
    redis_status = "unknown"
    try:
        db.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001
        db_status = "error"

    try:
        import redis

        client = redis.Redis.from_url(settings.redis_url, socket_connect_timeout=1)
        client.ping()
        redis_status = "ok"
    except Exception:  # noqa: BLE001
        redis_status = "error"

    overall = "ok" if db_status == "ok" else "degraded"
    return HealthResponse(
        status=overall,
        app=settings.app_name,
        env=settings.app_env,
        database=db_status,
        redis=redis_status,
        job_backend=settings.job_backend,
    )


@router.get("/ready")
def ready(db: Session = Depends(get_db)) -> dict:
    db.execute(text("SELECT 1"))
    return {"ready": True}
