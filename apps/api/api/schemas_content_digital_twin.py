"""Content Digital Twin API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CompetitorPageRequest(BaseModel):
    url: str = ""
    title: str = Field(min_length=1, max_length=512)
    strengths: list[str] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)
    questions_covered: list[str] = Field(default_factory=list)
    evidence_types: list[str] = Field(default_factory=list)


class PersonaRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    intents: list[str] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)


class AiAnswerScenarioRequest(BaseModel):
    prompt: str = Field(min_length=2)
    expected_answer_shape: str | None = None
    must_include_entities: list[str] = Field(default_factory=list)
    must_answer_points: list[str] = Field(default_factory=list)


class BrandGuidelinesRequest(BaseModel):
    tone_keywords: list[str] = Field(default_factory=list)
    required_mentions: list[str] = Field(default_factory=list)
    forbidden_claims: list[str] = Field(default_factory=list)
    rules: list[str] = Field(default_factory=list)


class ArticlePlanRequest(BaseModel):
    title: str = Field(min_length=2, max_length=512)
    slug: str = Field(min_length=1, max_length=255)
    outline_sections: list[str] = Field(default_factory=list)
    target_keywords: list[str] = Field(default_factory=list)
    covered_entities: list[str] = Field(default_factory=list)
    evidence_claims: list[str] = Field(default_factory=list)
    questions_answered: list[str] = Field(default_factory=list)
    differentiation_angles: list[str] = Field(default_factory=list)
    planned_citations: list[str] = Field(default_factory=list)
    structured_elements: list[str] = Field(default_factory=list)
    brand_voice_notes: str | None = None
    body_summary: str | None = None


class SimulationContextRequest(BaseModel):
    seo_requirements: list[str] = Field(default_factory=list)
    aeo_requirements: list[str] = Field(default_factory=list)
    geo_requirements: list[str] = Field(default_factory=list)
    competitor_pages: list[CompetitorPageRequest] = Field(default_factory=list)
    target_entities: list[str] = Field(default_factory=list)
    user_personas: list[PersonaRequest] = Field(default_factory=list)
    ai_answer_scenarios: list[AiAnswerScenarioRequest] = Field(default_factory=list)
    citation_requirements: list[str] = Field(default_factory=list)
    brand_guidelines: BrandGuidelinesRequest = Field(default_factory=BrandGuidelinesRequest)


class CreateTwinRequest(BaseModel):
    website_id: str
    workspace_id: str | None = None
    name: str = Field(min_length=2, max_length=255)
    client_brand: str = Field(min_length=1, max_length=255)
    topic_cluster: str | None = None
    article_plan: ArticlePlanRequest
    simulation_context: SimulationContextRequest = Field(
        default_factory=SimulationContextRequest
    )
    content_lab_proposal_id: str | None = None
    notes: str | None = None


class UpdatePlanRequest(BaseModel):
    workspace_id: str | None = None
    article_plan: ArticlePlanRequest | None = None
    simulation_context: SimulationContextRequest | None = None
    name: str | None = Field(default=None, min_length=2, max_length=255)
    notes: str | None = None
    rerun: bool = True


class RequirementScoreResponse(BaseModel):
    surface: str
    coverage_score: float
    matched_count: int
    missing_count: int
    explanation: str


class FindingResponse(BaseModel):
    category: str
    title: str
    detail: str
    severity: str
    related_surface: str | None = None
    related_item: str | None = None
    priority: float


class EvaluationResponse(BaseModel):
    twin_id: str
    evaluation_id: str
    evaluation_number: int
    plan_revision: int
    client_brand: str
    methodology: str
    article_plan: dict
    predicted_strength_score: float
    readiness_score: float
    summary: str
    requirement_scores: list[RequirementScoreResponse]
    findings: list[FindingResponse]
    findings_by_category: dict[str, list[FindingResponse]]


class EvaluationHistoryItem(BaseModel):
    evaluation_id: str
    evaluation_number: int
    plan_revision: int
    predicted_strength_score: float
    readiness_score: float
    summary: str


class TwinResponse(BaseModel):
    twin_id: str
    name: str
    client_brand: str
    methodology: str
    plan_revision: int
    evaluation_count: int
    article_plan: dict
    simulation_context: dict
    latest_evaluation: EvaluationResponse | None
    evaluation_history: list[EvaluationHistoryItem]


class TwinCatalogResponse(BaseModel):
    simulation_surfaces: list[str]
    finding_categories: list[str]
    methodology: str
    methodology_note: str
