"""OpenAI (ChatGPT) plugin — one of Peacock One's independent AI connectors.

Every AI plugin implements the same ``llm_gateway.ports.LLMProvider``
interface, so providers can be enabled, disabled, replaced, or added later
without changing the core application. Credentials come only from the
``OPENAI_API_KEY`` environment variable (see ``llm_gateway.factory``) — never
hardcoded here.
"""

from llm_gateway.adapters.openai_adapter import OpenAIAdapter

__all__ = ["OpenAIAdapter"]
