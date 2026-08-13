"""Peacock Executive Brain API schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ExecutiveSignalRequest(BaseModel):
    key: str = Field(min_length=1, max_length=128)
    value: str = Field(min_length=1)
    polarity: str = Field(default="neutral", max_length=32)
    weight: float = Field(default=0.75, ge=0.0, le=1.0)


class ExecutiveBrainBriefRequest(BaseModel):
    client_brand: str = Field(min_length=1, max_length=255)
    competitor_name: str = Field(default="Competitor A", max_length=255)
    budget_label: str = Field(default="₹10 lakh", max_length=64)
    horizon_days: int = Field(default=90, ge=30, le=365)
    signals: list[ExecutiveSignalRequest] = Field(default_factory=list)
    generated_at: datetime | None = None


class ExecutiveBrainCreateRequest(BaseModel):
    website_id: str
    workspace_id: str | None = None
    name: str = Field(min_length=2, max_length=255)
    brief: ExecutiveBrainBriefRequest
    notes: str | None = None


class ExecutiveAnswerResponse(BaseModel):
    question_key: str
    question_label: str
    answer: str
    evidence_note: str
    confidence: float
    rank_order: int


class RoleSummaryResponse(BaseModel):
    role: str
    title: str
    body: str
    call_to_action: str


class ExecutiveBrainResponse(BaseModel):
    brief_id: str
    name: str
    client_brand: str
    methodology: str
    generated_at: str
    horizon_days: int
    budget_label: str
    overall_confidence: float
    headline: str
    answers: list[ExecutiveAnswerResponse]
    role_summaries: list[RoleSummaryResponse]
    methodology_note: str
    summary: str


class ExecutiveBrainCatalogResponse(BaseModel):
    executive_questions: list[str]
    executive_question_labels: dict[str, str]
    summary_roles: list[str]
    methodology_note: str
    product_note: str


class ExecutiveBrainPreviewResponse(BaseModel):
    client_brand: str
    generated_at: str
    horizon_days: int
    budget_label: str
    overall_confidence: float
    headline: str
    answers: list[ExecutiveAnswerResponse]
    role_summaries: list[RoleSummaryResponse]
    methodology_note: str
    summary: str
