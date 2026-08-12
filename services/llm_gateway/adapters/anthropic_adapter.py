from __future__ import annotations

import os

from llm_gateway.ports import LLMCompletionRequest, LLMCompletionResponse, LLMProviderName


class AnthropicAdapter:
    name = LLMProviderName.ANTHROPIC

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

    async def complete(self, request: LLMCompletionRequest) -> LLMCompletionResponse:
        if not self._api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not configured")
        raise NotImplementedError("Live Anthropic adapter not enabled in architecture stage")
