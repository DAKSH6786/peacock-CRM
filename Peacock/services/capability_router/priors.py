"""Soft capability priors — defaults only, never permanent routing locks.

PINE must dynamically route from observed ``ModelCapabilityProfile`` data.
These priors only fill gaps when sample sizes are too small.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SoftCapabilityPrior:
    provider_code: str
    model_code: str
    task_type: str
    quality_score: float
    latency_ms: float
    cost_usd_micros: int
    failure_rate: float
    json_compliance_rate: float
    citation_accuracy: float
    historical_agreement: float
    prior_weight: float = 1.0
    notes: str = ""


# Soft starters only. Observed profiles override these.
SOFT_CAPABILITY_PRIORS: tuple[SoftCapabilityPrior, ...] = (
    # Perplexity — strong research prior, not a permanent assignment
    SoftCapabilityPrior(
        "perplexity",
        "sonar",
        "RESEARCH",
        0.78,
        2500,
        1500,
        0.08,
        0.65,
        0.8,
        0.55,
        notes="Soft prior: web-grounded research",
    ),
    SoftCapabilityPrior(
        "perplexity",
        "sonar",
        "CITATION_EXTRACTION",
        0.75,
        2200,
        1400,
        0.1,
        0.7,
        0.82,
        0.55,
        notes="Soft prior: citation-heavy answers",
    ),
    SoftCapabilityPrior(
        "perplexity",
        "sonar",
        "FACT_VERIFICATION",
        0.7,
        2400,
        1500,
        0.1,
        0.68,
        0.75,
        0.5,
    ),
    # Anthropic / Claude — critical analysis prior, not locked to critic
    SoftCapabilityPrior(
        "anthropic",
        "claude-sonnet",
        "CRITICAL_ANALYSIS",
        0.82,
        2800,
        2500,
        0.06,
        0.85,
        0.6,
        0.7,
        notes="Soft prior: adversarial / critical analysis",
    ),
    SoftCapabilityPrior(
        "anthropic",
        "claude-sonnet",
        "FACT_VERIFICATION",
        0.8,
        2600,
        2400,
        0.07,
        0.86,
        0.65,
        0.72,
    ),
    SoftCapabilityPrior(
        "anthropic",
        "claude-sonnet",
        "STRATEGY",
        0.76,
        3000,
        2600,
        0.08,
        0.84,
        0.55,
        0.68,
    ),
    SoftCapabilityPrior(
        "anthropic",
        "claude-sonnet",
        "LONG_CONTEXT_ANALYSIS",
        0.8,
        3500,
        3200,
        0.07,
        0.83,
        0.55,
        0.7,
    ),
    # OpenAI / GPT — strategy & structured output prior, not locked
    SoftCapabilityPrior(
        "openai",
        "gpt-4.1",
        "STRATEGY",
        0.8,
        2200,
        2800,
        0.07,
        0.9,
        0.55,
        0.7,
        notes="Soft prior: strategy synthesis",
    ),
    SoftCapabilityPrior(
        "openai",
        "gpt-4.1",
        "STRUCTURED_OUTPUT",
        0.85,
        2000,
        2600,
        0.05,
        0.95,
        0.5,
        0.72,
    ),
    SoftCapabilityPrior(
        "openai",
        "gpt-4.1",
        "SEO_REASONING",
        0.74,
        2100,
        2500,
        0.08,
        0.88,
        0.55,
        0.65,
    ),
    SoftCapabilityPrior(
        "openai",
        "gpt-4.1",
        "SUMMARISATION",
        0.78,
        1800,
        2200,
        0.06,
        0.9,
        0.5,
        0.68,
    ),
    # Gemini — long-context / summarisation prior
    SoftCapabilityPrior(
        "gemini",
        "gemini-2.0-flash",
        "LONG_CONTEXT_ANALYSIS",
        0.8,
        1800,
        900,
        0.08,
        0.82,
        0.5,
        0.65,
        notes="Soft prior: long-context analysis",
    ),
    SoftCapabilityPrior(
        "gemini",
        "gemini-2.0-flash",
        "SUMMARISATION",
        0.76,
        1600,
        800,
        0.08,
        0.84,
        0.5,
        0.64,
    ),
    SoftCapabilityPrior(
        "gemini",
        "gemini-2.0-flash",
        "ENTITY_EXTRACTION",
        0.74,
        1500,
        750,
        0.09,
        0.86,
        0.55,
        0.6,
    ),
    SoftCapabilityPrior(
        "gemini",
        "gemini-2.0-flash",
        "GEO_REASONING",
        0.72,
        1700,
        850,
        0.09,
        0.8,
        0.58,
        0.6,
    ),
    # DeepSeek — cost-efficient content / competitor analysis prior
    SoftCapabilityPrior(
        "deepseek",
        "deepseek-chat",
        "CONTENT_ANALYSIS",
        0.72,
        1900,
        400,
        0.1,
        0.8,
        0.45,
        0.58,
        notes="Soft prior: cost-efficient content analysis",
    ),
    SoftCapabilityPrior(
        "deepseek",
        "deepseek-chat",
        "COMPETITOR_ANALYSIS",
        0.7,
        2000,
        450,
        0.1,
        0.78,
        0.5,
        0.55,
    ),
    SoftCapabilityPrior(
        "deepseek",
        "deepseek-chat",
        "SEO_REASONING",
        0.68,
        1900,
        420,
        0.11,
        0.8,
        0.45,
        0.55,
    ),
)


# Soft mapping from gateway roles → capability task types (not provider locks)
GATEWAY_ROLE_TASK_DEFAULTS: dict[str, str] = {
    "WEB_RESEARCH": "RESEARCH",
    "SYNTHESIS": "STRATEGY",
    "VERIFY_ADVERSARIAL": "CRITICAL_ANALYSIS",
    "VISIBILITY_PROBE": "GEO_REASONING",
}
