"""Gemini plugin — one of Peacock One's independent AI connectors.

Implements the shared ``llm_gateway.ports.LLMProvider`` interface. Credentials
come only from the ``GEMINI_API_KEY`` (or ``GOOGLE_API_KEY``) environment
variable — never hardcoded here.
"""

from llm_gateway.adapters.gemini_adapter import GeminiAdapter

__all__ = ["GeminiAdapter"]
