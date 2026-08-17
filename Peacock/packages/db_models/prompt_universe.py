"""Prompt Universe Intelligence — complete intent landscape, not a fixed prompt set.

Competitors track manually configured 25/50/100 prompts. Peacock builds a
Prompt Universe from products, services, keywords, GSC, SERPs, personas,
funnel stages, locations, and taxonomy — then materialises both short and
persona-contextual prompts.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db_models.base import Base, WorkspaceTenantMixin, new_uuid


# Canonical prompt types (stored lowercase with underscores)
PROMPT_TYPES: tuple[str, ...] = (
    "discovery",
    "recommendation",
    "comparison",
    "problem_solving",
    "purchase",
    "research",
    "validation",
    "alternative",
    "pricing",
    "trust",
    "risk",
    "technical",
    "educational",
    "transactional",
)

# Sources used to grow the universe
PROMPT_SOURCE_KINDS: tuple[str, ...] = (
    "product",
    "service",
    "keyword",
    "search_console_query",
    "competitor_ranking",
    "forum",
    "serp",
    "people_also_ask",
    "customer_persona",
    "funnel_stage",
    "location",
    "industry_concept",
    "ai_query_pattern",
    "prompt_taxonomy",
    "manual",
)

FUNNEL_STAGES: tuple[str, ...] = (
    "awareness",
    "consideration",
    "decision",
    "retention",
    "advocacy",
)

# Analytical personas (not fake real identities)
SYNTHETIC_PERSONA_SEEDS: tuple[tuple[str, str, str, str], ...] = (
    ("cfo", "CFO", "Financial decision-maker focused on ROI, risk, and budget control.", "quantitative"),
    ("cmo", "CMO", "Marketing leader focused on brand, demand, and channel performance.", "strategic"),
    ("student", "Student", "Learner seeking accessible explanations and affordable options.", "exploratory"),
    ("enterprise_buyer", "Enterprise buyer", "Procurement-oriented buyer evaluating vendors at scale.", "rigorous"),
    (
        "technical_evaluator",
        "Technical evaluator",
        "Specialist assessing architecture, integrations, and operational fit.",
        "precise",
    ),
    ("hnwi", "HNWI", "High-net-worth individual seeking premium, trusted solutions.", "discerning"),
    (
        "small_business_owner",
        "Small business owner",
        "Owner-operator balancing cost, simplicity, and speed to value.",
        "pragmatic",
    ),
    ("developer", "Developer", "Builder focused on APIs, docs, DX, and technical constraints.", "technical"),
    ("parent", "Parent", "Household decision-maker prioritising safety, clarity, and value.", "cautious"),
    (
        "healthcare_professional",
        "Healthcare professional",
        "Clinical or care professional needing compliance-aware, evidence-based answers.",
        "careful",
    ),
)


class PromptUniverse(Base, WorkspaceTenantMixin):
    """Workspace-scoped container for the full intent landscape of a brand/site."""

    __tablename__ = "prompt_universes"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    brand_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    industry: Mapped[str | None] = mapped_column(String(128))
    primary_location: Mapped[str] = mapped_column(String(64), default="global", nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    generation_status: Mapped[str] = mapped_column(
        String(32), default="draft", nullable=False, index=True
    )
    prompt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    family_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    signal_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    signals: Mapped[list[PromptSourceSignal]] = relationship(
        back_populates="universe", cascade="all, delete-orphan", passive_deletes=True
    )
    families: Mapped[list[PromptFamily]] = relationship(
        back_populates="universe", cascade="all, delete-orphan", passive_deletes=True
    )
    prompts: Mapped[list[UniversePrompt]] = relationship(
        back_populates="universe", cascade="all, delete-orphan", passive_deletes=True
    )
    personas: Mapped[list[SyntheticPersona]] = relationship(
        back_populates="universe", cascade="all, delete-orphan", passive_deletes=True
    )
    generation_runs: Mapped[list[PromptGenerationRun]] = relationship(
        back_populates="universe", cascade="all, delete-orphan", passive_deletes=True
    )


class SyntheticPersona(Base, WorkspaceTenantMixin):
    """Analytical query persona — shapes prompt wording, not a fake identity."""

    __tablename__ = "synthetic_personas"
    __table_args__ = (UniqueConstraint("universe_id", "code"),)

    universe_id: Mapped[str] = mapped_column(
        ForeignKey("prompt_universes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    query_style: Mapped[str] = mapped_column(String(64), default="pragmatic", nullable=False)
    is_system_seed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    context_template: Mapped[str | None] = mapped_column(Text)

    universe: Mapped[PromptUniverse] = relationship(back_populates="personas")
    prompts: Mapped[list[UniversePrompt]] = relationship(back_populates="persona")


class PromptSourceSignal(Base, WorkspaceTenantMixin):
    """A seed signal used to expand the prompt universe."""

    __tablename__ = "prompt_source_signals"

    universe_id: Mapped[str] = mapped_column(
        ForeignKey("prompt_universes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_kind: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    signal_text: Mapped[str] = mapped_column(Text, nullable=False)
    signal_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    location_code: Mapped[str | None] = mapped_column(String(64))
    product_name: Mapped[str | None] = mapped_column(String(255))
    topic_hint: Mapped[str | None] = mapped_column(String(255))
    external_ref: Mapped[str | None] = mapped_column(String(512))

    universe: Mapped[PromptUniverse] = relationship(back_populates="signals")
    families: Mapped[list[PromptFamily]] = relationship(back_populates="seed_signal")


class PromptFamily(Base, WorkspaceTenantMixin):
    """A family of related prompts covering one intent cluster."""

    __tablename__ = "prompt_families"
    __table_args__ = (UniqueConstraint("universe_id", "slug"),)

    universe_id: Mapped[str] = mapped_column(
        ForeignKey("prompt_universes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    seed_signal_id: Mapped[str | None] = mapped_column(
        ForeignKey("prompt_source_signals.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(160), nullable=False)
    topic: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    summary: Mapped[str | None] = mapped_column(Text)
    member_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    universe: Mapped[PromptUniverse] = relationship(back_populates="families")
    seed_signal: Mapped[PromptSourceSignal | None] = relationship(back_populates="families")
    prompts: Mapped[list[UniversePrompt]] = relationship(back_populates="family")


class UniversePrompt(Base, WorkspaceTenantMixin):
    """A single prompt in the universe with full taxonomy attributes."""

    __tablename__ = "universe_prompts"
    __table_args__ = (UniqueConstraint("universe_id", "prompt_hash", "persona_code"),)

    universe_id: Mapped[str] = mapped_column(
        ForeignKey("prompt_universes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    family_id: Mapped[str | None] = mapped_column(
        ForeignKey("prompt_families.id", ondelete="SET NULL"), nullable=True, index=True
    )
    persona_id: Mapped[str | None] = mapped_column(
        ForeignKey("synthetic_personas.id", ondelete="SET NULL"), nullable=True, index=True
    )
    parent_prompt_id: Mapped[str | None] = mapped_column(
        ForeignKey("universe_prompts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    ai_query_id: Mapped[str | None] = mapped_column(
        ForeignKey("ai_queries.id", ondelete="SET NULL"), nullable=True, index=True
    )

    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    topic: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    subtopic: Mapped[str | None] = mapped_column(String(255))
    intent: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    persona_code: Mapped[str] = mapped_column(String(64), default="general", nullable=False, index=True)
    funnel_stage: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    location: Mapped[str] = mapped_column(String(64), default="global", nullable=False, index=True)
    product: Mapped[str | None] = mapped_column(String(255))
    problem: Mapped[str | None] = mapped_column(Text)
    commercial_value: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    brand_relevance: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    prompt_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    source_kind: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    complexity: Mapped[str] = mapped_column(
        String(32), default="simple", nullable=False, index=True
    )  # simple | contextual
    is_tracked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(16), default="medium", nullable=False)

    universe: Mapped[PromptUniverse] = relationship(back_populates="prompts")
    family: Mapped[PromptFamily | None] = relationship(back_populates="prompts")
    persona: Mapped[SyntheticPersona | None] = relationship(back_populates="prompts")


class PromptGenerationRun(Base, WorkspaceTenantMixin):
    """Audit trail for a Prompt Universe expansion run."""

    __tablename__ = "prompt_generation_runs"

    universe_id: Mapped[str] = mapped_column(
        ForeignKey("prompt_universes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    run_status: Mapped[str] = mapped_column(String(32), default="running", nullable=False, index=True)
    signals_consumed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    prompts_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    families_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    personas_materialised: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_summary: Mapped[str | None] = mapped_column(Text)

    universe: Mapped[PromptUniverse] = relationship(back_populates="generation_runs")
