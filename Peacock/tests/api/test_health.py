from __future__ import annotations

from fastapi.testclient import TestClient

from api.config import get_settings
from api.main import create_app


def test_health_endpoint_shape(monkeypatch) -> None:
    monkeypatch.setenv("JOB_BACKEND", "memory")
    get_settings.cache_clear()
    app = create_app()
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert "status" in body
    assert "job_backend" in body
    assert body["app"]
    assert body["job_backend"] == "memory"


def test_api_root_is_not_bare_404(monkeypatch) -> None:
    monkeypatch.setenv("JOB_BACKEND", "memory")
    get_settings.cache_clear()
    app = create_app()
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["web_ui"]
    assert body["docs"] == "/docs"
    assert body["health"] == "/health"
    assert "port 3000" in body["message"]
