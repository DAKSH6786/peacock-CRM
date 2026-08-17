"""Final Peacock Architecture engine — system map + product standard."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

from db_models.final_architecture import (
    ARCHITECTURE_POSITIONING,
    LEARNING_LOOPS_TO,
    METHODOLOGY_NOTE,
    NOT_ONLY_VISIBILITY,
    OBSERVATION_SOURCE_LABELS,
    OBSERVATION_SOURCES,
    PINE_FABRIC_LABELS,
    PINE_FABRIC_LANES,
    PIPELINE_STAGES,
    PRODUCT_QUESTION_TEXT,
    PRODUCT_QUESTIONS,
    PRODUCT_STANDARD,
    STAGE_LABELS,
)


STAGE_DETAILS: dict[str, str] = {
    "peacock_one": "Product root — generative visibility closed loop.",
    "data_observation": "Observe website, search, AI, competitors, analytics.",
    "evidence_ledger": "Provenance-backed facts — never private CoT as evidence.",
    "pine": "Intelligence orchestrator — specialists, LLM fabric, data models.",
    "peacock_council": "Opposing-role debate for strategic decisions.",
    "critic_layer": "Adversarial critique of council / specialist claims.",
    "verification_layer": "Verify claims against evidence and observations.",
    "peacock_judge": "Deterministic multi-signal judgment.",
    "counterfactual_simulation": "What-if ranges before committing actions.",
    "recommendation_engine": "Ranked, evidence-backed recommendations.",
    "peacock_action_engine": "Approval-based connector execution.",
    "execution": "Carry out approved actions.",
    "monitoring": "Watch visibility and system health after execution.",
    "experiments": "Controlled lab / Research Mode measurements.",
    "outcome_measurement": "Did the change work? Measure deltas.",
    "peacock_learning": "Industry memory — feed outcomes back into PINE.",
}

PINE_LANE_DETAILS: dict[str, str] = {
    "specialists": "Domain engines (SEO, GEO, SoA, entity, citation, …).",
    "llm_fabric": "Capability-routed multi-model fabric via LLM gateway.",
    "data_models": "Proprietary metrics, moat pathways, graphs, twins.",
}

# Which pipeline stage primarily answers each product question
QUESTION_PRIMARY_STAGE: dict[str, str] = {
    "how_visible": "data_observation",
    "how_certain": "verification_layer",
    "why": "pine",
    "compared_with_whom": "data_observation",
    "which_sources": "evidence_ledger",
    "which_entities": "pine",
    "which_intents_losing": "pine",
    "what_should_change": "recommendation_engine",
    "highest_expected_value": "counterfactual_simulation",
    "who_should_execute": "peacock_action_engine",
    "what_if_we_dont": "counterfactual_simulation",
    "did_change_work": "outcome_measurement",
    "what_did_peacock_learn": "peacock_learning",
}

ARCHITECTURE_DIAGRAM = """\
                         PEACOCK ONE
                              │
                              ▼
                     DATA OBSERVATION LAYER
        ┌────────────┬──────────────┬──────────────┐
        │            │              │              │
      Website      Search          AI         Competitors
        │            │              │              │
        ├──────── Analytics         │              │
        │            │              │              │
        └────────────┴──────────────┴──────────────┘
                              │
                              ▼
                       EVIDENCE LEDGER
                              │
                              ▼
                             PINE
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
      SPECIALISTS        LLM FABRIC         DATA MODELS
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
                     PEACOCK COUNCIL
                              ▼
                         CRITIC LAYER
                              ▼
                     VERIFICATION LAYER
                              ▼
                       PEACOCK JUDGE
                              ▼
                 COUNTERFACTUAL SIMULATION
                              ▼
                    RECOMMENDATION ENGINE
                              ▼
                      PEACOCK ACTION ENGINE
                              ▼
                          EXECUTION
                              ▼
                         MONITORING
                              ▼
                         EXPERIMENTS
                              ▼
                     OUTCOME MEASUREMENT
                              ▼
                     PEACOCK LEARNING
                              │
                              └──────────────► PINE
