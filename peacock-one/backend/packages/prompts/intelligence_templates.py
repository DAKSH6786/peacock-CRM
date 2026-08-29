from __future__ import annotations

from dataclasses import dataclass

from prompts.registry import PromptRegistry, PromptTemplate


LAYER_PROMPTS: tuple[PromptTemplate, ...] = (
    PromptTemplate(
        template_id="intel.layer0.classify",
        role="SYNTHESIS",
        system="Classify strategic requests. Return structured intent fields only — no private chain-of-thought.",
        user="Request: {{request_text}}",
    ),
    PromptTemplate(
        template_id="intel.layer4.specialist",
        role="SYNTHESIS",
        system=(
            "You are a specialist strategist. Use provided deterministic evidence. "
            "Do not invent numeric scores. Separate speculation from facts."
        ),
        user="Intent={{intent}}\nEvidence={{evidence}}\nContext={{context}}",
    ),
    PromptTemplate(
        template_id="intel.layer5.adversarial",
        role="VERIFY_ADVERSARIAL",
        system="Challenge weak or unsupported claims. Prefer deterministic evidence over narrative.",
        user="Claims={{claims}}\nEvidence={{evidence}}",
    ),
    PromptTemplate(
        template_id="intel.layer3.research",
        role="WEB_RESEARCH",
        system="Gather fresh external evidence. Summarise sources; do not fabricate citations.",
        user="Query={{query}}",
    ),
)


def build_intelligence_prompt_registry() -> PromptRegistry:
    return PromptRegistry(list(LAYER_PROMPTS))


@dataclass(frozen=True, slots=True)
class _PromptSeed:
    count: int = len(LAYER_PROMPTS)
