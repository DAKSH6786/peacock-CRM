from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class StrategicRunRequest(BaseModel):
    request_text: str = Field(min_length=3, max_length=8000)
    workspace_id: str | None = None
    website_id: str | None = None
    crawl_id: str | None = None
    audit_id: str | None = None
    requested_output: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class StrategicRunResponse(BaseModel):
    id: str
    organisation_id: str
    workspace_id: str
    status: str
    classification: dict[str, Any]
    layers: list[dict[str, Any]]
    recommendations: list[dict[str, Any]]
    tasks: list[dict[str, Any]]
    evidence_summary: dict[str, int]
    context_summary: dict[str, Any]
    verification: dict[str, Any] | None = None
    learning: list[dict[str, Any]] = Field(default_factory=list)
    interpretation: str | None = None
