from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import get_settings
from api.routes import auth, crawler, health, intelligence, jobs, seo, services
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

    # Composition root — gateway uses null provider until keys + live adapters enabled
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
