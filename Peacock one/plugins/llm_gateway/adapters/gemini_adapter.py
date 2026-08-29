"""Google Gemini generateContent adapter (httpx)."""

from __future__ import annotations

import os

from llm_gateway.adapters.http_utils import (
    default_model,
    estimate_cost_usd_micros,
    post_json,
    require_api_key,
)
from llm_gateway.ports import LLMCompletionRequest, LLMCompletionResponse, LLMProviderName
from observability.metrics import TokenUsage

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
DEFAULT_MODEL = "gemini-2.0-flash"


class GeminiAdapter:
    name = LLMProviderName.GEMINI

    def __init__(self, api_key: str | None = None, *, base_url: str = GEMINI_BASE) -> None:
        self._api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self._base_url = base_url.rstrip("/")

    async def complete(self, request: LLMCompletionRequest) -> LLMCompletionResponse:
        api_key = require_api_key(self._api_key, "GEMINI_API_KEY")
        model = default_model(request, DEFAULT_MODEL)
        timeout = float(request.timeout_seconds or 60.0)

        contents: list[dict] = []
        system_instruction = None
        for msg in request.messages:
            role = msg.get("role", "user")
            text = msg.get("content", "")
            if role == "system":
                system_instruction = {"parts": [{"text": text}]}
                continue
            contents.append(
                {
                    "role": "model" if role == "assistant" else "user",
                    "parts": [{"text": text}],
                }
            )
        if not contents:
            contents = [{"role": "user", "parts": [{"text": ""}]}]

        payload: dict = {
            "contents": contents,
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens,
            },
        }
        if system_instruction:
            payload["systemInstruction"] = system_instruction

        url = f"{self._base_url}/{model}:generateContent?key={api_key}"
        data, latency_ms = await post_json(
            url,
            headers={"Content-Type": "application/json"},
            payload=payload,
            timeout=timeout,
        )
        candidates = data.get("candidates") or []
        if not candidates:
            raise RuntimeError("Gemini returned no candidates")
        parts = (((candidates[0].get("content") or {}).get("parts")) or [])
        content = "".join(part.get("text", "") for part in parts if isinstance(part, dict))
        usage_raw = data.get("usageMetadata") or {}
        prompt_tokens = int(usage_raw.get("promptTokenCount") or 0)
        completion_tokens = int(usage_raw.get("candidatesTokenCount") or 0)
        return LLMCompletionResponse(
            provider=self.name,
            model=model,
            content=content,
            structured_summary={"finish_reason": candidates[0].get("finishReason")},
            usage=TokenUsage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens),
            cost_usd_micros=estimate_cost_usd_micros(
                prompt_tokens, completion_tokens, per_mtok_in=0.1, per_mtok_out=0.4
            ),
            latency_ms=latency_ms,
            request_id=None,
        )
