from __future__ import annotations

from fastapi import APIRouter, Depends

from aeo_engine import AeoEngine
from api.deps import AuthContext, get_auth_context
from api.schemas import ServiceStatusResponse
from competitor_engine import CompetitorEngine
from content_engine import ContentEngine
from crawler import CrawlerService
from geo_engine import GeoEngine
from intelligence import IntelligenceOrchestrator
from learning_engine import LearningEngine
from monitoring_engine import MonitoringEngine
from seo_engine import SeoEngine
from strategy_engine import StrategyEngine
from writer_engine import WriterEngine

router = APIRouter(prefix="/services", tags=["services"])


@router.get("/status", response_model=list[ServiceStatusResponse])
def list_service_status(ctx: AuthContext = Depends(get_auth_context)) -> list[ServiceStatusResponse]:
    org = ctx.organisation.id
    engines = [
        CrawlerService(org),
        IntelligenceOrchestrator(org),
        SeoEngine(org),
        GeoEngine(org),
        AeoEngine(org),
        ContentEngine(org),
        WriterEngine(org),
        CompetitorEngine(org),
        StrategyEngine(org),
        MonitoringEngine(org),
        LearningEngine(org),
    ]
    payload: list[ServiceStatusResponse] = []
    for engine in engines:
        status = engine.status()
        payload.append(
            ServiceStatusResponse(
                service=status["service"],
                organisation_id=status["organisation_id"],
                ready=bool(status["ready"]),
                features_implemented=bool(status["features_implemented"]),
                detail={k: v for k, v in status.items() if k not in {"service", "organisation_id", "ready", "features_implemented"}},
            )
        )
    return payload
