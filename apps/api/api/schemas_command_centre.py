"""Peacock Command Centre API schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class VisibilitySignalRequest(BaseModel):
    dimension: str = Field(min_length=1, max_length=64)
    score: float = Field(ge=0.0, le=100.0)
    delta: float = 0.0


class SituationRequest(BaseModel):
    kind: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=255)
    detail: str = Field(min_length=1)
    severity: str = Field(default="medium", max_length=16)


class FeedItemRequest(BaseModel):
    headline: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1)
    primary_driver: str = Field(min_length=1)
    potential_response: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    detected_at: datetime | None = None
    graph_surface: str | None = Field(default=None, max_length=64)
    detection_label: str = Field(default="PEACOCK DETECTED", max_length=64)


class CommandCentreBriefRequest(BaseModel):
    client_brand: str = Field(min_length=1, max_length=255)
    signals: list[VisibilitySignalRequest] = Field(default_factory=list)
    situations: list[SituationRequest] = Field(default_factory=list)
    feed_items: list[FeedItemRequest] = Field(default_factory=list)
    captured_at: datetime | None = None


class CommandCentreSnapshotRequest(BaseModel):
    website_id: str
    workspace_id: str | None = None
    name: str = Field(min_length=2, max_length=255)
    brief: CommandCentreBriefRequest
    notes: str | None = None


class VisibilitySignalResponse(BaseModel):
    dimension: str
    label: str
    score: float
    delta: float
    rank_order: int


class SituationResponse(BaseModel):
    kind: str
    label: str
    title: str
    detail: str
    severity: str
    rank_order: int


class FeedItemResponse(BaseModel):
    feed_index: int
    detection_label: str
    headline: str
    body: str
    primary_driver: str
    potential_response: str
    confidence: float
    confidence_pct: int
    detected_at: str
    graph_surface: str | None


class CommandCentreSnapshotResponse(BaseModel):
    snapshot_id: str
    name: str
    client_brand: str
    methodology: str
    visibility_index: float
    visibility_delta: float
    captured_at: str
    headline: str
    signals: list[VisibilitySignalResponse]
    situations: list[SituationResponse]
    feed_items: list[FeedItemResponse]
    methodology_note: str
    summary: str


class CommandCentreCatalogResponse(BaseModel):
    visibility_dimensions: list[str]
    visibility_labels: dict[str, str]
    situation_kinds: list[str]
    situation_labels: dict[str, str]
    methodology_note: str
    product_note: str


class CommandCentrePreviewResponse(BaseModel):
    """Unauthenticated demo payload for the flagship UI."""

    client_brand: str
    visibility_index: float
    visibility_delta: float
    captured_at: str
    headline: str
    signals: list[VisibilitySignalResponse]
    situations: list[SituationResponse]
    feed_items: list[FeedItemResponse]
    methodology_note: str
    summary: str
