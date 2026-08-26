"""Public GEO Intelligence endpoints — AI Gateway plugin catalog, preview, and analyses."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.config import get_settings
from api.main import create_app


@pytest.fixture
def client(monkeypatch) -> TestClient:
    monkeypatch.setenv("JOB_BACKEND", "memory")
    # Never hardcode credentials: explicitly ensure no provider keys leak into this test run.
    for env_var in (
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GEMINI_API_KEY",
        "PERPLEXITY_API_KEY",
        "DEEPSEEK_API_KEY",
    ):
        monkeypatch.delenv(env_var, raising=False)
    get_settings.cache_clear()
    return TestClient(create_app())


def test_plugin_catalog_lists_all_five_ai_plugins_as_not_live(client: TestClient) -> None:
    response = client.get("/geo-intelligence/plugins")
    assert response.status_code == 200
    body = response.json()
    codes = {p["engine_code"] for p in body["plugins"]}
    assert codes == {"chatgpt", "gemini", "claude", "perplexity", "deepseek"}
    assert all(not p["live"] for p in body["plugins"])
    assert "not a guarantee" in body["disclaimer"].lower()


def test_geo_intelligence_preview_is_public_and_covers_all_plugins(client: TestClient) -> None:
    response = client.get("/geo-intelligence/preview", params={"brand": "Acme"})
    assert response.status_code == 200
    body = response.json()
    assert body["client_brand"] == "Acme"
    assert {r["engine_code"] for r in body["provider_responses"]} == {
        "chatgpt",
        "gemini",
        "claude",
        "perplexity",
        "deepseek",
    }
    assert len(body["recommendations"]) == 5
    for rec in body["recommendations"]:
        assert rec["opportunities"]
    assert body["keywords"]
    assert body["entities"]


def test_geo_intelligence_analysis_accepts_custom_inputs(client: TestClient) -> None:
    response = client.post(
        "/geo-intelligence/analyses",
        json={
            "client_brand": "Northwind",
            "competitors": ["Contoso"],
            "site_topics": ["widgets"],
            "engine_codes": ["chatgpt", "claude"],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["client_brand"] == "Northwind"
    assert {r["engine_code"] for r in body["provider_responses"]} == {"chatgpt", "claude"}
    assert all(r["simulated"] for r in body["provider_responses"])
