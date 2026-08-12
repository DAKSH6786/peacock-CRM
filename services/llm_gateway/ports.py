from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol

from observability.metrics import TokenUsage


class LLMProviderName(StrEnum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    PERPLEXITY = "perplexity"
    DEEPSEEK = "deepseek"
    NULL = "null"


@dataclass(slots=True)
class LLMCompletionRequest:
    """Provider-agnostic completion request.

    Business services pass role + template id; gateway maps to a provider adapter.
    Never embed provider SDKs in business modules.
    """

    organisation_id: str
    role: str
    template_id: str
    messages: list[dict[str, str]]
    model: str | None = None
    temperature: float = 0.2
    max_tokens: int = 2048
    timeout_seconds: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class LLMCompletionResponse:
    provider: LLMProviderName
    model: str
    content: str
    # Structured summary only — never private chain-of-thought
    structured_summary: dict[str, Any] = field(default_factory=dict)
    usage: TokenUsage = field(default_factory=TokenUsage)
    cost_usd_micros: int = 0
    latency_ms: int = 0
    request_id: str | None = None


class LLMProvider(Protocol):
    name: LLMProviderName

    async def complete(self, request: LLMCompletionRequest) -> LLMCompletionResponse: ...
