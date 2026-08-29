"""Site Intelligence API — real crawl of a public site (network access required).

These tests hit the live network (like the manual verification in the task
report) rather than mocking the crawler, so they honestly prove the endpoint
end to end. They are skipped automatically if outbound network access is
unavailable in the current sandbox.
"""

from __future__ import annotations

import socket

import pytest
from fastapi.testclient import TestClient

from api.config import get_settings
from api.main import create_app


def _network_available() -> bool:
    try:
        socket.create_connection(("www.python.org", 443), timeout=3).close()
        return True
    except OSError:
        return False


pytestmark = pytest.mark.skipif(not _network_available(), reason="No outbound network access in this environment")


@pytest.fixture
def client(monkeypatch) -> TestClient:
    monkeypatch.setenv("JOB_BACKEND", "memory")
    get_settings.cache_clear()
    return TestClient(create_app())


def test_analyze_real_public_site_returns_full_report(client: TestClient) -> None:
    response = client.post(
        "/site-intelligence/analyze",
        json={"url": "https://www.python.org", "max_pages": 5},
    )
    assert response.status_code == 200
    body = response.json()

    assert body["crawled_pages_count"] > 0
    assert 0 <= body["seo_score"] <= 100
    assert 0 <= body["aeo_score"] <= 100
    assert 0 <= body["geo_score"] <= 100
    assert len(body["ai_visibility"]) == 5
    # Never fabricate LLM visibility for a plugin with no configured API key.
    for entry in body["ai_visibility"]:
        if not entry["available"]:
            assert entry["score"] is None
            assert entry["reason_unavailable"]
    assert body["backlink_opportunities"].startswith("Data unavailable")
    assert body["data_availability"]["measured"]
    assert body["data_availability"]["unavailable"]
    assert body["pages"]
    for page in body["pages"]:
        for key in ("seo_score", "aeo_score", "geo_score", "content_score", "technical_score", "authority_score"):
            assert 0 <= page[key] <= 100


def test_analyze_rejects_private_host_target(client: TestClient) -> None:
    response = client.post(
        "/site-intelligence/analyze",
        json={"url": "http://localhost:9999", "max_pages": 4},
    )
    assert response.status_code == 400
    assert "blocked" in response.json()["detail"].lower() or "could not crawl" in response.json()["detail"].lower()


def test_analyze_with_competitor_url_produces_real_diff(client: TestClient) -> None:
    response = client.post(
        "/site-intelligence/analyze",
        json={
            "url": "https://www.python.org",
            "competitor_url": "https://www.djangoproject.com",
            "max_pages": 3,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["competitor_gap"]["available"] is True
    assert body["competitor_gap"]["why_competitor_is_winning"]
