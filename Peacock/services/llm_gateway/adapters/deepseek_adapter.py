"""DeepSeek chat completions adapter (OpenAI-compatible, httpx)."""

from __future__ import annotations

import os

from llm_gateway.adapters.http_utils import (
    default_model,
    openai_compatible_response,
    post_json,
    require_api_key,
)
from llm_gateway.ports import LLMCompletionRequest, LLMCompletionResponse, LLMProviderName

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_MODEL = "deepseek-chat"


class DeepSeekAdapter:
    name = LLMProviderName.DEEPSEEK

    def __init__(self, api_key: str | None = None, *, base_url: str = DEEPSEEK_URL) -> None:
        self._api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self._base_url = base_url

    async def complete(self, request: LLMCompletionRequest) -> LLMCompletionResponse:
        api_key = require_api_key(self._api_key, "DEEPSEEK_API_KEY")
        model = default_model(request, DEFAULT_MODEL)
        timeout = float(request.timeout_seconds or 60.0)
        data, latency_ms = await post_json(
            self._base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            payload={
                "model": model,
                "messages": request.messages,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
            },
            timeout=timeout,
        )
        return openai_compatible_response(
            provider=self.name,
            model=model,
            data=data,
            latency_ms=latency_ms,
            cost_in=0.14,
            cost_out=0.28,
        )
