from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from llm_gateway.ports import LLMCompletionRequest, LLMCompletionResponse, LLMProvider, LLMProviderName
from observability.logging import get_logger
from observability.metrics import CostRecord, UsageTracker

T = TypeVar("T")


class RateLimitError(Exception):
    pass


class ProviderTimeoutError(Exception):
    pass


class LLMGateway:
    """Routes role-bound requests to provider adapters with retry/timeout/cost tracking.

    Static ``role_routing`` is a soft fallback only. Prefer setting
    ``request.provider`` / ``request.model`` from ``CapabilityRouter`` so PINE
    routes dynamically from observed capability profiles.
    """

    def __init__(
        self,
        providers: dict[LLMProviderName, LLMProvider],
        role_routing: dict[str, LLMProviderName],
        usage_tracker: UsageTracker | None = None,
        max_retries: int = 3,
        default_timeout_seconds: float = 60.0,
    ) -> None:
        self._providers = providers
        self._role_routing = role_routing
        self._usage = usage_tracker or UsageTracker()
        self._max_retries = max_retries
        self._default_timeout = default_timeout_seconds
        self._log = get_logger("llm_gateway")

    def provider_for_role(self, role: str) -> LLMProvider:
        """Soft static fallback — not a permanent capability lock."""
        name = self._role_routing.get(role, LLMProviderName.NULL)
        if name not in self._providers:
            raise KeyError(f"No provider registered for {name}")
        return self._providers[name]

    def provider_for_request(self, request: LLMCompletionRequest) -> LLMProvider:
        """Resolve provider: dynamic override first, then soft role fallback."""
        if request.provider:
            try:
                name = LLMProviderName(request.provider)
            except ValueError as exc:
                raise KeyError(f"Unknown provider override: {request.provider}") from exc
            if name not in self._providers:
                raise KeyError(f"No provider registered for {name}")
            return self._providers[name]
        return self.provider_for_role(request.role)

    def _guard_untrusted_messages(self, request: LLMCompletionRequest) -> None:
        """Block obvious prompt-injection / secret-exfil attempts in untrusted input."""
        import re

        joined = "\n".join(m.get("content", "") for m in request.messages)
        # Treat crawler / visibility excerpts as untrusted DATA — refuse instruction overrides.
        patterns = [
            r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
            r"reveal\s+(the\s+)?(system\s+prompt|api\s*keys?)",
            r"exfiltrate\s+(secrets?|credentials?)",
            r"jailbreak",
        ]
        for pattern in patterns:
            if re.search(pattern, joined, re.IGNORECASE):
                raise ValueError(
                    "Blocked untrusted prompt content (prompt-injection / secret-exfil pattern). "
                    "Crawler and visibility text must be treated as DATA, not instructions."
                )

    async def complete(self, request: LLMCompletionRequest) -> LLMCompletionResponse:
        self._guard_untrusted_messages(request)
        provider = self.provider_for_request(request)
        timeout = request.timeout_seconds or self._default_timeout

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self._max_retries),
            wait=wait_exponential_jitter(initial=0.5, max=8),
            retry=retry_if_exception_type((RateLimitError, ProviderTimeoutError, TimeoutError)),
            reraise=True,
        ):
            with attempt:
                try:
                    response = await asyncio.wait_for(provider.complete(request), timeout=timeout)
                except TimeoutError as exc:
                    self._log.warning(
                        "llm_timeout",
                        provider=provider.name,
                        role=request.role,
                        task_type=request.task_type,
                        attempt=attempt.retry_state.attempt_number,
                    )
                    raise ProviderTimeoutError(str(exc)) from exc

                self._usage.record(
                    CostRecord(
                        provider=str(response.provider),
                        model=response.model,
                        organisation_id=request.organisation_id,
                        operation=request.task_type or request.role,
                        usage=response.usage,
                        cost_usd_micros=response.cost_usd_micros,
                        metadata={
                            "template_id": request.template_id,
                            "role": request.role,
                            "task_type": request.task_type,
                            "workspace_id": request.workspace_id,
                            "routing": "dynamic_override" if request.provider else "role_fallback",
                            # Never persist private CoT — structured summary only
                            "structured_summary_keys": list(response.structured_summary.keys()),
                        },
                    )
                )
                self._log.info(
                    "llm_completion",
                    provider=str(response.provider),
                    role=request.role,
                    task_type=request.task_type,
                    tokens=response.usage.total_tokens,
                    cost_usd_micros=response.cost_usd_micros,
                    organisation_id=request.organisation_id,
                    routing="dynamic_override" if request.provider else "role_fallback",
                )
                return response

        raise RuntimeError("unreachable")
