from __future__ import annotations

import time

from llm_gateway.ports import (
    LLMCompletionRequest,
    LLMCompletionResponse,
    LLMProviderName,
)
from observability.metrics import TokenUsage


class NullLLMProvider:
    """Deterministic adapter for local/dev/tests — no external calls."""

    name = LLMProviderName.NULL

    async def complete(self, request: LLMCompletionRequest) -> LLMCompletionResponse:
        started = time.perf_counter()
        # Visibility probes need structured parseable output even without live keys.
        if request.template_id == "geo.visibility_probe" or request.role == "VISIBILITY_PROBE":
            brand = (request.metadata or {}).get("brand_name", "Brand")
            competitors = (request.metadata or {}).get("competitors") or []
            content = (
                f"NULL_VISIBILITY_PROBE brand={brand}. "
                f"The answer mentions {brand} in position 2 and cites {brand.lower()}.example. "
                f"Competitors mentioned: {', '.join(competitors[:3]) or 'none'}."
            )
            structured = {
                "role": request.role,
                "ok": True,
                "brand_mentioned": True,
                "brand_cited": True,
                "brand_top3": True,
                "brand_position": 2,
                "competitor_mentions": list(competitors[:3]),
            }
        else:
            content = (
                f"[null:{request.role}] template={request.template_id} "
                f"messages={len(request.messages)}"
            )
            structured = {"role": request.role, "ok": True}
        return LLMCompletionResponse(
            provider=self.name,
            model="null-1",
            content=content,
            structured_summary=structured,
            usage=TokenUsage(prompt_tokens=10, completion_tokens=20),
            cost_usd_micros=0,
            latency_ms=int((time.perf_counter() - started) * 1000),
            request_id="null",
        )
