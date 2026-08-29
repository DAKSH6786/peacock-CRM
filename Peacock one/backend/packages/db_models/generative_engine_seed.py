"""Seed generative engines linked to AI providers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GenerativeEngineSeed:
    code: str
    name: str
    vendor: str
    provider_code: str | None


GENERATIVE_ENGINE_SEEDS: tuple[GenerativeEngineSeed, ...] = (
    GenerativeEngineSeed("chatgpt", "ChatGPT", "OpenAI", "openai"),
    GenerativeEngineSeed("gemini", "Gemini", "Google", "gemini"),
    GenerativeEngineSeed("claude", "Claude", "Anthropic", "anthropic"),
    GenerativeEngineSeed("perplexity", "Perplexity", "Perplexity", "perplexity"),
    GenerativeEngineSeed("deepseek", "DeepSeek", "DeepSeek", "deepseek"),
    GenerativeEngineSeed("google_ai_overview", "Google AI Overview", "Google", "gemini"),
)
