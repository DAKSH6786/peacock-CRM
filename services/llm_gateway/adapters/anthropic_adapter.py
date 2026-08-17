"""Anthropic Messages API adapter (httpx)."""

from __future__ import annotations

import os
import time

from llm_gateway.adapters.http_utils import (
    default_model,
    estimate_cost_usd_micros,
    post_json,
    require_api_key,
)
from llm_gateway.ports import LLMCompletionRequest, LLMCompletionResponse, LLMProviderName
from observability.metrics import TokenUsage

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-3-5-haiku-latest"


class AnthropicAdapter:
    name = LLMProviderName.ANTHROPIC

    def __init__(self, api_key: str | None = None, *, base_url: str = ANTHROPIC_URL) -> None:
        self._api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self._base_url = base_url

    async def complete(self, request: LLMCompletionRequest) -> LLMCompletionResponse:
        api_key = require_api_key(self._api_key, "ANTHROPIC_API_KEY")
        model = default_model(request, DEFAULT_MODEL)
        timeout = float(request.timeout_seconds or 60.0)

        system_parts: list[str] = []
        messages: list[dict[str, str]] = []
        for msg in request.messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                system_parts.append(content)
            else:
                messages.append({"role": "user" if role != "assistant" else "assistant", "content": content})
        if not messages:
            messages = [{"role": "user", "content": ""}]

        payload: dict = {
            "model": model,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "messages": messages,
        }
        if system_parts:
            payload["system"] = "\n\n".join(system_parts)

        data, latency_ms = await post_json(
            self._base_url,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            payload=payload,
            timeout=timeout,
        )
        blocks = data.get("content") or []
        texts = [
            block.get("text", "")
            for block in blocks
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        usage_raw = data.get("usage") or {}
        prompt_tokens = int(usage_raw.get("input_tokens") or 0)
        completion_tokens = int(usage_raw.get("output_tokens") or 0)
        return LLMCompletionResponse(
            provider=self.name,
            model=model,
            content="\n".join(texts),
            structured_summary={"stop_reason": data.get("stop_reason")},
            usage=TokenUsage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens),
            cost_usd_micros=estimate_cost_usd_micros(
                prompt_tokens, completion_tokens, per_mtok_in=0.8, per_mtok_out=4.0
            ),
            latency_ms=latency_ms or int(time.perf_counter() * 0),
            request_id=data.get("id"),
        )
