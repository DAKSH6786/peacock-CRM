"""OpenAI adapter stub — implement HTTP calls later; keep SDK out of business modules."""

from __future__ import annotations

import os

from llm_gateway.ports import LLMCompletionRequest, LLMCompletionResponse, LLMProviderName


class OpenAIAdapter:
    name = LLMProviderName.OPENAI

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")

    async def complete(self, request: LLMCompletionRequest) -> LLMCompletionResponse:
        if not self._api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        raise NotImplementedError("Live OpenAI adapter not enabled in architecture stage")
