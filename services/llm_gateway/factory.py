"""Build LLMGateway from settings — register live adapters when keys present."""

from __future__ import annotations

from typing import Any

from llm_gateway.adapters.anthropic_adapter import AnthropicAdapter
from llm_gateway.adapters.deepseek_adapter import DeepSeekAdapter
from llm_gateway.adapters.gemini_adapter import GeminiAdapter
from llm_gateway.adapters.null_provider import NullLLMProvider
from llm_gateway.adapters.openai_adapter import OpenAIAdapter
from llm_gateway.adapters.perplexity_adapter import PerplexityAdapter
from llm_gateway.ports import LLMProvider, LLMProviderName
from llm_gateway.registry import LLMGateway


def build_providers_from_settings(settings: Any) -> dict[LLMProviderName, LLMProvider]:
    providers: dict[LLMProviderName, LLMProvider] = {
        LLMProviderName.NULL: NullLLMProvider(),
    }
    if getattr(settings, "openai_api_key", ""):
        providers[LLMProviderName.OPENAI] = OpenAIAdapter(api_key=settings.openai_api_key)
    if getattr(settings, "anthropic_api_key", ""):
        providers[LLMProviderName.ANTHROPIC] = AnthropicAdapter(api_key=settings.anthropic_api_key)
    if getattr(settings, "gemini_api_key", ""):
        providers[LLMProviderName.GEMINI] = GeminiAdapter(api_key=settings.gemini_api_key)
    if getattr(settings, "perplexity_api_key", ""):
        providers[LLMProviderName.PERPLEXITY] = PerplexityAdapter(api_key=settings.perplexity_api_key)
    if getattr(settings, "deepseek_api_key", ""):
        providers[LLMProviderName.DEEPSEEK] = DeepSeekAdapter(api_key=settings.deepseek_api_key)
    return providers


def soft_role_routing(providers: dict[LLMProviderName, LLMProvider]) -> dict[str, LLMProviderName]:
    """Soft defaults — CapabilityRouter should override per request."""
    prefer = [
        LLMProviderName.OPENAI,
        LLMProviderName.ANTHROPIC,
        LLMProviderName.GEMINI,
        LLMProviderName.PERPLEXITY,
        LLMProviderName.DEEPSEEK,
        LLMProviderName.NULL,
    ]
    default = next((p for p in prefer if p in providers), LLMProviderName.NULL)
    research = (
        LLMProviderName.PERPLEXITY
        if LLMProviderName.PERPLEXITY in providers
        else default
    )
    adversarial = (
        LLMProviderName.ANTHROPIC
        if LLMProviderName.ANTHROPIC in providers
        else default
    )
    return {
        "WEB_RESEARCH": research,
        "SYNTHESIS": default,
        "VERIFY_ADVERSARIAL": adversarial,
        "VISIBILITY_PROBE": default,
    }


def build_gateway_from_settings(settings: Any) -> LLMGateway:
    providers = build_providers_from_settings(settings)
    return LLMGateway(
        providers=providers,
        role_routing=soft_role_routing(providers),
        max_retries=getattr(settings, "llm_max_retries", 3),
        default_timeout_seconds=getattr(settings, "llm_default_timeout_seconds", 60.0),
    )


def live_provider_codes(gateway: LLMGateway) -> list[str]:
    return sorted(
        str(name) for name in gateway._providers.keys() if name != LLMProviderName.NULL
    )
