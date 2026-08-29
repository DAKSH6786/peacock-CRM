"""Ask Peacock 2.0 API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class GraphSignalRequest(BaseModel):
    surface: str = Field(min_length=1, max_length=64)
    key: str = Field(min_length=1, max_length=128)
    value: str = Field(min_length=1)
    weight: float = Field(default=0.7, ge=0.0, le=1.0)
    ref_id: str | None = Field(default=None, max_length=128)


class AskSessionBriefRequest(BaseModel):
    client_brand: str = Field(min_length=1, max_length=255)
    questions: list[str] = Field(default_factory=list)
    signals: list[GraphSignalRequest] = Field(default_factory=list)
    competitor_name: str | None = Field(default=None, max_length=255)
    budget_amount: str | None = Field(default=None, max_length=64)
    topic: str | None = Field(default=None, max_length=255)


class AskSessionRequest(BaseModel):
    website_id: str
    workspace_id: str | None = None
    name: str = Field(min_length=2, max_length=255)
    brief: AskSessionBriefRequest
    notes: str | None = None


class EvidenceResponse(BaseModel):
    evidence_index: int
    graph_surface: str
    claim: str
    ref_id: str | None
    weight: float
    section: str


class StructuredAnswerResponse(BaseModel):
    question_index: int
    question: str
    intent: str
    intent_label: str
    observed: str
    inferred: str
    recommended: str
    forecast: str
    confidence: float
    confidence_rationale: str
    graph_surfaces_used: list[str]
    answered_at: str
    evidence: list[EvidenceResponse]
    sections: dict[str, str | float]


class AskSessionResponse(BaseModel):
    session_id: str
    name: str
    client_brand: str
    methodology: str
    questions_asked: int
    answers_produced: int
    evidence_items: int
    mean_confidence: float | None
    primary_intent: str | None
    methodology_note: str
    summary: str
    answers: list[StructuredAnswerResponse]


class AskCatalogResponse(BaseModel):
    answer_sections: list[str]
    query_intents: list[str]
    intent_labels: dict[str, str]
    example_questions: list[str]
    graph_surfaces: list[str]
    methodology_note: str
    structure_note: str
