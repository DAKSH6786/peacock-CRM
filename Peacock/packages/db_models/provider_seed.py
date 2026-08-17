"""Canonical seed data for supported AI providers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProviderModelSeed:
    model_code: str
    display_name: str
    is_default: bool = False
    context_window_tokens: int | None = None
    sort_order: int = 100


@dataclass(frozen=True, slots=True)
class ProviderSeed:
    code: str
    name: str
    vendor: str
    supports_chat: bool = True
    supports_embeddings: bool = False
    supports_web_grounding: bool = False
    documentation_url: str | None = None
    notes: str | None = None
    models: tuple[ProviderModelSeed, ...] = ()


SUPPORTED_AI_PROVIDERS: tuple[ProviderSeed, ...] = (
    ProviderSeed(
        code="openai",
        name="OpenAI",
        vendor="OpenAI",
        supports_chat=True,
        supports_embeddings=True,
        supports_web_grounding=False,
        documentation_url="https://platform.openai.com/docs",
        notes="ChatGPT / OpenAI API family",
        models=(
            ProviderModelSeed("gpt-4.1", "GPT-4.1", is_default=True, context_window_tokens=1_047_576, sort_order=10),
            ProviderModelSeed("gpt-4.1-mini", "GPT-4.1 Mini", context_window_tokens=1_047_576, sort_order=20),
            ProviderModelSeed("text-embedding-3-large", "Embedding 3 Large", context_window_tokens=8191, sort_order=90),
        ),
    ),
    ProviderSeed(
        code="gemini",
        name="Gemini",
        vendor="Google",
        supports_chat=True,
        supports_embeddings=True,
        supports_web_grounding=True,
        documentation_url="https://ai.google.dev/gemini-api/docs",
        notes="Google Gemini models",
        models=(
            ProviderModelSeed("gemini-2.5-pro", "Gemini 2.5 Pro", is_default=True, context_window_tokens=1_048_576, sort_order=10),
            ProviderModelSeed("gemini-2.5-flash", "Gemini 2.5 Flash", context_window_tokens=1_048_576, sort_order=20),
        ),
    ),
    ProviderSeed(
        code="anthropic",
        name="Claude",
        vendor="Anthropic",
        supports_chat=True,
        supports_embeddings=False,
        supports_web_grounding=False,
        documentation_url="https://docs.anthropic.com",
        notes="Anthropic Claude family",
        models=(
            ProviderModelSeed("claude-sonnet-4", "Claude Sonnet 4", is_default=True, context_window_tokens=200_000, sort_order=10),
            ProviderModelSeed("claude-opus-4", "Claude Opus 4", context_window_tokens=200_000, sort_order=20),
        ),
    ),
    ProviderSeed(
        code="perplexity",
        name="Perplexity",
        vendor="Perplexity",
        supports_chat=True,
        supports_embeddings=False,
        supports_web_grounding=True,
        documentation_url="https://docs.perplexity.ai",
        notes="Live web-grounded research models",
        models=(
            ProviderModelSeed("sonar-pro", "Sonar Pro", is_default=True, context_window_tokens=200_000, sort_order=10),
            ProviderModelSeed("sonar", "Sonar", context_window_tokens=128_000, sort_order=20),
        ),
    ),
    ProviderSeed(
        code="deepseek",
        name="DeepSeek",
        vendor="DeepSeek",
        supports_chat=True,
        supports_embeddings=False,
        supports_web_grounding=False,
        documentation_url="https://api-docs.deepseek.com",
        notes="DeepSeek chat / reasoner family",
        models=(
            ProviderModelSeed("deepseek-chat", "DeepSeek Chat", is_default=True, context_window_tokens=64_000, sort_order=10),
            ProviderModelSeed("deepseek-reasoner", "DeepSeek Reasoner", context_window_tokens=64_000, sort_order=20),
        ),
    ),
)

REQUIRED_PROVIDER_CODES = frozenset(p.code for p in SUPPORTED_AI_PROVIDERS)
