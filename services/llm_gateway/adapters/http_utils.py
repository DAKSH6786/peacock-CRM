"""Shared HTTP helpers for live LLM provider adapters."""

from __future__ import annotations

import time
from typing import Any

import httpx

from llm_gateway.ports import LLMCompletionRequest, LLMCompletionResponse, LLMProviderName
from llm_gateway.registry import ProviderTimeoutError, RateLimitError
from observability.metrics import TokenUsage


def estimate_cost_usd_micros(prompt_tokens: int, completion_tokens: int, *, per_mtok_in: float, per_mtok_out: float) -> int:
    """Rough USD micros estimate from public list prices (not billing-grade)."""
    cost = (prompt_tokens / 1_000_000.0) * per_mtok_in + (completion_tokens / 1_000_000.0) * per_mtok_out
    return int(round(cost * 1_000_000))


async def post_json(
    url: str,
    *,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout: float,
) -> tuple[dict[str, Any], int]:
    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
    except httpx.TimeoutException as exc:
        raise ProviderTimeoutError(str(exc)) from exc
    except httpx.HTTPError as exc:
        raise RuntimeError(f"LLM HTTP error: {exc}") from exc

    latency_ms = int((time.perf_counter() - started) * 1000)
    if response.status_code == 429:
        raise RateLimitError(response.text[:500])
    if response.status_code >= 400:
        raise RuntimeError(f"LLM provider HTTP {response.status_code}: {response.text[:500]}")
    data = response.json()
    if not isinstance(data, dict):
        raise RuntimeError("LLM provider returned non-object JSON")
    return data, latency_ms


def openai_compatible_response(
    *,
    provider: LLMProviderName,
    model: str,
    data: dict[str, Any],
    latency_ms: int,
    request_id: str | None = None,
    cost_in: float = 0.5,
    cost_out: float = 1.5,
) -> LLMCompletionResponse:
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("LLM provider returned no choices")
    message = choices[0].get("message") or {}
    content = message.get("content") or ""
    if isinstance(content, list):
        content = "".join(
            part.get("text", "") if isinstance(part, dict) else str(part) for part in content
        )
    usage_raw = data.get("usage") or {}
    prompt_tokens = int(usage_raw.get("prompt_tokens") or usage_raw.get("input_tokens") or 0)
    completion_tokens = int(usage_raw.get("completion_tokens") or usage_raw.get("output_tokens") or 0)
    return LLMCompletionResponse(
        provider=provider,
        model=model,
        content=str(content),
        structured_summary={"finish_reason": choices[0].get("finish_reason")},
        usage=TokenUsage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens),
        cost_usd_micros=estimate_cost_usd_micros(
            prompt_tokens, completion_tokens, per_mtok_in=cost_in, per_mtok_out=cost_out
        ),
        latency_ms=latency_ms,
        request_id=request_id or data.get("id"),
    )


def require_api_key(api_key: str | None, env_name: str) -> str:
    if not api_key:
        raise RuntimeError(f"{env_name} is not configured")
    return api_key


def default_model(request: LLMCompletionRequest, fallback: str) -> str:
    return (request.model or fallback).strip() or fallback


__all__ = [
    "default_model",
    "estimate_cost_usd_micros",
    "openai_compatible_response",
    "post_json",
    "require_api_key",
]
