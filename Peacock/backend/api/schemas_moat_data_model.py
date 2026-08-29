"""Peacock Moat Data Model API schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class MoatRunBriefRequest(BaseModel):
    client_brand: str = Field(min_length=1, max_length=255)
    industry: str | None = Field(default=None, max_length=64)
    analysed_at: datetime | None = None


class MoatRunCreateRequest(BaseModel):
    website_id: str
    workspace_id: str | None = None
    name: str = Field(min_length=2, max_length=255)
    brief: MoatRunBriefRequest
    notes: str | None = None


class NodeResponse(BaseModel):
    node_ordinal: int
    node_role: str
    node_kind: str
    node_key: str
    label: str


class EdgeResponse(BaseModel):
    from_ordinal: int
    to_ordinal: int
    edge_type: str
    weight: float


class OutcomeResponse(BaseModel):
    metric_key: str
    metric_value: float
    baseline_value: float | None
    delta: float | None
    observed_at: str
    provenance: str | None


class PathwayResponse(BaseModel):
    pathway_kind: str
    pathway_label: str
    pathway_key: str
    industry: str | None
    topic_key: str | None
    expected_score: float | None
    actual_score: float | None
    outcome_delta: float | None
    confidence: float
    sample_weight: float
    source_system: str | None
    source_ref: str | None
    narrative: str
    rank_order: int
    nodes: list[NodeResponse]
    edges: list[EdgeResponse]
    outcomes: list[OutcomeResponse]
    chain: str


class MoatRunResponse(BaseModel):
    run_id: str
    name: str
    client_brand: str
    methodology: str
    industry: str | None
    pathways: list[PathwayResponse]
    pathways_count: int
    nodes_count: int
    edges_count: int
    outcomes_count: int
    moat_strength_score: float
    mean_outcome_delta: float | None
    mean_confidence: float | None
    pathway_kind_coverage: list[str]
    moat_positioning: str
    methodology_note: str
    not_universal_geo: str
    summary: str
    analysed_at: str


class MoatPreviewResponse(BaseModel):
    client_brand: str
    industry: str | None
    pathways: list[PathwayResponse]
    pathways_count: int
    nodes_count: int
    edges_count: int
    outcomes_count: int
    moat_strength_score: float
    mean_outcome_delta: float | None
    mean_confidence: float | None
    pathway_kind_coverage: list[str]
    moat_positioning: str
    methodology_note: str
    not_universal_geo: str
    summary: str
    analysed_at: str


class MoatCatalogResponse(BaseModel):
    pathway_kinds: list[str]
    pathway_labels: dict[str, str]
    node_roles: list[str]
    node_kinds: list[str]
    edge_types: list[str]
    moat_positioning: str
    not_universal_geo: str
    methodology_note: str
    product_note: str
    example_pathways: list[str]
