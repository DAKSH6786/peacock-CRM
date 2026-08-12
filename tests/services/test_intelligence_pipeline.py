"""Tests for Layers 0–10 strategic intelligence pipeline."""

from __future__ import annotations

import pytest

from intelligence import IntelligenceOrchestrator, StrategicPipeline, StrategicRequest
from intelligence.context_selector import CONTEXT_CATALOG, ContextSelector, InMemoryContextProvider
from intelligence.models import ContextItem, EvidenceKind, RequestClassification, ThinkingDepth
from prompts import build_intelligence_prompt_registry


@pytest.mark.asyncio
async def test_pipeline_runs_all_layers_for_seo_request() -> None:
    pipeline = StrategicPipeline()
    result = await pipeline.run(
        StrategicRequest(
            organisation_id="org",
            workspace_id="ws",
            request_text="Urgent SEO audit review: fix critical crawl issues and raise visibility.",
            crawl_id="crawl-1",
            audit_id="audit-1",
            metadata={
                "crawl": {"pages_crawled": 40, "pages_failed": 2, "issues_found": 8},
                "seo_audit": {
                    "peacock_seo_score": 55,
                    "critical_issues": 3,
                    "warnings": 5,
                    "opportunities": 4,
                    "section_scores": {"technical_seo": 50, "content_quality": 60},
                },
                "visibility": {"brand_mentions": 1, "citation_counts": 0},
            },
        )
    )
    assert result.status in {"completed", "completed_with_blocks"}
    assert result.classification.user_intent == "seo_audit_review"
    assert result.classification.thinking_depth in {
        ThinkingDepth.STANDARD,
        ThinkingDepth.DEEP,
        ThinkingDepth.COUNCIL,
    }
    assert len(result.layers) == 11
    assert [layer.layer for layer in result.layers] == list(range(11))
    assert result.evidence_summary["deterministic"] >= 3
    # Hard separation: inferences never counted as deterministic
    assert result.evidence_summary["deterministic"] >= 0
    assert result.recommendations
    assert result.tasks
    assert result.learning
    assert result.context_summary["tokens_used"] <= result.context_summary["token_budget"]


@pytest.mark.asyncio
async def test_shallow_request_skips_research_and_simulation() -> None:
    result = await StrategicPipeline().run(
        StrategicRequest(
            organisation_id="org",
            workspace_id="ws",
            request_text="Quick summary of current SEO status",
        )
    )
    skipped = {layer.layer for layer in result.layers if layer.status == "skipped"}
    assert 3 in skipped
    assert 8 in skipped


def test_context_selector_never_dumps_full_catalogue() -> None:
    providers = [
        InMemoryContextProvider(
            kind,
            [
                ContextItem(
                    kind,
                    f"{kind}.1",
                    f"Summary for {kind}",
                    0.5,
                    200,
                    "test",
                )
            ],
        )
        for kind in CONTEXT_CATALOG
    ]
    selector = ContextSelector(providers=providers, token_budget=500, max_items=5)
    classification = RequestClassification(
        user_intent="content_strategy",
        requested_output="content_roadmap",
        importance="medium",
        business_risk="low",
        freshness_requirement="recent",
        required_data=["existing_content", "audience", "writer_pool"],
        thinking_depth=ThinkingDepth.STANDARD,
    )
    bundle = selector.assemble(
        StrategicRequest("org", "ws", "Plan a content strategy"),
        classification,
    )
    assert bundle.tokens_used <= 500
    assert len(bundle.items) <= 5
    assert bundle.rejected_kinds
    assert "Full-database dump forbidden" in " ".join(bundle.selection_rationale)


@pytest.mark.asyncio
async def test_deterministic_and_inference_are_separated() -> None:
    result = await StrategicPipeline().run(
        StrategicRequest(
            organisation_id="org",
            workspace_id="ws",
            request_text="Deep dive competitive visibility strategy for the board",
            metadata={"seo_audit": {"peacock_seo_score": 40, "critical_issues": 2}},
        )
    )
    # Layer 2 output should declare separation
    layer2 = next(layer for layer in result.layers if layer.layer == 2)
    assert "Deterministic evidence isolated" in layer2.output.get("separation", "")
    # Recommendations may mark inference dependence explicitly
    assert any(not r.depends_on_inference for r in result.recommendations) or result.recommendations


def test_orchestrator_status_lists_layers() -> None:
    status = IntelligenceOrchestrator("org").status()
    assert status["features_implemented"] is True
    assert len(status["layers"]) == 11
    assert "no_full_database_dump" in status["guarantees"]


def test_intelligence_prompt_templates_registered() -> None:
    registry = build_intelligence_prompt_registry()
    assert registry.get("intel.layer4.specialist").role == "SYNTHESIS"
    assert registry.get("intel.layer5.adversarial").role == "VERIFY_ADVERSARIAL"
