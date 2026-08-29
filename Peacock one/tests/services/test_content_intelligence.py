from __future__ import annotations

import pytest

from content_intelligence import (
    build_content_graph,
    generate_content_brief,
    recommend_content_types,
    simulate_geo_readiness,
    simulate_multi_llm_readiness,
)


def test_build_content_graph_has_full_relationship_chain() -> None:
    graph = build_content_graph(
        brand="Acme",
        topics=["widgets", "gadgets"],
        entities=["Acme", "Globex"],
        keywords=["widget pricing"],
        queries=[("What is Acme?", "informational")],
        pages=[("https://acme.com/", "Acme Home")],
    )
    kinds = {n.kind for n in graph.nodes}
    assert {"brand", "topic", "entity", "keyword", "query", "prompt", "page"} <= kinds
    assert graph.edges


def test_recommend_content_types_reacts_to_gaps() -> None:
    recs = recommend_content_types(
        missing_topics=["ai visibility"], missing_entities=["Perplexity"], competitor_names=["Semrush"], has_information_gain_gap=True
    )
    content_types = {r.content_type for r in recs}
    assert "pillar_page" in content_types
    assert "comparison_page" in content_types
    assert "research_content" in content_types


def test_generate_content_brief_never_fabricates_research() -> None:
    brief = generate_content_brief(
        topic="AI visibility", brand="Acme", related_entities=[], related_questions=[], internal_link_candidates=[]
    )
    assert any("does not invent research" in note for note in brief.research_notes)
    assert brief.sources_needed


def test_simulate_geo_readiness_is_deterministic() -> None:
    draft = "# AI Visibility\n\nWhat is AI visibility? It is how brands appear in AI answers."
    breakdown_1 = simulate_geo_readiness(draft)
    breakdown_2 = simulate_geo_readiness(draft)
    assert breakdown_1.geo_score == breakdown_2.geo_score


@pytest.mark.asyncio
async def test_simulate_multi_llm_readiness_labels_unavailable_plugins() -> None:
    result = await simulate_multi_llm_readiness(
        llm_gateway=None, draft_text="# Topic\n\nSome text.", topic="Topic", brand="Acme", engine_codes=["chatgpt"]
    )
    assert result["per_platform"][0]["live_critique_available"] is False
    assert "no live api key" in result["per_platform"][0]["note"].lower()
