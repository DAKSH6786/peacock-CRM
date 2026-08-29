"""Final Peacock Architecture API schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ArchitectureBriefRequest(BaseModel):
    client_brand: str = Field(min_length=1, max_length=255)
    addressed_questions: list[str] = Field(default_factory=list)
    assume_full_standard: bool = True
    analysed_at: datetime | None = None


class ArchitectureMapCreateRequest(BaseModel):
    website_id: str
    workspace_id: str | None = None
    name: str = Field(min_length=2, max_length=255)
    brief: ArchitectureBriefRequest
    notes: str | None = None


class PipelineStageResponse(BaseModel):
    stage_key: str
    stage_label: str
    rank_order: int
    next_stage_key: str | None
    loops_to_stage_key: str | None
    detail: str


class ObservationSourceResponse(BaseModel):
    source_key: str
    source_label: str
    feeds_evidence_ledger: bool
    rank_order: int


class PineLaneResponse(BaseModel):
    lane_key: str
    lane_label: str
    rank_order: int
    detail: str


class ProductQuestionResponse(BaseModel):
    question_key: str
    question_text: str
    required: bool
    addressed: bool
    primary_stage_key: str | None
    rank_order: int


class ArchitectureMapResponse(BaseModel):
    map_id: str
    name: str
    client_brand: str
    methodology: str
    stages: list[PipelineStageResponse]
    observation_sources: list[ObservationSourceResponse]
    pine_lanes: list[PineLaneResponse]
    product_questions: list[ProductQuestionResponse]
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
    analysed_at: str


class ArchitecturePreviewResponse(BaseModel):
    client_brand: str
    stages: list[PipelineStageResponse]
    observation_sources: list[ObservationSourceResponse]
    pine_lanes: list[PineLaneResponse]
    product_questions: list[ProductQuestionResponse]
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
    analysed_at: str


class ArchitectureCatalogResponse(BaseModel):
    pipeline_stages: list[str]
    stage_labels: dict[str, str]
    observation_sources: list[str]
    observation_source_labels: dict[str, str]
    pine_fabric_lanes: list[str]
    pine_fabric_labels: dict[str, str]
    product_questions: list[str]
    product_question_text: dict[str, str]
    question_primary_stage: dict[str, str]
    learning_loops_to: str
    not_only_visibility_note: str
    product_standard: str
    architecture_positioning: str
    methodology_note: str
    architecture_diagram: str
    product_note: str
