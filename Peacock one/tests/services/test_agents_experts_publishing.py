from __future__ import annotations

import pytest

from peacock_agents import AGENT_REGISTRY, run_technical_seo_agent
from peacock_experts import approve_task, assign_task, create_task, mark_ready_to_publish, start_review
from peacock_publishing import PublishRequest, get_connector, list_connectors


def test_all_twelve_agents_are_registered() -> None:
    expected = {
        "seo_agent", "aeo_agent", "geo_agent", "research_agent", "content_strategist_agent",
        "competitor_agent", "citation_agent", "internal_linking_agent", "technical_seo_agent",
        "content_refresh_agent", "measurement_agent", "experiment_agent",
    }
    assert expected == set(AGENT_REGISTRY.keys())


def test_technical_seo_agent_never_makes_destructive_changes() -> None:
    result = run_technical_seo_agent({"pages_with_broken_status": 2, "pages_js_heavy": 0, "pages_missing_schema": 0, "robots_txt_present": True, "sitemap_urls_found": 1})
    assert result.tasks
    assert all(task.requires_approval for task in result.tasks)
    assert "cannot publish" in result.guardrail_note.lower()


def test_expert_workflow_state_machine_rejects_invalid_transitions() -> None:
    task = create_task(title="Test brief", task_type="content_brief", content="draft")
    assert task.status == "ai_generated"
    with pytest.raises(ValueError):
        approve_task(task.task_id, approver="Jane")  # cannot approve before review

    task = assign_task(task.task_id, assignee="Jane", assignee_role="seo_expert")
    task = start_review(task.task_id)
    task = approve_task(task.task_id, approver="Jane")
    task = mark_ready_to_publish(task.task_id)
    assert task.status == "ready_to_publish"
    assert task.approved_by == "Jane"


@pytest.mark.asyncio
async def test_manual_connector_never_calls_external_system_and_requires_confirmation() -> None:
    connector = get_connector("manual")
    result = await connector.publish(PublishRequest(title="T", body="B"), confirm=False)
    assert result.status == "requires_confirmation"
    assert result.published is False

    result2 = await connector.publish(PublishRequest(title="T", body="B"), confirm=True)
    assert result2.published is False  # Peacock never auto-publishes
    assert result2.status == "draft_created"


@pytest.mark.asyncio
async def test_wordpress_connector_reports_not_configured_without_credentials(monkeypatch) -> None:
    monkeypatch.delenv("WORDPRESS_URL", raising=False)
    monkeypatch.delenv("WORDPRESS_USERNAME", raising=False)
    monkeypatch.delenv("WORDPRESS_APP_PASSWORD", raising=False)
    from peacock_publishing.wordpress_connector import WordPressConnector

    connector = WordPressConnector()
    result = await connector.publish(PublishRequest(title="T", body="B"), confirm=True)
    assert result.status == "not_configured"


def test_list_connectors_reports_configuration_status() -> None:
    connectors = list_connectors()
    names = {c["name"] for c in connectors}
    assert {"manual", "wordpress", "webflow", "shopify"} == names
    manual = next(c for c in connectors if c["name"] == "manual")
    assert manual["configured"] is True
