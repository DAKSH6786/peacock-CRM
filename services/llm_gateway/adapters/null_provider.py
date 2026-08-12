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
        content = (
            f"[null:{request.role}] template={request.template_id} "
            f"messages={len(request.messages)}"
        )
        return LLMCompletionResponse(
            provider=self.name,
            model="null-1",
            content=content,
            structured_summary={"role": request.role, "ok": True},
            usage=TokenUsage(prompt_tokens=10, completion_tokens=20),
            cost_usd_micros=0,
            latency_ms=int((time.perf_counter() - started) * 1000),
            request_id="null",
        )
