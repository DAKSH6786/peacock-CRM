"""Peacock Growth Loop API — real crawl of a public site (network access required).

Skipped automatically if outbound network access is unavailable, matching
``tests/api/test_site_intelligence_routes.py``.
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


def test_growth_loop_run_end_to_end(client: TestClient) -> None:
    response = client.post("/growth-loop/run", json={"url": "https://www.python.org", "max_pages": 3})
    assert response.status_code == 200
    body = response.json()
    assert body["brand"]
    assert len(body["stages"]) == 13
    assert body["site_intelligence"]["crawled_pages_count"] > 0
    assert body["measurement_snapshot"] is not None
    if body["publishing_preview"]:
        assert body["publishing_preview"]["published"] is False


def test_growth_loop_run_rejects_invalid_url(client: TestClient) -> None:
    response = client.post("/growth-loop/run", json={"url": "not-a-valid-url", "max_pages": 1})
    assert response.status_code == 400


def test_growth_loop_agents_list(client: TestClient) -> None:
    response = client.get("/growth-loop/agents")
    assert response.status_code == 200
    assert len(response.json()["agents"]) == 12


def test_growth_loop_publishing_connectors(client: TestClient) -> None:
    response = client.get("/growth-loop/publishing/connectors")
    assert response.status_code == 200
    names = {c["name"] for c in response.json()["connectors"]}
    assert {"manual", "wordpress", "webflow", "shopify"} == names


def test_growth_loop_expert_workflow_via_api(client: TestClient) -> None:
    from peacock_experts import create_task

    task = create_task(title="API test task", task_type="content_brief", content="draft")
    response = client.post(
        f"/growth-loop/experts/tasks/{task.task_id}/assign", json={"assignee": "Jane", "assignee_role": "seo_expert"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "human_assigned"

    response = client.post(f"/growth-loop/experts/tasks/{task.task_id}/start-review")
    assert response.status_code == 200
    response = client.post(f"/growth-loop/experts/tasks/{task.task_id}/approve", json={"approver": "Jane"})
    assert response.status_code == 200
    assert response.json()["status"] == "approved"


def test_growth_loop_experiment_lifecycle_via_api(client: TestClient) -> None:
    response = client.post(
        "/growth-loop/experiments",
        json={"hypothesis": "Test hypothesis", "page_url": "https://example.com/", "change_description": "Test change"},
    )
    assert response.status_code == 200
    experiment_id = response.json()["experiment_id"]

    response = client.post(f"/growth-loop/experiments/{experiment_id}/evaluate")
    assert response.status_code == 200
    assert "does not by itself prove" in response.json()["causality_caution"]
