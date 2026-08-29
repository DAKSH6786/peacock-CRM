"""Perplexity plugin — one of Peacock One's independent AI connectors.

Implements the shared ``llm_gateway.ports.LLMProvider`` interface. Credentials
come only from the ``PERPLEXITY_API_KEY`` environment variable — never
hardcoded here.
"""

from llm_gateway.adapters.perplexity_adapter import PerplexityAdapter

__all__ = ["PerplexityAdapter"]
