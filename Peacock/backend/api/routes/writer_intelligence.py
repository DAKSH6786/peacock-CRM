"""Writer Intelligence 2.0 API — proprietary outcome decision (not similarity)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas_writer_intelligence import (
    DnaTraitResponse,
    OutcomeEdgeResponse,
    OutcomeNodeResponse,
    PerformanceRecordResponse,
    RecommendationResponse,
    WriterDnaResponse,
    WriterIntelligenceCatalogResponse,
    WriterIntelligenceRequest,
    WriterIntelligenceResponse,
)
from observability.audit import AuditEvent, AuditLogger
from writer_intelligence import (
    METHODOLOGY,
    METHODOLOGY_NOTE,
    OUTCOME_EDGE_TYPES,
    OUTCOME_NODE_KINDS,
    PERFORMANCE_METRICS,
    SIMILARITY_ONLY_REJECTED,
    WRITER_DNA_TRAITS,
    ArticleOutcomeHistory,
    DecisionContext,
    WriterCandidate,
    WriterIntelligenceService,
    WriterIntelligenceSpec,
    recommend_writers,
)

router = APIRouter(prefix="/writer-intelligence", tags=["writer-intelligence"])
audit_logger = AuditLogger()


def _preview_context(brand: str) -> DecisionContext:
    return DecisionContext(
        client_brand=brand,
        industry="B2B SaaS",
        topic="AI visibility monitoring",
        audience="Marketing & SEO leaders",
        required_traits=["seo_execution", "aeo_execution"],
    )


def _preview_writers() -> list[WriterCandidate]:
    return [
        WriterCandidate(
            writer_key="writer_amina",
            display_name="Amina Chen",
            dna_traits={
                "subject_expertise": 88,
                "research_depth": 82,
                "technical_accuracy": 85,
                "seo_execution": 80,
                "aeo_execution": 78,
                "geo_execution": 74,
                "editing_effort": 25,
                "deadline_reliability": 90,
                "client_acceptance": 86,
            },
            subject_tags=["SEO", "AEO", "AI visibility"],
            prior_topics=["AI visibility monitoring", "answer engine optimisation"],
            prior_industries=["B2B SaaS"],
            prior_audiences=["Marketing & SEO leaders"],
        ),
        WriterCandidate(
            writer_key="writer_diego",
            display_name="Diego Alvarez",
            dna_traits={
                "subject_expertise": 60,
                "research_depth": 55,
                "technical_accuracy": 65,
                "storytelling": 85,
                "seo_execution": 50,
                "aeo_execution": 45,
                "geo_execution": 40,
                "editing_effort": 55,
                "deadline_reliability": 70,
                "client_acceptance": 72,
            },
            subject_tags=["brand storytelling", "content marketing"],
            prior_topics=["brand narrative"],
            prior_industries=["consumer retail"],
            prior_audiences=["general consumers"],
        ),
    ]


def _preview_history() -> list[ArticleOutcomeHistory]:
    return [
        ArticleOutcomeHistory(
            article_key="article_1",
            writer_key="writer_amina",
            client_key="Acme",
            industry="B2B SaaS",
            topic="AI visibility monitoring",
            audience="Marketing & SEO leaders",
            title="How AI Visibility Monitoring Works",
            approval=0.95,
            revision_rounds=1,
            ranking=0.8,
            ai_citations=12,
            engagement=0.6,
        ),
        ArticleOutcomeHistory(
            article_key="article_2",
            writer_key="writer_diego",
            client_key="Acme",
            industry="B2B SaaS",
            topic="brand narrative",
            audience="general consumers",
            title="Our Brand Story",
            approval=0.7,
            revision_rounds=3,
            ranking=0.4,
            ai_citations=2,
            engagement=0.5,
        ),
    ]


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


def _to_response(report) -> WriterIntelligenceResponse:
    r = report.result
    return WriterIntelligenceResponse(
        analysis_id=report.analysis_id,
        name=report.name,
        client_brand=report.client_brand,
        industry=report.industry,
        topic=report.topic,
        audience=report.audience,
        methodology=report.methodology,
        decision_question=r.decision_question,
        methodology_note=r.methodology_note,
        similarity_only_rejected=True,
        similarity_rejection_note=r.similarity_rejection_note,
        dna_profiles=[
            WriterDnaResponse(
                writer_key=d.writer_key,
                display_name=d.display_name,
                traits=[DnaTraitResponse(**t.to_dict()) for t in d.traits],
                dna_composite_score=d.dna_composite_score,
                dna_summary=d.dna_summary,
            )
            for d in r.dna_profiles
        ],
        recommendations=[
            RecommendationResponse(**x.to_dict()) for x in r.recommendations
        ],
        outcome_nodes=[OutcomeNodeResponse(**n.to_dict()) for n in r.outcome_nodes],
        outcome_edges=[OutcomeEdgeResponse(**e.to_dict()) for e in r.outcome_edges],
        performance_records=[
            PerformanceRecordResponse(**p.to_dict()) for p in r.performance_records
        ],
        top_writer_key=r.top_writer_key,
        top_outcome_score=r.top_outcome_score,
        summary=r.summary,
    )


@router.get("/preview", response_model=WriterIntelligenceResponse)
def writer_intelligence_preview(brand: str = "Acme") -> WriterIntelligenceResponse:
    """Public demo analysis for the Content Optimizer module."""
    context = _preview_context(brand)
    result = recommend_writers(
        context=context,
        writers=_preview_writers(),
        history=_preview_history(),
    )
    return WriterIntelligenceResponse(
        analysis_id="preview",
        name=f"{brand} — Content Optimizer preview",
        client_brand=brand,
        industry=context.industry,
        topic=context.topic,
        audience=context.audience,
        methodology=METHODOLOGY,
        decision_question=result.decision_question,
        methodology_note=result.methodology_note,
        similarity_only_rejected=True,
        similarity_rejection_note=result.similarity_rejection_note,
        dna_profiles=[
            WriterDnaResponse(
                writer_key=d.writer_key,
                display_name=d.display_name,
                traits=[DnaTraitResponse(**t.to_dict()) for t in d.traits],
                dna_composite_score=d.dna_composite_score,
                dna_summary=d.dna_summary,
            )
            for d in result.dna_profiles
        ],
        recommendations=[
            RecommendationResponse(**x.to_dict()) for x in result.recommendations
        ],
        outcome_nodes=[OutcomeNodeResponse(**n.to_dict()) for n in result.outcome_nodes],
        outcome_edges=[OutcomeEdgeResponse(**e.to_dict()) for e in result.outcome_edges],
        performance_records=[
            PerformanceRecordResponse(**p.to_dict()) for p in result.performance_records
        ],
        top_writer_key=result.top_writer_key,
        top_outcome_score=result.top_outcome_score,
        summary=result.summary,
    )


@router.get("/catalog", response_model=WriterIntelligenceCatalogResponse)
def writer_intelligence_catalog(
    ctx: AuthContext = Depends(get_auth_context),
) -> WriterIntelligenceCatalogResponse:
    _ = ctx
    return WriterIntelligenceCatalogResponse(
        dna_traits=list(WRITER_DNA_TRAITS),
        outcome_node_kinds=list(OUTCOME_NODE_KINDS),
        outcome_edge_types=list(OUTCOME_EDGE_TYPES),
        performance_metrics=list(PERFORMANCE_METRICS),
        methodology=METHODOLOGY,
        methodology_note=METHODOLOGY_NOTE,
        similarity_only_rejected=True,
        similarity_rejection_note=SIMILARITY_ONLY_REJECTED,
        decision_question_template=(
            "Which writer is most likely to produce the best outcome "
            "for THIS topic, for THIS client, for THIS audience?"
        ),
    )


@router.post("/analyses", response_model=WriterIntelligenceResponse, status_code=201)
def create_writer_intelligence_analysis(
    body: WriterIntelligenceRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> WriterIntelligenceResponse:
    ws = _workspace_id(ctx, body.workspace_id)
    try:
        report = WriterIntelligenceService(db).analyse(
            organisation_id=ctx.organisation.id,
            workspace_id=ws,
            created_by=ctx.user.id,
            spec=WriterIntelligenceSpec(
                website_id=body.website_id,
                name=body.name,
                context=DecisionContext(**body.context.model_dump()),
                writers=[WriterCandidate(**w.model_dump()) for w in body.writers],
                history=[
                    ArticleOutcomeHistory(**h.model_dump()) for h in body.history
                ],
                notes=body.notes,
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_logger.log(
        AuditEvent(
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            action="writer_intelligence.analyse",
            resource_type="writer_intelligence_analysis",
            resource_id=report.analysis_id,
            workspace_id=ws,
            metadata={
                "similarity_only_rejected": True,
                "top_writer_key": report.result.top_writer_key,
                "top_outcome_score": report.result.top_outcome_score,
            },
        )
    )
    return _to_response(report)


@router.get("/analyses/{analysis_id}", response_model=WriterIntelligenceResponse)
def get_writer_intelligence_analysis(
    analysis_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> WriterIntelligenceResponse:
    report = WriterIntelligenceService(db).get_report(
        analysis_id=analysis_id,
        organisation_id=ctx.organisation.id,
    )
    if report is None:
        raise HTTPException(
            status_code=404, detail="Writer Intelligence analysis not found"
        )
    return _to_response(report)
