from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import get_settings
from api.routes import (
    action_engine,
    agentic_readiness,
    anomaly_engine,
    ask_peacock,
    auth,
    capabilities,
    citation_graph,
    command_centre,
    content_digital_twin,
    content_lab,
    council2,
    crawler,
    deep_competitor,
    entity_intelligence,
    evidence_ledger,
    executive_brain,
    geo_lab,
    health,
    intelligence,
    jobs,
    judge2,
    learning_engine2,
    opportunity_engine,
    peacock90,
    proprietary_metrics,
    research_mode,
    moat_data_model,
    cost_intelligence,
    enterprise_reliability,
    scenario_engine,
    prompt_universe,
    retrieval_pathway,
    revenue_attribution,
    seo,
    services,
    share_of_answer,
    temporal_intelligence,
    visibility,
    writer_intelligence,
)
from llm_gateway import LLMGateway, NullLLMProvider
from llm_gateway.ports import LLMProviderName
from observability.logging import configure_logging, get_logger


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level, json_logs=settings.app_env != "local")
    get_logger("api").info("api_starting", env=settings.app_env, job_backend=settings.job_backend)
    yield
    get_logger("api").info("api_stopping")


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(health.router)
    application.include_router(auth.router)
    application.include_router(services.router)
    application.include_router(jobs.router)
    application.include_router(crawler.router)
    application.include_router(seo.router)
    application.include_router(intelligence.router)
    application.include_router(evidence_ledger.router)
    application.include_router(capabilities.router)
    application.include_router(visibility.router)
    application.include_router(prompt_universe.router)
    application.include_router(share_of_answer.router)
    application.include_router(citation_graph.router)
    application.include_router(retrieval_pathway.router)
    application.include_router(entity_intelligence.router)
    application.include_router(deep_competitor.router)
    application.include_router(content_lab.router)
    application.include_router(content_digital_twin.router)
    application.include_router(geo_lab.router)
    application.include_router(writer_intelligence.router)
    application.include_router(opportunity_engine.router)
    application.include_router(council2.router)
    application.include_router(judge2.router)
    application.include_router(scenario_engine.router)
    application.include_router(peacock90.router)
    application.include_router(action_engine.router)
    application.include_router(agentic_readiness.router)
    application.include_router(revenue_attribution.router)
    application.include_router(learning_engine2.router)
    application.include_router(temporal_intelligence.router)
    application.include_router(anomaly_engine.router)
    application.include_router(ask_peacock.router)
    application.include_router(command_centre.router)
    application.include_router(executive_brain.router)
    application.include_router(proprietary_metrics.router)
    application.include_router(research_mode.router)
    application.include_router(moat_data_model.router)
    application.include_router(cost_intelligence.router)
    application.include_router(enterprise_reliability.router)

    # Soft static role fallbacks only — PINE should prefer CapabilityRouter
    # dynamic selection (request.provider / request.model). Never treat these
    # as permanent Claude=critic / Perplexity=research / GPT=strategy locks.
    application.state.llm_gateway = LLMGateway(
        providers={LLMProviderName.NULL: NullLLMProvider()},
        role_routing={
            "WEB_RESEARCH": LLMProviderName.NULL,
            "SYNTHESIS": LLMProviderName.NULL,
            "VERIFY_ADVERSARIAL": LLMProviderName.NULL,
            "VISIBILITY_PROBE": LLMProviderName.NULL,
        },
        max_retries=settings.llm_max_retries,
        default_timeout_seconds=settings.llm_default_timeout_seconds,
    )
    return application


app = create_app()
