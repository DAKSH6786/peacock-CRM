"""Peacock One Quality Bar API schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class GateAnswerRequest(BaseModel):
    gate_key: str = Field(min_length=1, max_length=64)
    answer_yes_problem: bool
    rationale: str | None = None
    evidence_note: str | None = None


class QualityBarBriefRequest(BaseModel):
    client_brand: str = Field(min_length=1, max_length=255)
    module_key: str = Field(default="custom", max_length=128)
    module_label: str | None = Field(default=None, max_length=255)
    gate_answers: list[GateAnswerRequest] = Field(default_factory=list)
    analysed_at: datetime | None = None


class QualityBarCreateRequest(BaseModel):
    website_id: str
    workspace_id: str | None = None
    name: str = Field(min_length=2, max_length=255)
    brief: QualityBarBriefRequest
    notes: str | None = None


class GateResultResponse(BaseModel):
    gate_key: str
    gate_label: str
    question: str
    improvement_if_fail: str
    passed: bool
    answer_yes_problem: bool
    rationale: str
    evidence_note: str | None
    rank_order: int


class RemediationActionResponse(BaseModel):
    gate_key: str
    action_key: str
    action_label: str
    detail: str
    links_to_learning: bool
    rank_order: int


class QualityBarAssessmentResponse(BaseModel):
    assessment_id: str
    name: str
    client_brand: str
    methodology: str
    module_key: str
    module_label: str
    completeness_verdict: str
    gates_total: int
    gates_passed: int
    gates_failed: int
    completeness_score: float
    blocked_by: list[str]
    improvement_summary: str
    gate_results: list[GateResultResponse]
    remediation_actions: list[RemediationActionResponse]
    quality_positioning: str
    methodology_note: str
    summary: str
    analysed_at: str


class QualityBarPreviewResponse(BaseModel):
    client_brand: str
    module_key: str
    module_label: str
    completeness_verdict: str
    gates_total: int
    gates_passed: int
    gates_failed: int
    completeness_score: float
    blocked_by: list[str]
    improvement_summary: str
    gate_results: list[GateResultResponse]
    remediation_actions: list[RemediationActionResponse]
    quality_positioning: str
    methodology_note: str
    summary: str
    analysed_at: str


class QualityBarCatalogResponse(BaseModel):
    quality_gates: list[str]
    gate_labels: dict[str, str]
    gate_questions: dict[str, str]
    gate_improvements: dict[str, str]
    gate_pass_means: dict[str, str]
    completeness_verdicts: list[str]
    module_catalog: dict[str, dict[str, str]]
    quality_positioning: str
    methodology_note: str
    product_note: str
    checklist: list[str]
