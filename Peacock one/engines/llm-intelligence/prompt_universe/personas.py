"""Synthetic analytical personas for Prompt Universe Intelligence.

These are query lenses (CFO, developer, …), not fabricated real identities.
"""

from __future__ import annotations

from dataclasses import dataclass

from db_models.prompt_universe import SYNTHETIC_PERSONA_SEEDS


@dataclass(frozen=True)
class PersonaCatalogEntry:
    code: str
    name: str
    description: str
    query_style: str
    # Context fragment injected into long-form prompts
    context_template: str


def _build_catalog() -> dict[str, PersonaCatalogEntry]:
    templates = {
        "cfo": (
            "We are evaluating vendors with strict budget governance. "
            "Focus on total cost of ownership, ROI evidence, contractual risk, "
            "and financial controls."
        ),
        "cmo": (
            "We need options that improve pipeline quality and brand authority. "
            "Emphasise demand generation impact, attribution clarity, and channel fit."
        ),
        "student": (
            "I am learning this space and need clear, affordable recommendations "
            "with plain-language explanations."
        ),
        "enterprise_buyer": (
            "We are a large organisation running a formal shortlist process. "
            "Require enterprise readiness, security posture, SLAs, and procurement fit."
        ),
        "technical_evaluator": (
            "I am assessing architecture, APIs, data residency, integrations, "
            "and operational maintainability in detail."
        ),
        "hnwi": (
            "I want premium, highly trusted options with white-glove support "
            "and proven outcomes for sophisticated buyers."
        ),
        "small_business_owner": (
            "I run a small business and need something practical, affordable, "
            "and quick to implement without a large team."
        ),
        "developer": (
            "I care about API quality, documentation, extensibility, and "
            "engineering time-to-integrate."
        ),
        "parent": (
            "I need safe, clear, and reliable recommendations that are easy "
            "to understand for a household decision."
        ),
        "healthcare_professional": (
            "Recommendations must be compliance-aware, evidence-oriented, "
            "and suitable for regulated healthcare contexts."
        ),
    }
    out: dict[str, PersonaCatalogEntry] = {}
    for code, name, description, style in SYNTHETIC_PERSONA_SEEDS:
        out[code] = PersonaCatalogEntry(
            code=code,
            name=name,
            description=description,
            query_style=style,
            context_template=templates[code],
        )
    return out


SYNTHETIC_PERSONA_CATALOG: dict[str, PersonaCatalogEntry] = _build_catalog()


def persona_by_code(code: str) -> PersonaCatalogEntry | None:
    return SYNTHETIC_PERSONA_CATALOG.get(code.lower().strip())
