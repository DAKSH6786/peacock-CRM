"""Typed specs for Prompt Universe Intelligence."""

from __future__ import annotations

from dataclasses import dataclass, field

from db_models.prompt_universe import FUNNEL_STAGES, PROMPT_SOURCE_KINDS, PROMPT_TYPES

__all__ = [
    "FUNNEL_STAGES",
    "PROMPT_SOURCE_KINDS",
    "PROMPT_TYPES",
    "GenerateUniverseSpec",
    "SourceSignalSpec",
    "UniverseSummary",
]


@dataclass(frozen=True)
class SourceSignalSpec:
    source_kind: str
    signal_text: str
    weight: float = 1.0
    location_code: str | None = None
    product_name: str | None = None
    topic_hint: str | None = None
    external_ref: str | None = None


@dataclass
class GenerateUniverseSpec:
    website_id: str
    name: str
    brand_name: str
    industry: str | None = None
    primary_location: str = "global"
    description: str | None = None
    notes: str | None = None
    signals: list[SourceSignalSpec] = field(default_factory=list)
    persona_codes: list[str] | None = None
    include_persona_variants: bool = True
    max_prompts: int = 500


@dataclass(frozen=True)
class UniverseSummary:
    universe_id: str
    name: str
    brand_name: str
    generation_status: str
    prompt_count: int
    family_count: int
    signal_count: int
    persona_count: int
    prompt_type_counts: dict[str, int]
    simple_count: int
    contextual_count: int
