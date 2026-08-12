"""Prompt Universe Intelligence API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SourceSignalRequest(BaseModel):
    source_kind: str = Field(
        description="product|service|keyword|search_console_query|competitor_ranking|forum|serp|"
        "people_also_ask|customer_persona|funnel_stage|location|industry_concept|"
        "ai_query_pattern|prompt_taxonomy|manual"
    )
    signal_text: str = Field(min_length=1, max_length=4000)
    weight: float = Field(default=1.0, ge=0.0, le=5.0)
    location_code: str | None = Field(default=None, max_length=64)
    product_name: str | None = Field(default=None, max_length=255)
    topic_hint: str | None = Field(default=None, max_length=255)
    external_ref: str | None = Field(default=None, max_length=512)


class CreatePromptUniverseRequest(BaseModel):
    website_id: str
    workspace_id: str | None = None
    name: str = Field(min_length=2, max_length=255)
    brand_name: str = Field(min_length=1, max_length=255)
    industry: str | None = Field(default=None, max_length=128)
    primary_location: str = Field(default="global", max_length=64)
    description: str | None = None
    notes: str | None = None
    signals: list[SourceSignalRequest] = Field(min_length=1)
    persona_codes: list[str] | None = None
    include_persona_variants: bool = True
    max_prompts: int = Field(default=500, ge=1, le=5000)


class ExpandPromptUniverseRequest(BaseModel):
    signals: list[SourceSignalRequest] = Field(min_length=1)
    include_persona_variants: bool = True
    max_new_prompts: int = Field(default=200, ge=1, le=2000)


class UniverseSummaryResponse(BaseModel):
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
    tracks_both_simple_and_contextual: bool = True


class UniversePromptResponse(BaseModel):
    id: str
    prompt_text: str
    topic: str
    subtopic: str | None
    intent: str
    persona: str
    funnel_stage: str
    location: str
    product: str | None
    problem: str | None
    commercial_value: float
    brand_relevance: float
    prompt_type: str
    source_kind: str
    complexity: str
    is_tracked: bool
    priority: str
    family_id: str | None


class SyntheticPersonaResponse(BaseModel):
    code: str
    name: str
    description: str | None
    query_style: str
    is_system_seed: bool


class PromptUniverseCatalogResponse(BaseModel):
    prompt_types: list[str]
    source_kinds: list[str]
    funnel_stages: list[str]
    synthetic_personas: list[dict]
