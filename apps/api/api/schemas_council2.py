"""Peacock Council 2.0 API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ContextFactRequest(BaseModel):
    label: str = Field(min_length=1, max_length=255)
    statement: str = Field(min_length=1)
    polarity: str = Field(default="neutral", pattern="^(support|oppose|neutral)$")
    strength: float = Field(default=0.5, ge=0.0, le=1.0)


class CouncilBriefRequest(BaseModel):
    decision_question: str = Field(min_length=4)
    client_brand: str = Field(min_length=1, max_length=255)
    context_summary: str | None = None
    facts: list[ContextFactRequest] = Field(default_factory=list)
    options: list[str] = Field(default_factory=list)
    model_by_role: dict[str, str] = Field(default_factory=dict)
    roles: list[str] = Field(default_factory=list)


class Council2SessionRequest(BaseModel):
    website_id: str
    workspace_id: str | None = None
    name: str = Field(min_length=2, max_length=255)
    brief: CouncilBriefRequest
    notes: str | None = None


class AgentResponse(BaseModel):
    role_code: str
    role_mandate: str
    model_label: str
    open_opinion_prompt_rejected: bool


class RoundResponse(BaseModel):
    round_number: int
    round_code: str
    round_label: str
    structured_summary: str


class ClaimResponse(BaseModel):
    claim_key: str
    role_code: str
    round_number: int
    statement: str
    confidence: float
    stance: str


class EvidenceResponse(BaseModel):
    claim_key: str
    role_code: str
    round_number: int
    statement: str
    source_ref: str | None
    strength: float


class CounterargumentResponse(BaseModel):
    claim_key: str
    role_code: str
    round_number: int
    statement: str
    confidence: float


class DisagreementResponse(BaseModel):
    claim_key: str
    role_a: str
    role_b: str
    summary: str
    severity: float


class EvidenceRequestResponse(BaseModel):
    claim_key: str
    requested_by_role: str
    request_statement: str
    fulfilled: bool
    fulfillment_evidence: str | None


class DecisionResponse(BaseModel):
    decision: str
    confidence: float
    supporting_claim_keys: list[str]
    rejected_claim_keys: list[str]
    judge_role: str


class Council2SessionResponse(BaseModel):
    session_id: str
    name: str
    client_brand: str
    methodology: str
    decision_question: str
    open_opinion_prompts_rejected: bool
    chain_of_thought_not_stored: bool
    stored_artifact_kinds: list[str]
    methodology_note: str
    summary: str
    final_decision: str
    final_confidence: float
    agents: list[AgentResponse]
    rounds: list[RoundResponse]
    claims: list[ClaimResponse]
    evidence: list[EvidenceResponse]
    counterarguments: list[CounterargumentResponse]
    disagreements: list[DisagreementResponse]
    evidence_requests: list[EvidenceRequestResponse]
    decisions: list[DecisionResponse]


class Council2CatalogResponse(BaseModel):
    roles: list[str]
    role_mandates: dict[str, str]
    debate_rounds: list[dict]
    stored_artifact_kinds: list[str]
    forbidden_prompts: list[str]
    forbidden_storage_fields: list[str]
    methodology: str
    methodology_note: str
    open_opinion_prompts_rejected: bool
    chain_of_thought_not_stored: bool
