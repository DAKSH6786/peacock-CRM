"""Public, unauthenticated preview endpoints backing the five Peacock One
product modules (Website SEO/AEO/GEO Audit, Blog & Topic Recommendations,
Keyword & Backlink Recommendations, AI Visibility, Content Optimizer).

These endpoints must work without a database connection or bearer token so the
frontend dashboard can open every module in local development out of the box.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.config import get_settings
from api.main import create_app


@pytest.fixture
def client(monkeypatch) -> TestClient:
    monkeypatch.setenv("JOB_BACKEND", "memory")
    get_settings.cache_clear()
    return TestClient(create_app())


def test_seo_preview_is_public_and_scored(client: TestClient) -> None:
    response = client.get("/seo/preview", params={"brand": "Acme"})
    assert response.status_code == 200
    body = response.json()
    assert 0 <= body["peacock_seo_score"]["score"] <= 100
    assert body["scores"]
    assert body["recommendations"]


def test_aeo_preview_is_public_and_scored(client: TestClient) -> None:
    response = client.get("/aeo/preview", params={"brand": "Acme"})
    assert response.status_code == 200
    body = response.json()
    assert 0 <= body["aeo_score"] <= 100
    assert body["page_count"] == 2


def test_geo_lab_preview_rejects_auto_causal_conclusion(client: TestClient) -> None:
    response = client.get("/geo-lab/preview", params={"brand": "Acme"})
    assert response.status_code == 200
    body = response.json()
    assert body["auto_causal_conclusion_rejected"] is True
    assert body["deltas"]
    assert body["causality_assessments"]


def test_opportunities_preview_ranks_keyword_and_backlink_signals(client: TestClient) -> None:
    response = client.get("/opportunities/preview", params={"brand": "Acme"})
    assert response.status_code == 200
    body = response.json()
    assert body["fixed_formula_rejected"] is True
    opportunity_types = {o["opportunity_type"] for o in body["opportunities"]}
    assert "high_value_topic_available" in opportunity_types
    assert "backlink_source_gained_influence" in opportunity_types
    ranks = [o["rank"] for o in body["opportunities"]]
    assert ranks == sorted(ranks)


def test_content_lab_preview_ranks_blog_topic_proposals(client: TestClient) -> None:
    response = client.get("/content-lab/preview", params={"brand": "Acme"})
    assert response.status_code == 200
    body = response.json()
    assert body["proposals"]
    assert body["top_recommendation"]["title"] == body["proposals"][0]["title"]


def test_writer_intelligence_preview_ranks_writers(client: TestClient) -> None:
    response = client.get("/writer-intelligence/preview", params={"brand": "Acme"})
    assert response.status_code == 200
    body = response.json()
    assert body["similarity_only_rejected"] is True
    assert body["recommendations"]
    assert body["top_writer_key"] == body["recommendations"][0]["writer_key"]


def test_visibility_preview_rejects_single_shot_measurement(client: TestClient) -> None:
    response = client.get("/visibility/preview", params={"brand": "Acme"})
    assert response.status_code == 200
    body = response.json()
    assert body["single_shot_rejected"] is True
    assert 0 <= body["ai_visibility_score"] <= 100
    assert body["distributions"]
