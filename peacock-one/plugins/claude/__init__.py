"""Claude (Anthropic) plugin — one of Peacock One's independent AI connectors.

Implements the shared ``llm_gateway.ports.LLMProvider`` interface. Credentials
come only from the ``ANTHROPIC_API_KEY`` environment variable — never
hardcoded here.
"""

from llm_gateway.adapters.anthropic_adapter import AnthropicAdapter

__all__ = ["AnthropicAdapter"]
