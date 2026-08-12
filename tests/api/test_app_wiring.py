from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from api.config import get_settings
from api.main import create_app
from llm_gateway.ports import LLMCompletionRequest


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("JOB_BACKEND", "memory")
    get_settings.cache_clear()
    return create_app()


@pytest.mark.asyncio
async def test_llm_gateway_on_app_state(app) -> None:
    gateway = app.state.llm_gateway
    result = await gateway.complete(
        LLMCompletionRequest(
            organisation_id="org",
            role="SYNTHESIS",
            template_id="think.synthesis",
            messages=[{"role": "user", "content": "x"}],
        )
    )
    assert result.content.startswith("[null:")


@pytest.mark.asyncio
async def test_oauth_providers_endpoint(app) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/auth/oauth/providers")
    assert response.status_code == 200
    providers = {row["provider"] for row in response.json()}
    assert {"google", "microsoft", "email_password"} <= providers
