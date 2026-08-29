"""DeepSeek plugin — one of Peacock One's independent AI connectors.

Implements the shared ``llm_gateway.ports.LLMProvider`` interface. Credentials
come only from the ``DEEPSEEK_API_KEY`` environment variable — never
hardcoded here.
"""

from llm_gateway.adapters.deepseek_adapter import DeepSeekAdapter

__all__ = ["DeepSeekAdapter"]
