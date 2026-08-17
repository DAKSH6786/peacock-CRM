"""Prompt taxonomy helpers — types, intents, commercial scoring."""

from __future__ import annotations

from db_models.prompt_universe import FUNNEL_STAGES, PROMPT_TYPES

# Human labels for API/docs
PROMPT_TYPE_LABELS: dict[str, str] = {
    "discovery": "Discovery",
    "recommendation": "Recommendation",
    "comparison": "Comparison",
    "problem_solving": "Problem Solving",
    "purchase": "Purchase",
    "research": "Research",
    "validation": "Validation",
    "alternative": "Alternative",
    "pricing": "Pricing",
    "trust": "Trust",
    "risk": "Risk",
    "technical": "Technical",
    "educational": "Educational",
    "transactional": "Transactional",
}

# Default funnel stage per prompt type
TYPE_TO_FUNNEL: dict[str, str] = {
    "discovery": "awareness",
    "recommendation": "consideration",
    "comparison": "consideration",
    "problem_solving": "consideration",
    "purchase": "decision",
    "research": "awareness",
    "validation": "decision",
    "alternative": "consideration",
    "pricing": "decision",
    "trust": "decision",
    "risk": "decision",
    "technical": "consideration",
    "educational": "awareness",
    "transactional": "decision",
}

# Default search-intent label per prompt type
TYPE_TO_INTENT: dict[str, str] = {
    "discovery": "informational",
    "recommendation": "commercial",
    "comparison": "commercial",
    "problem_solving": "informational",
    "purchase": "transactional",
    "research": "informational",
    "validation": "commercial",
    "alternative": "commercial",
    "pricing": "commercial",
    "trust": "commercial",
    "risk": "commercial",
    "technical": "informational",
    "educational": "informational",
    "transactional": "transactional",
}

# Relative commercial value priors (0–1)
TYPE_COMMERCIAL_VALUE: dict[str, float] = {
    "discovery": 0.35,
    "recommendation": 0.75,
    "comparison": 0.80,
    "problem_solving": 0.55,
    "purchase": 0.95,
    "research": 0.40,
    "validation": 0.70,
    "alternative": 0.72,
    "pricing": 0.88,
    "trust": 0.65,
    "risk": 0.60,
    "technical": 0.58,
    "educational": 0.30,
    "transactional": 0.92,
}


def normalise_prompt_type(value: str) -> str:
    key = value.strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "problem_solving": "problem_solving",
        "problemsolving": "problem_solving",
        "problem": "problem_solving",
    }
    key = aliases.get(key, key)
    if key not in PROMPT_TYPES:
        raise ValueError(f"Unknown prompt_type: {value}")
    return key


def funnel_for_type(prompt_type: str) -> str:
    stage = TYPE_TO_FUNNEL[normalise_prompt_type(prompt_type)]
    assert stage in FUNNEL_STAGES
    return stage


def intent_for_type(prompt_type: str) -> str:
    return TYPE_TO_INTENT[normalise_prompt_type(prompt_type)]


def commercial_value_for_type(prompt_type: str, weight: float = 1.0) -> float:
    base = TYPE_COMMERCIAL_VALUE[normalise_prompt_type(prompt_type)]
    # Weight amplifies but stays in [0, 1]
    return max(0.0, min(1.0, base * (0.7 + 0.3 * max(0.0, min(weight, 2.0)))))
