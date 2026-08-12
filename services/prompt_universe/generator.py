"""Deterministic Prompt Universe expansion from source signals.

Generates prompt families across the taxonomy and materialises both
simple discovery prompts and persona-contextual variants.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from prompt_universe.personas import PersonaCatalogEntry, SYNTHETIC_PERSONA_CATALOG
from prompt_universe.taxonomy import (
    commercial_value_for_type,
    funnel_for_type,
    intent_for_type,
)


def prompt_hash(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


def slugify(text: str, max_len: int = 140) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return (s or "family")[:max_len]


@dataclass(frozen=True)
class GeneratedPrompt:
    prompt_text: str
    topic: str
    subtopic: str | None
    intent: str
    persona_code: str
    funnel_stage: str
    location: str
    product: str | None
    problem: str | None
    commercial_value: float
    brand_relevance: float
    prompt_type: str
    source_kind: str
    complexity: str  # simple | contextual
    family_slug: str
    family_name: str
    family_topic: str
    priority: str


# Core types always expanded for product/keyword/service-like signals
_CORE_TYPES: tuple[str, ...] = (
    "discovery",
    "recommendation",
    "comparison",
    "pricing",
    "alternative",
    "trust",
    "technical",
    "purchase",
)

# Extra types for problem / PAA / forum style signals
_PROBLEM_TYPES: tuple[str, ...] = (
    "problem_solving",
    "research",
    "educational",
    "validation",
    "risk",
)

# Commercial / transactional boosters
_COMMERCIAL_TYPES: tuple[str, ...] = (
    "transactional",
    "purchase",
    "pricing",
)


def _subject(signal_text: str, product_name: str | None) -> str:
    return (product_name or signal_text).strip()


def _brand_relevance(source_kind: str, weight: float) -> float:
    base = {
        "product": 0.90,
        "service": 0.88,
        "keyword": 0.70,
        "search_console_query": 0.85,
        "competitor_ranking": 0.75,
        "forum": 0.55,
        "serp": 0.65,
        "people_also_ask": 0.60,
        "customer_persona": 0.50,
        "funnel_stage": 0.40,
        "location": 0.45,
        "industry_concept": 0.60,
        "ai_query_pattern": 0.80,
        "prompt_taxonomy": 0.50,
        "manual": 0.70,
    }.get(source_kind, 0.55)
    return max(0.0, min(1.0, base * (0.75 + 0.25 * max(0.0, min(weight, 2.0)))))


def _priority(commercial_value: float, brand_relevance: float) -> str:
    score = 0.6 * commercial_value + 0.4 * brand_relevance
    if score >= 0.75:
        return "high"
    if score >= 0.45:
        return "medium"
    return "low"


def _simple_templates(prompt_type: str, subject: str, brand: str, location: str) -> str:
    loc = "" if location in {"global", "", "worldwide"} else f" in {location.upper()}"
    templates = {
        "discovery": f"what is {subject}{loc}",
        "recommendation": f"best {subject}{loc}",
        "comparison": f"{subject} vs alternatives{loc}",
        "problem_solving": f"how to solve {subject} problems{loc}",
        "purchase": f"buy {subject}{loc}",
        "research": f"{subject} overview and key considerations{loc}",
        "validation": f"is {brand} a good {subject}{loc}",
        "alternative": f"alternatives to {subject}{loc}",
        "pricing": f"{subject} pricing{loc}",
        "trust": f"is {subject} trustworthy{loc}",
        "risk": f"risks of choosing {subject}{loc}",
        "technical": f"{subject} technical requirements and integrations{loc}",
        "educational": f"explain {subject} for beginners{loc}",
        "transactional": f"get a demo of {subject}{loc}",
    }
    return templates[prompt_type]


def _contextual_template(
    prompt_type: str,
    subject: str,
    brand: str,
    location: str,
    persona: PersonaCatalogEntry,
    industry: str | None,
    problem: str | None,
) -> str:
    loc_clause = (
        f" Prefer vendors with presence or data residency suitable for {location.upper()}."
        if location not in {"global", "", "worldwide"}
        else ""
    )
    industry_clause = f" Industry context: {industry}." if industry else ""
    problem_clause = f" Core problem: {problem}." if problem else ""
    base_context = (
        f"{persona.context_template}{industry_clause}{problem_clause}{loc_clause}"
    ).strip()

    asks = {
        "discovery": f"Explain what {subject} is and when organisations should use it.",
        "recommendation": f"Which {subject} platforms should we shortlist and why?",
        "comparison": f"Compare leading {subject} options against each other and against {brand}.",
        "problem_solving": f"How should we approach solving {problem or subject} with the right platform?",
        "purchase": f"What is the recommended buying process and shortlist for {subject}?",
        "research": f"Provide a structured research brief on {subject} for our evaluation committee.",
        "validation": f"Validate whether {brand} belongs on a serious shortlist for {subject}.",
        "alternative": f"What credible alternatives to {subject} / {brand} should we evaluate?",
        "pricing": f"How should we compare pricing models and TCO for {subject} vendors?",
        "trust": f"Which trust, security, and reputation signals matter most when choosing {subject}?",
        "risk": f"What are the main risks of selecting the wrong {subject} vendor, and how do we mitigate them?",
        "technical": f"What technical evaluation criteria should we use for {subject} platforms?",
        "educational": f"Educate our stakeholders on {subject} fundamentals before vendor demos.",
        "transactional": f"What next steps and proof points should we request before purchasing {subject}?",
    }
    return f"{base_context}\n\n{asks[prompt_type]}"


def _types_for_source(source_kind: str) -> tuple[str, ...]:
    if source_kind in {"people_also_ask", "forum", "problem"}:
        return tuple(dict.fromkeys(_CORE_TYPES + _PROBLEM_TYPES))
    if source_kind in {"search_console_query", "ai_query_pattern", "keyword", "serp"}:
        return tuple(dict.fromkeys(_CORE_TYPES + ("research", "educational", "validation")))
    if source_kind in {"competitor_ranking", "product", "service"}:
        return tuple(dict.fromkeys(_CORE_TYPES + _COMMERCIAL_TYPES + ("validation", "risk")))
    if source_kind == "prompt_taxonomy":
        return ("discovery", "recommendation", "comparison", "educational")
    return _CORE_TYPES


@dataclass
class ExpansionResult:
    prompts: list[GeneratedPrompt]


def expand_signal(
    *,
    signal_text: str,
    source_kind: str,
    brand_name: str,
    industry: str | None = None,
    location: str = "global",
    product_name: str | None = None,
    topic_hint: str | None = None,
    weight: float = 1.0,
    personas: list[PersonaCatalogEntry] | None = None,
    include_persona_variants: bool = True,
) -> ExpansionResult:
    subject = _subject(signal_text, product_name)
    topic = (topic_hint or subject).strip()
    family_name = f"{topic} intent family"
    family_slug = slugify(f"{source_kind}-{topic}")
    problem = signal_text if source_kind in {"people_also_ask", "forum"} else None
    brand_rel = _brand_relevance(source_kind, weight)
    personas = personas or []

    out: list[GeneratedPrompt] = []
    for prompt_type in _types_for_source(source_kind):
        simple_text = _simple_templates(prompt_type, subject, brand_name, location)
        cv = commercial_value_for_type(prompt_type, weight)
        out.append(
            GeneratedPrompt(
                prompt_text=simple_text,
                topic=topic,
                subtopic=prompt_type.replace("_", " "),
                intent=intent_for_type(prompt_type),
                persona_code="general",
                funnel_stage=funnel_for_type(prompt_type),
                location=location,
                product=product_name or (subject if source_kind in {"product", "service"} else None),
                problem=problem,
                commercial_value=cv,
                brand_relevance=brand_rel,
                prompt_type=prompt_type,
                source_kind=source_kind,
                complexity="simple",
                family_slug=family_slug,
                family_name=family_name,
                family_topic=topic,
                priority=_priority(cv, brand_rel),
            )
        )

        if not include_persona_variants or not personas:
            continue

        # Persona variants: track both short and long (contextual) prompts
        for persona in personas:
            # Skip some low-fit combinations to keep landscape useful, not noisy
            if prompt_type in {"educational", "discovery"} and persona.code in {
                "hnwi",
                "cfo",
            }:
                # still include recommendation/pricing/etc.
                if prompt_type == "educational":
                    continue

            contextual = _contextual_template(
                prompt_type=prompt_type,
                subject=subject,
                brand=brand_name,
                location=location,
                persona=persona,
                industry=industry,
                problem=problem,
            )
            # Slight commercial bump for enterprise-like personas on commercial types
            persona_cv = cv
            if persona.code in {"cfo", "enterprise_buyer", "technical_evaluator"} and prompt_type in {
                "purchase",
                "pricing",
                "comparison",
                "recommendation",
            }:
                persona_cv = min(1.0, cv + 0.08)

            out.append(
                GeneratedPrompt(
                    prompt_text=contextual,
                    topic=topic,
                    subtopic=f"{prompt_type.replace('_', ' ')} · {persona.name}",
                    intent=intent_for_type(prompt_type),
                    persona_code=persona.code,
                    funnel_stage=funnel_for_type(prompt_type),
                    location=location,
                    product=product_name or (subject if source_kind in {"product", "service"} else None),
                    problem=problem,
                    commercial_value=persona_cv,
                    brand_relevance=brand_rel,
                    prompt_type=prompt_type,
                    source_kind=source_kind,
                    complexity="contextual",
                    family_slug=family_slug,
                    family_name=family_name,
                    family_topic=topic,
                    priority=_priority(persona_cv, brand_rel),
                )
            )

    return ExpansionResult(prompts=out)


def default_personas_for_codes(codes: list[str] | None) -> list[PersonaCatalogEntry]:
    if codes is None:
        return list(SYNTHETIC_PERSONA_CATALOG.values())
    out: list[PersonaCatalogEntry] = []
    for code in codes:
        entry = SYNTHETIC_PERSONA_CATALOG.get(code.lower().strip())
        if entry is None:
            raise ValueError(f"Unknown synthetic persona code: {code}")
        out.append(entry)
    return out
