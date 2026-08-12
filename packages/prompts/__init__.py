"""Role-bound prompt templates — provider-agnostic."""

from prompts.intelligence_templates import LAYER_PROMPTS, build_intelligence_prompt_registry
from prompts.registry import PromptRegistry, PromptTemplate

__all__ = [
    "LAYER_PROMPTS",
    "PromptRegistry",
    "PromptTemplate",
    "build_intelligence_prompt_registry",
]
