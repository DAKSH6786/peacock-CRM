"""Peacock Temporal Intelligence API schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class TimelineEventRequest(BaseModel):
    event_kind: str = Field(min_length=1, max_length=64)
    occurred_at: datetime
    title: str = Field(min_length=1, max_length=255)
    detail: str = Field(min_length=1)
    magnitude: float = 0.0
    direction: str = Field(default="neutral", pattern="^(up|down|neutral)$")
    metric_key: str | None = None
    metric_value: float | None = None
    source_ref: str | None = None


class MetricPointRequest(BaseModel):
    occurred_at: datetime
    value: float


class MetricSeriesRequest(BaseModel):
    metric_key: str = Field(min_length=1, max_length=128)
    points: list[MetricPointRequest] = Field(default_factory=list)


class TimelineBriefRequest(BaseModel):
    client_brand: str = Field(min_length=1, max_length=255)
    window_start: datetime
    window_end: datetime
    events: list[TimelineEventRequest] = Field(default_factory=list)
    series: list[MetricSeriesRequest] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)


class TemporalTimelineRequest(BaseModel):
    website_id: str
    workspace_id: str | None = None
    name: str = Field(min_length=2, max_length=255)
    brief: TimelineBriefRequest
    notes: str | None = None


class EventResponse(BaseModel):
    event_kind: str
    event_label: str
    occurred_at: str
    title: str
    detail: str
    magnitude: float
    direction: str
    metric_key: str | None
    metric_value: float | None
    source_ref: str | None
    event_id: str | None = None


class ChangePointResponse(BaseModel):
    metric_key: str
    detected_at: str
    score: float
    effect_size: float
    baseline_mean: float
    baseline_std: float
    post_mean: float
    is_alert: bool
    suppressed_as_noise: bool
    rationale: str


class QueryAnswerResponse(BaseModel):
    intent: str
    question: str
    answer: str
    supporting_event_indexes: list[int]
    confidence: float


class TemporalTimelineResponse(BaseModel):
    timeline_id: str
    name: str
    client_brand: str
    methodology: str
    window_start: str
    window_end: str
    events: list[EventResponse]
    change_points: list[ChangePointResponse]
    query_answers: list[QueryAnswerResponse]
    events_count: int
    change_points_count: int
    alerts_suppressed: int
    noise_guardrail: str
    methodology_note: str
    summary: str


class TemporalCatalogResponse(BaseModel):
    event_kinds: dict[str, str]
    event_codes: list[str]
    query_intents: list[str]
    example_queries: list[str]
    noise_guardrail: str
    methodology_note: str
    change_detection: dict
