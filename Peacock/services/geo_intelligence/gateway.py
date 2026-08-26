"""Peacock AI Gateway — broadcasts one prompt to every selected AI plugin.

This module is the ONLY place that fans a single research/search-intent prompt
out to multiple LLM plugins at once. It never talks to a provider SDK directly:
every call goes through ``llm_gateway.LLMGateway``, whose adapters are the
plugins (OpenAI/ChatGPT, Anthropic/Claude, Gemini, Perplexity, DeepSeek) and are
only ever constructed from environment-variable API keys
(``llm_gateway.factory.build_gateway_from_settings``). Adding, removing, or
swapping a plugin never requires touching this file or the GEO Intelligence
Layer that consumes its output — plugins register themselves with the gateway
by provider name.

If a plugin has no API key configured, the gateway falls back to a clearly
labelled ``simulated=True`` response instead of crashing or pretending a real
call happened, so the dashboard stays usable in local development with zero
credentials configured.
"""

from __future__ import annotations

import asyncio

from llm_gateway.ports import LLMCompletionRequest, LLMProviderName
from llm_gateway.registry import LLMGateway
from observability.logging import get_logger

from geo_intelligence.models import ProviderResponse

# engine_code (product-facing platform identity) -> (display name, llm_gateway provider code).
# This is the single place that names the five supported AI plugins; the gateway and GEO
# Intelligence Layer are otherwise provider-agnostic and read this table, not a hardcoded branch.
ENGINE_META: dict[str, dict[str, str]] = {
    "chatgpt": {"name": "ChatGPT", "provider": "openai"},
    "gemini": {"name": "Gemini", "provider": "gemini"},
    "claude": {"name": "Claude", "provider": "anthropic"},
    "perplexity": {"name": "Perplexity", "provider": "perplexity"},
    "deepseek": {"name": "DeepSeek", "provider": "deepseek"},
}

DEFAULT_ENGINE_CODES: tuple[str, ...] = tuple(ENGINE_META.keys())

_log = get_logger("geo_intelligence.gateway")


class PeacockAIGateway:
    """Central gateway: one prompt in, one response per selected AI plugin out."""

    def __init__(self, llm_gateway: LLMGateway | None = None) -> None:
        self._llm_gateway = llm_gateway

    def available_engine_codes(self) -> set[str]:
        """Engine codes whose plugin currently has a live adapter registered."""
        if self._llm_gateway is None:
            return set()
        live = {str(p) for p in self._llm_gateway._providers.keys() if p != LLMProviderName.NULL}
        return {code for code, meta in ENGINE_META.items() if meta["provider"] in live}

    async def broadcast(
        self,
        *,
        organisation_id: str,
        research_prompt: str,
        engine_codes: list[str] | None = None,
        role: str = "GEO_RESEARCH",
        template_id: str = "geo_intelligence.research_prompt",
        workspace_id: str | None = None,
        simulated_responses: dict[str, str] | None = None,
    ) -> list[ProviderResponse]:
        """Send ``research_prompt`` to every requested plugin in parallel.

        Unknown engine codes are ignored. Plugins without a configured API key
        return a ``simulated=True`` response built from ``simulated_responses``
        (or an empty string) — never a fabricated "live" answer.
        """
        codes = [c for c in (engine_codes or list(DEFAULT_ENGINE_CODES)) if c in ENGINE_META]
        available = self.available_engine_codes()
        simulated_responses = simulated_responses or {}

        async def _call_one(engine_code: str) -> ProviderResponse:
            meta = ENGINE_META[engine_code]
            provider_code = meta["provider"]
            if self._llm_gateway is not None and engine_code in available:
                try:
                    response = await self._llm_gateway.complete(
                        LLMCompletionRequest(
                            organisation_id=organisation_id,
                            workspace_id=workspace_id,
                            role=role,
                            template_id=template_id,
                            messages=[{"role": "user", "content": research_prompt}],
                            provider=provider_code,
                            metadata={"engine_code": engine_code},
                        )
                    )
                    return ProviderResponse(
                        engine_code=engine_code,
                        engine_name=meta["name"],
                        provider_code=provider_code,
                        content=response.content,
                        simulated=False,
                        model=response.model,
                        latency_ms=response.latency_ms,
                        error=None,
                    )
                except Exception as exc:  # a single plugin failure must never break the broadcast
                    _log.warning("geo_intelligence_provider_failed", engine_code=engine_code, error=str(exc))
                    return ProviderResponse(
                        engine_code=engine_code,
                        engine_name=meta["name"],
                        provider_code=provider_code,
                        content=simulated_responses.get(engine_code, ""),
                        simulated=True,
                        model=None,
                        latency_ms=0,
                        error=str(exc),
                    )
            return ProviderResponse(
                engine_code=engine_code,
                engine_name=meta["name"],
                provider_code=provider_code,
                content=simulated_responses.get(engine_code, ""),
                simulated=True,
                model=None,
                latency_ms=0,
                error=None,
            )

        return list(await asyncio.gather(*(_call_one(code) for code in codes)))
