"""Peacock Anomaly Engine API schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class MetricPointRequest(BaseModel):
    occurred_at: datetime
    value: float


class MetricObservationRequest(BaseModel):
    metric_key: str = Field(min_length=1, max_length=128)
    anomaly_type: str = Field(min_length=1, max_length=64)
    points: list[MetricPointRequest] = Field(min_length=2)
    revenue_exposure: float | None = Field(default=None, ge=0.0)
    label_hint: str | None = None


class AnomalyScanBriefRequest(BaseModel):
    client_brand: str = Field(min_length=1, max_length=255)
    window_start: datetime
    window_end: datetime
    observations: list[MetricObservationRequest] = Field(default_factory=list)
    default_revenue_exposure: float = Field(default=0.0, ge=0.0)


class AnomalyScanRequest(BaseModel):
    website_id: str
    workspace_id: str | None = None
    name: str = Field(min_length=2, max_length=255)
    brief: AnomalyScanBriefRequest
    notes: str | None = None


class AnomalyResponse(BaseModel):
    anomaly_type: str
    anomaly_label: str
    title: str
    detail: str
    detected_at: str
    severity: str
    magnitude: float
    z_score: float
    impact_score: float
    impact_rank: int
    revenue_exposure: float | None
    metric_key: str | None
    baseline_value: float | None
    current_value: float | None
    recommended_response: str
    is_noise: bool


class AnomalyScanResponse(BaseModel):
    scan_id: str
    name: str
    client_brand: str
    methodology: str
    window_start: str
    window_end: str
    anomalies: list[AnomalyResponse]
    anomalies_detected: int
    critical_count: int
    high_count: int
    top_anomaly_type: str | None
    top_impact_score: float | None
    methodology_note: str
    summary: str


class AnomalyCatalogResponse(BaseModel):
    anomaly_types: dict[str, str]
    anomaly_codes: list[str]
    severity_levels: list[str]
    impact_priors: dict[str, float]
    methodology_note: str
    ranking_note: str
