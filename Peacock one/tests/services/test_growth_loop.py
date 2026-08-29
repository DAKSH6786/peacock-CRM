from __future__ import annotations

import pytest

from growth_loop import run_growth_loop


@pytest.mark.asyncio
async def test_growth_loop_runs_every_stage_and_never_publishes_automatically() -> None:
    report = await run_growth_loop(llm_gateway=None, url="https://www.python.org", max_pages=3)

    stage_names = [s.stage for s in report.stages]
    assert stage_names == [
        "seo_aeo_geo_intelligence",
        "ai_visibility",
        "citation_gap_analysis",
        "opportunity_engine",
        "content_strategy",
        "content_creation",
        "multi_llm_simulation_and_optimization",
        "ai_agents",
        "human_experts",
        "publishing",
        "measurement",
        "experiments",
        "learning",
    ]
    assert all(s.status in {"completed", "skipped"} for s in report.stages)

    # Publishing must never auto-publish — only a preview requiring confirmation.
    if report.publishing_preview:
        assert report.publishing_preview["published"] is False

    # AI agents never take destructive action.
    for agent_result in report.agent_results.values():
        assert "cannot publish" in agent_result["guardrail_note"].lower()

    assert report.measurement_snapshot is not None
    assert report.executive_summary["peacock_visibility_score"] == report.site_intelligence["peacock_visibility_score"]


@pytest.mark.asyncio
async def test_growth_loop_rejects_invalid_url() -> None:
    with pytest.raises(Exception):
        await run_growth_loop(llm_gateway=None, url="not-a-valid-url", max_pages=1)
