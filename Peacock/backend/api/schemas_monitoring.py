"""Monitoring API schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class MonitoringProjectRequest(BaseModel):
    website_id: str
    name: str = Field(min_length=2, max_length=255)
    workspace_id: str | None = None
    cadence: str = Field(default="weekly", max_length=32)


class MetricInput(BaseModel):
    metric_key: str = Field(min_length=1, max_length=128)
    metric_value: float
    captured_at: str | None = None


class SnapshotRequest(BaseModel):
    metrics: list[MetricInput] = Field(min_length=1)
    emit_learning: bool = True
    run_async: bool = False


class SearchPerformanceRequest(BaseModel):
    clicks: int = Field(ge=0)
    impressions: int = Field(ge=0)
    ctr: float | None = None
    avg_position: float | None = None


class MonitoringProjectResponse(BaseModel):
    project_id: str
    website_id: str
    name: str
    cadence: str
    is_active: bool


class SnapshotResponse(BaseModel):
    project_id: str
    snapshots: list[dict[str, Any]]
    learning_hooks: list[dict[str, Any]] = Field(default_factory=list)
    learning_record_ids: list[str] = Field(default_factory=list)
    job_id: str | None = None
