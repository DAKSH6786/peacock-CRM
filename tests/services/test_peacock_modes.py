"""Peacock Fast / Standard / Deep / Council / Lab modes."""

from __future__ import annotations

import pytest

from intelligence import (
    PeacockMode,
    StrategicPipeline,
    StrategicRequest,
    list_mode_catalog,
    profile_for,
    resolve_mode,
)
from intelligence.models import ThinkingDepth
from intelligence.peacock_modes import ModeBudgetTracker


def test_all_modes_declare_hard_budgets() -> None:
    catalog = list_mode_catalog()
    assert {row["mode"] for row in catalog} == {
        "peacock_fast",
        "peacock_standard",
        "peacock_deep",
        "peacock_council",
        "peacock_lab",
    }
    for row in catalog:
        budget = row["budget"]
        for key in ("max_cost", "max_calls", "max_iterations", "max_runtime"):
            assert key in budget
            assert budget[key] > 0


def test_mode_capabilities_match_product_contract() -> None:
    fast = profile_for(PeacockMode.FAST)
    assert fast.capabilities.single_pass is True
    assert fast.capabilities.enable_research is False

    standard = profile_for(PeacockMode.STANDARD)
    assert standard.capabilities.multiple_evidence_sources is True
    assert standard.capabilities.primary_reasoning_models == 1
    assert standard.capabilities.verification_when_required is True

    deep = profile_for(PeacockMode.DEEP)
    assert deep.capabilities.agent_count_hint >= 3
    assert deep.capabilities.enable_research is True
    assert deep.capabilities.enable_critic is True
    assert deep.capabilities.enable_verification is True

    council = profile_for(PeacockMode.COUNCIL)
    assert council.capabilities.independent_models is True
    assert council.capabilities.adversarial_reasoning is True
    assert council.capabilities.evidence_reconciliation is True

    lab = profile_for(PeacockMode.LAB)
    assert lab.capabilities.allow_repeated_measurements is True
    assert lab.capabilities.allow_prompt_experiments is True
    assert lab.capabilities.allow_content_simulations is True
    assert lab.capabilities.allow_controlled_comparisons is True
    assert lab.capabilities.allow_hypothesis_tests is True


def test_resolve_mode_explicit_and_cues() -> None:
    assert resolve_mode(explicit="peacock_lab") == PeacockMode.LAB
    assert resolve_mode(request_text="Run a quick summary") == PeacockMode.FAST
    assert resolve_mode(request_text="Deep dive multi-agent visibility") == PeacockMode.DEEP
    assert resolve_mode(request_text="Council strategic decision for the board") == PeacockMode.COUNCIL
    assert resolve_mode(request_text="Lab hypothesis test with prompt experiments") == PeacockMode.LAB
    assert resolve_mode(thinking_depth=ThinkingDepth.STANDARD) == PeacockMode.STANDARD


def test_budget_tracker_exhausts_on_max_calls() -> None:
    profile = profile_for(PeacockMode.FAST)
    tracker = ModeBudgetTracker(
        type(profile.budget)(
            max_cost=profile.budget.max_cost,
            max_calls=2,
            max_iterations=profile.budget.max_iterations,
            max_runtime=profile.budget.max_runtime,
        )
    )
    assert tracker.checkpoint() is True
    tracker.record_call()
    tracker.record_call()
    assert tracker.exhausted() == "max_calls"
    assert tracker.checkpoint() is False


@pytest.mark.asyncio
async def test_explicit_modes_drive_pipeline() -> None:
    pipeline = StrategicPipeline()

    fast = await pipeline.run(
        StrategicRequest("org", "ws", "Analyse homepage titles", peacock_mode="peacock_fast")
    )
    assert fast.peacock_mode == "peacock_fast"
    assert fast.mode["capabilities"]["single_pass"] is True

    standard = await pipeline.run(
        StrategicRequest(
            "org",
            "ws",
            "Build an SEO content plan with evidence",
            peacock_mode="peacock_standard",
        )
    )
    assert standard.peacock_mode == "peacock_standard"
    assert standard.mode["capabilities"]["multiple_evidence_sources"] is True

    deep = await pipeline.run(
        StrategicRequest(
            "org",
            "ws",
            "Deep multi-agent visibility review",
            peacock_mode="peacock_deep",
        )
    )
    assert deep.peacock_mode == "peacock_deep"
    assert deep.mode["capabilities"]["enable_critic"] is True

    council = await pipeline.run(
        StrategicRequest(
            "org",
            "ws",
            "Strategic board decision on market expansion",
            peacock_mode="peacock_council",
        )
    )
    assert council.peacock_mode == "peacock_council"
    assert council.mode["capabilities"]["evidence_reconciliation"] is True

    lab = await pipeline.run(
        StrategicRequest(
            "org",
            "ws",
            "Lab mode: compare two prompt variants and test the hypothesis",
            peacock_mode="peacock_lab",
        )
    )
    assert lab.peacock_mode == "peacock_lab"
    assert lab.mode["lab_plan"] is not None
    assert lab.mode["lab_plan"]["hypothesis_tests"] is True
    for key in ("max_cost", "max_calls", "max_iterations", "max_runtime"):
        assert key in lab.mode["budget"]
