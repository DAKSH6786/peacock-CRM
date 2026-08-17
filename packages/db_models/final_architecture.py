"""Final Peacock Architecture — system map + product difference standard.

The completed system conceptually becomes:

  PEACOCK ONE
    → DATA OBSERVATION LAYER (Website, Search, AI, Competitors, Analytics)
    → EVIDENCE LEDGER
    → PINE (Specialists | LLM Fabric | Data Models)
    → PEACOCK COUNCIL → CRITIC → VERIFICATION → PEACOCK JUDGE
    → COUNTERFACTUAL SIMULATION → RECOMMENDATION ENGINE
    → PEACOCK ACTION ENGINE → EXECUTION → MONITORING → EXPERIMENTS
    → OUTCOME MEASUREMENT → PEACOCK LEARNING → (loop back) PINE

Fundamental product difference — do not only answer \"How visible are we?\"
Answer the full Peacock One standard question set (visibility, certainty, why,
competitors, sources, entities, intents, change, EV, owner, inaction, outcomes,
learning).
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

from db_models.base import Base, WorkspaceTenantMixin


PIPELINE_STAGES: tuple[str, ...] = (
    "peacock_one",
    "data_observation",
    "evidence_ledger",
    "pine",
    "peacock_council",
    "critic_layer",
    "verification_layer",
    "peacock_judge",
    "counterfactual_simulation",
    "recommendation_engine",
    "peacock_action_engine",
    "execution",
    "monitoring",
    "experiments",
    "outcome_measurement",
    "peacock_learning",
)

STAGE_LABELS: dict[str, str] = {
    "peacock_one": "Peacock One",
    "data_observation": "Data Observation Layer",
    "evidence_ledger": "Evidence Ledger",
    "pine": "PINE",
    "peacock_council": "Peacock Council",
    "critic_layer": "Critic Layer",
    "verification_layer": "Verification Layer",
    "peacock_judge": "Peacock Judge",
    "counterfactual_simulation": "Counterfactual Simulation",
    "recommendation_engine": "Recommendation Engine",
    "peacock_action_engine": "Peacock Action Engine",
    "execution": "Execution",
    "monitoring": "Monitoring",
    "experiments": "Experiments",
    "outcome_measurement": "Outcome Measurement",
    "peacock_learning": "Peacock Learning",
}

OBSERVATION_SOURCES: tuple[str, ...] = (
    "website",
    "search",
    "ai",
    "competitors",
    "analytics",
)

OBSERVATION_SOURCE_LABELS: dict[str, str] = {
    "website": "Website",
    "search": "Search",
    "ai": "AI",
    "competitors": "Competitors",
    "analytics": "Analytics",
}

PINE_FABRIC_LANES: tuple[str, ...] = (
    "specialists",
    "llm_fabric",
    "data_models",
)

PINE_FABRIC_LABELS: dict[str, str] = {
    "specialists": "Specialists",
    "llm_fabric": "LLM Fabric",
    "data_models": "Data Models",
}

# Ordered product-difference questions — the Peacock One standard
PRODUCT_QUESTIONS: tuple[str, ...] = (
    "how_visible",
    "how_certain",
    "why",
    "compared_with_whom",
    "which_sources",
    "which_entities",
    "which_intents_losing",
    "what_should_change",
    "highest_expected_value",
    "who_should_execute",
    "what_if_we_dont",
    "did_change_work",
    "what_did_peacock_learn",
)

PRODUCT_QUESTION_TEXT: dict[str, str] = {
    "how_visible": "How visible are we?",
    "how_certain": "How certain are we?",
    "why": "Why?",
    "compared_with_whom": "Compared with whom?",
    "which_sources": "Which sources are causing it?",
    "which_entities": "Which entities are influencing it?",
    "which_intents_losing": "Which customer intents are we losing?",
    "what_should_change": "What should we change?",
    "highest_expected_value": "Which action has the highest expected value?",
    "who_should_execute": "Who should execute it?",
    "what_if_we_dont": "What happens if we don't?",
    "did_change_work": "Did the change work?",
    "what_did_peacock_learn": "What did Peacock learn?",
}

# Anti-pattern: building only for visibility
NOT_ONLY_VISIBILITY = (
    'Do not build Peacock One to answer only: "How visible are we?"'
)

PRODUCT_STANDARD = (
    "That is the standard for Peacock One — visibility, certainty, why, "
    "competitors, sources, entities, intents, change, expected value, "
    "ownership, inaction risk, outcomes, and learning."
)

METHODOLOGY = "peacock_final_architecture_v1"
METHODOLOGY_NOTE = (
    "Final Peacock Architecture maps Observation → Evidence → PINE → Council → "
    "Critic → Verification → Judge → Simulation → Recommendations → Action → "
    "Execution → Monitoring → Experiments → Outcomes → Learning (back to PINE). "
    + PRODUCT_STANDARD
)
ARCHITECTURE_POSITIONING = (
    "Peacock One is a closed-loop generative visibility system — not a "
    "conventional SEO tool and not a mere AI-mention dashboard."
)

# Learning loops back to PINE
LEARNING_LOOPS_TO = "pine"


class FinalArchitectureMap(Base, WorkspaceTenantMixin):
    """One Final Peacock Architecture map / product-standard snapshot."""

    __tablename__ = "final_architecture_maps"

    website_id: Mapped[str] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_brand: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    stages_count: Mapped[int] = mapped_column(Integer, nullable=False)
    observation_sources_count: Mapped[int] = mapped_column(Integer, nullable=False)
    pine_lanes_count: Mapped[int] = mapped_column(Integer, nullable=False)
    product_questions_count: Mapped[int] = mapped_column(Integer, nullable=False)
    learning_loops_to_pine: Mapped[bool] = mapped_column(Boolean, nullable=False)
    not_only_visibility: Mapped[bool] = mapped_column(Boolean, nullable=False)
    product_standard_coverage: Mapped[float] = mapped_column(Float, nullable=False)
    architecture_diagram: Mapped[str] = mapped_column(Text, nullable=False)
    methodology: Mapped[str] = mapped_column(String(64), default=METHODOLOGY, nullable=False)
    architecture_positioning: Mapped[str] = mapped_column(Text, nullable=False)
    product_standard: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    analysed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    notes: Mapped[str | None] = mapped_column(Text)

    stages: Mapped[list[FaPipelineStage]] = relationship(
        back_populates="architecture_map",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    observation_sources: Mapped[list[FaObservationSource]] = relationship(
        back_populates="architecture_map",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    pine_lanes: Mapped[list[FaPineLane]] = relationship(
        back_populates="architecture_map",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    product_questions: Mapped[list[FaProductQuestion]] = relationship(
        back_populates="architecture_map",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class FaPipelineStage(Base, WorkspaceTenantMixin):
    """Ordered stage in the Final Peacock Architecture pipeline."""

    __tablename__ = "fa_pipeline_stages"
    __table_args__ = (UniqueConstraint("map_id", "stage_key"),)

    map_id: Mapped[str] = mapped_column(
        ForeignKey("final_architecture_maps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stage_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    stage_label: Mapped[str] = mapped_column(String(255), nullable=False)
    rank_order: Mapped[int] = mapped_column(Integer, nullable=False)
    next_stage_key: Mapped[str | None] = mapped_column(String(64))
    loops_to_stage_key: Mapped[str | None] = mapped_column(String(64))
    detail: Mapped[str] = mapped_column(Text, nullable=False)

    architecture_map: Mapped[FinalArchitectureMap] = relationship(back_populates="stages")


class FaObservationSource(Base, WorkspaceTenantMixin):
    """Data Observation Layer source."""

    __tablename__ = "fa_observation_sources"
    __table_args__ = (UniqueConstraint("map_id", "source_key"),)

    map_id: Mapped[str] = mapped_column(
        ForeignKey("final_architecture_maps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_label: Mapped[str] = mapped_column(String(255), nullable=False)
    feeds_evidence_ledger: Mapped[bool] = mapped_column(Boolean, nullable=False)
    rank_order: Mapped[int] = mapped_column(Integer, nullable=False)

    architecture_map: Mapped[FinalArchitectureMap] = relationship(
        back_populates="observation_sources"
    )


class FaPineLane(Base, WorkspaceTenantMixin):
    """PINE fabric lane: specialists / LLM fabric / data models."""

    __tablename__ = "fa_pine_lanes"
    __table_args__ = (UniqueConstraint("map_id", "lane_key"),)

    map_id: Mapped[str] = mapped_column(
        ForeignKey("final_architecture_maps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lane_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    lane_label: Mapped[str] = mapped_column(String(255), nullable=False)
    rank_order: Mapped[int] = mapped_column(Integer, nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False)

    architecture_map: Mapped[FinalArchitectureMap] = relationship(back_populates="pine_lanes")


class FaProductQuestion(Base, WorkspaceTenantMixin):
    """One Peacock One product-difference standard question."""

    __tablename__ = "fa_product_questions"
    __table_args__ = (UniqueConstraint("map_id", "question_key"),)

    map_id: Mapped[str] = mapped_column(
        ForeignKey("final_architecture_maps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    addressed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    primary_stage_key: Mapped[str | None] = mapped_column(String(64))
    rank_order: Mapped[int] = mapped_column(Integer, nullable=False)

    architecture_map: Mapped[FinalArchitectureMap] = relationship(
        back_populates="product_questions"
    )