"""


@dataclass
class FinalArchitectureSpec:
    client_brand: str
    # Optional: mark which product questions are addressed for this brand map
    addressed_questions: list[str] = field(default_factory=list)
    # If empty, demo assumes full standard coverage
    assume_full_standard: bool = True
    analysed_at: datetime | None = None


@dataclass(slots=True)
class PipelineStageView:
    stage_key: str
    stage_label: str
    rank_order: int
    next_stage_key: str | None
    loops_to_stage_key: str | None
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ObservationSourceView:
    source_key: str
    source_label: str
    feeds_evidence_ledger: bool
    rank_order: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PineLaneView:
    lane_key: str
    lane_label: str
    rank_order: int
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ProductQuestionView:
    question_key: str
    question_text: str
    required: bool
    addressed: bool
    primary_stage_key: str | None
    rank_order: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class FinalArchitectureResult:
    client_brand: str
    stages: list[PipelineStageView]
    observation_sources: list[ObservationSourceView]
    pine_lanes: list[PineLaneView]
    product_questions: list[ProductQuestionView]
    stages_count: int
    observation_sources_count: int
    pine_lanes_count: int
    product_questions_count: int
    learning_loops_to_pine: bool
    not_only_visibility: bool
    product_standard_coverage: float
    architecture_diagram: str
    architecture_positioning: str
    product_standard: str
    not_only_visibility_note: str
    methodology_note: str
    summary: str
    analysed_at: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "client_brand": self.client_brand,
            "stages": [s.to_dict() for s in self.stages],
            "observation_sources": [o.to_dict() for o in self.observation_sources],
            "pine_lanes": [p.to_dict() for p in self.pine_lanes],
            "product_questions": [q.to_dict() for q in self.product_questions],
            "stages_count": self.stages_count,
            "observation_sources_count": self.observation_sources_count,
            "pine_lanes_count": self.pine_lanes_count,
            "product_questions_count": self.product_questions_count,
            "learning_loops_to_pine": self.learning_loops_to_pine,
            "not_only_visibility": self.not_only_visibility,
            "product_standard_coverage": self.product_standard_coverage,
            "architecture_diagram": self.architecture_diagram,
            "architecture_positioning": self.architecture_positioning,
            "product_standard": self.product_standard,
            "not_only_visibility_note": self.not_only_visibility_note,
            "methodology_note": self.methodology_note,
            "summary": self.summary,
            "analysed_at": self.analysed_at.isoformat(),
        }


def catalog() -> dict[str, Any]:
    return {
        "pipeline_stages": list(PIPELINE_STAGES),
        "stage_labels": dict(STAGE_LABELS),
        "observation_sources": list(OBSERVATION_SOURCES),
        "observation_source_labels": dict(OBSERVATION_SOURCE_LABELS),
        "pine_fabric_lanes": list(PINE_FABRIC_LANES),
        "pine_fabric_labels": dict(PINE_FABRIC_LABELS),
        "product_questions": list(PRODUCT_QUESTIONS),
        "product_question_text": dict(PRODUCT_QUESTION_TEXT),
        "question_primary_stage": dict(QUESTION_PRIMARY_STAGE),
        "learning_loops_to": LEARNING_LOOPS_TO,
        "not_only_visibility_note": NOT_ONLY_VISIBILITY,
        "product_standard": PRODUCT_STANDARD,
        "architecture_positioning": ARCHITECTURE_POSITIONING,
        "methodology_note": METHODOLOGY_NOTE,
        "architecture_diagram": ARCHITECTURE_DIAGRAM,
        "product_note": (
            "Final Peacock Architecture — Observation → Evidence → PINE → … → "
            "Learning → PINE. Answer the full product-difference question set."
        ),
    }


def build_architecture_map(spec: FinalArchitectureSpec) -> FinalArchitectureResult:
    brand = (spec.client_brand or "").strip()
    if not brand:
        raise ValueError("client_brand is required")

    analysed_at = spec.analysed_at or datetime.now(tz=UTC)

    stages: list[PipelineStageView] = []
    for i, key in enumerate(PIPELINE_STAGES):
        next_key = PIPELINE_STAGES[i + 1] if i + 1 < len(PIPELINE_STAGES) else None
        loops_to = LEARNING_LOOPS_TO if key == "peacock_learning" else None
        stages.append(
            PipelineStageView(
                stage_key=key,
                stage_label=STAGE_LABELS[key],
                rank_order=i,
                next_stage_key=next_key,
                loops_to_stage_key=loops_to,
                detail=STAGE_DETAILS[key],
            )
        )

    sources = [
        ObservationSourceView(
            source_key=k,
            source_label=OBSERVATION_SOURCE_LABELS[k],
            feeds_evidence_ledger=True,
            rank_order=i,
        )
        for i, k in enumerate(OBSERVATION_SOURCES)
    ]

    lanes = [
        PineLaneView(
            lane_key=k,
            lane_label=PINE_FABRIC_LABELS[k],
            rank_order=i,
            detail=PINE_LANE_DETAILS[k],
        )
        for i, k in enumerate(PINE_FABRIC_LANES)
    ]

    addressed_set = set(spec.addressed_questions)
    if spec.assume_full_standard and not addressed_set:
        addressed_set = set(PRODUCT_QUESTIONS)
    for q in addressed_set:
        if q not in PRODUCT_QUESTIONS:
            raise ValueError(f"Unsupported product question: {q}")

    questions = [
        ProductQuestionView(
            question_key=k,
            question_text=PRODUCT_QUESTION_TEXT[k],
            required=True,
            addressed=k in addressed_set,
            primary_stage_key=QUESTION_PRIMARY_STAGE.get(k),
            rank_order=i,
        )
        for i, k in enumerate(PRODUCT_QUESTIONS)
    ]

    addressed_n = sum(1 for q in questions if q.addressed)
    coverage = round(100.0 * addressed_n / max(len(PRODUCT_QUESTIONS), 1), 1)
    # not_only_visibility: true when we address more than just how_visible
    not_only = addressed_n > 1 and "how_certain" in addressed_set

    summary = (
        f"Final Peacock Architecture map for {brand}: "
        f"{len(stages)} stages, {len(sources)} observation sources, "
        f"{len(lanes)} PINE lanes, {addressed_n}/{len(questions)} product "
        f"questions ({coverage}% coverage). Learning loops to PINE. "
        f"{NOT_ONLY_VISIBILITY} {PRODUCT_STANDARD}"
    )

    return FinalArchitectureResult(
        client_brand=brand,
        stages=stages,
        observation_sources=sources,
        pine_lanes=lanes,
        product_questions=questions,
        stages_count=len(stages),
        observation_sources_count=len(sources),
        pine_lanes_count=len(lanes),
        product_questions_count=len(questions),
        learning_loops_to_pine=True,
        not_only_visibility=not_only,
        product_standard_coverage=coverage,
        architecture_diagram=ARCHITECTURE_DIAGRAM,
        architecture_positioning=ARCHITECTURE_POSITIONING,
        product_standard=PRODUCT_STANDARD,
        not_only_visibility_note=NOT_ONLY_VISIBILITY,
        methodology_note=METHODOLOGY_NOTE,
        summary=summary,
        analysed_at=analysed_at,
    )


def demo_map(brand: str = "Acme") -> FinalArchitectureResult:
    return build_architecture_map(
        FinalArchitectureSpec(client_brand=brand, assume_full_standard=True)
    )
