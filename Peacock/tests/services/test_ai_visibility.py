from __future__ import annotations

import pytest

from ai_visibility import build_queries, run_ai_visibility_scan
from llm_gateway.ports import LLMCompletionRequest, LLMCompletionResponse, LLMProviderName
from llm_gateway.registry import LLMGateway


def test_build_queries_covers_multiple_intents() -> None:
    queries = build_queries(brand="Acme", topics=["widgets"], competitors=["Globex"])
    intents = {q.intent for q in queries}
    assert {"informational", "comparison", "purchase", "commercial"} <= intents
    assert all("Acme" in q.query_text or "widgets" in q.query_text for q in queries)


@pytest.mark.asyncio
async def test_ai_visibility_scan_never_fabricates_without_api_key() -> None:
    report = await run_ai_visibility_scan(llm_gateway=None, brand="Acme", topics=["widgets"], engine_codes=["chatgpt"])
    engine = report.engine_reports[0]
    assert engine.available is False
    assert engine.reason_unavailable is not None
    assert report.universal_share_of_answer is None


@pytest.mark.asyncio
async def test_ai_visibility_scan_computes_real_signals_when_live() -> None:
    class FakeProvider:
        name = LLMProviderName.OPENAI

        async def complete(self, request: LLMCompletionRequest) -> LLMCompletionResponse:
            return LLMCompletionResponse(
                provider=LLMProviderName.OPENAI,
                model="fake",
                content="Acme is a reliable, best choice. We recommend Acme. Sources: https://g2.com/acme",
            )

    gateway = LLMGateway(providers={LLMProviderName.OPENAI: FakeProvider(), LLMProviderName.NULL: FakeProvider()}, role_routing={})
    report = await run_ai_visibility_scan(llm_gateway=gateway, brand="Acme", topics=["widgets"], engine_codes=["chatgpt"])
    engine = report.engine_reports[0]
    assert engine.available is True
    assert engine.brand_mention_rate == 1.0
    assert engine.dominant_sentiment == "positive"
    assert "g2.com" in engine.top_cited_domains
