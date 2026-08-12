"""Peacock Citation Graph API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas_citation_graph import (
    CitationGraphCatalogResponse,
    CitationGraphRequest,
    CitationGraphResponse,
    DomainScoreResponse,
    OpportunityResponse,
    PathwayResponse,
)
from citation_graph import (
    CIS_COMPONENTS,
    DEFAULT_CIS_WEIGHTS,
    FORBIDDEN_TACTICS,
    OPPORTUNITY_TYPES,
    PATHWAY_NODE_KINDS,
    SOURCE_CLASSES,
    CitationGraphService,
)
from citation_graph.models import (
    CitationGraphSpec,
    CitationSpec,
    EntityMentionSpec,
    ObservationSpec,
)
from observability.audit import AuditEvent, AuditLogger

router = APIRouter(prefix="/citation-graph", tags=["citation-graph"])
audit_logger = AuditLogger()


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


def _domain(d) -> DomainScoreResponse:
    return DomainScoreResponse(
        cited_domain=d.cited_domain,
        source_class=d.source_class,
        is_citation_hub=d.is_citation_hub,
        is_competitor_owned=d.is_competitor_owned,
        is_client_owned=d.is_client_owned,
        citation_influence_score=d.citation_influence_score,
        components=d.components,
        explanations=d.explanations,
        citation_count=d.citation_count,
        engine_count=d.engine_count,
        page_count=d.page_count,
        observation_share=d.observation_share,
        client_mention_rate=d.client_mention_rate,
        competitor_mention_rate=d.competitor_mention_rate,
        top_competitor_name=d.top_competitor_name,
        top_competitor_mention_rate=d.top_competitor_mention_rate,
    )


def _to_response(report) -> CitationGraphResponse:
    example = None
    if report.opportunities:
        o = report.opportunities[0]
        example = {
            "domain": o.cited_domain,
            "message": (
                f"This source influences {o.domain_answer_influence_pct:.0f}% of AI answers "
                f"in this topic cluster. Your brand is mentioned in {o.client_mention_pct:.0f}%."
                + (
                    f" {o.top_competitor_name} is mentioned in {o.top_competitor_mention_pct:.0f}%."
                    if o.top_competitor_name
                    else ""
                )
            ),
            "opportunity_type": o.opportunity_type,
            "recommended_actions": o.recommended_actions,
        }
    return CitationGraphResponse(
        analysis_id=report.analysis_id,
        topic_cluster=report.topic_cluster,
        client_brand=report.client_brand,
        methodology=report.methodology,
        observation_count=report.observation_count,
        citation_count=report.citation_count,
        domain_count=report.domain_count,
        pathway_count=report.pathway_count,
        pathway_chain=list(PATHWAY_NODE_KINDS),
        domains=[_domain(d) for d in report.domains],
        hubs=[_domain(d) for d in report.hubs],
        pathways_sample=[
            PathwayResponse(**p.__dict__) for p in report.pathways_sample
        ],
        opportunities=[
            OpportunityResponse(
                cited_domain=o.cited_domain,
                source_class=o.source_class,
                opportunity_type=o.opportunity_type,
                priority=o.priority,
                domain_answer_influence_pct=o.domain_answer_influence_pct,
                client_mention_pct=o.client_mention_pct,
                top_competitor_name=o.top_competitor_name,
                top_competitor_mention_pct=o.top_competitor_mention_pct,
                title=o.title,
                rationale=o.rationale,
                recommended_actions=o.recommended_actions,
                manipulative_spam_rejected=o.manipulative_spam_rejected,
            )
            for o in report.opportunities
        ],
        source_class_breakdown=report.source_class_breakdown,
        cis_weights=report.cis_weights,
        manipulative_spam_rejected=report.manipulative_spam_rejected,
        example_opportunity=example,
    )


@router.get("/catalog", response_model=CitationGraphCatalogResponse)
def citation_graph_catalog(
    ctx: AuthContext = Depends(get_auth_context),
) -> CitationGraphCatalogResponse:
    _ = ctx
    return CitationGraphCatalogResponse(
        pathway_chain=list(PATHWAY_NODE_KINDS),
        source_classes=list(SOURCE_CLASSES),
        cis_components=list(CIS_COMPONENTS),
        default_cis_weights=dict(DEFAULT_CIS_WEIGHTS),
        opportunity_types=list(OPPORTUNITY_TYPES),
        forbidden_tactics=list(FORBIDDEN_TACTICS),
        methodology_note=(
            "Citation Influence Score is a weighted sum of explainable components "
            "(frequency, cross-engine, topic coverage, prominence, freshness, "
            "authority proxy, brand association, diversity). "
            "Source Opportunity Engine never recommends manipulative spam."
        ),
    )


@router.post("/analyses", response_model=CitationGraphResponse, status_code=201)
def create_citation_graph_analysis(
    body: CitationGraphRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> CitationGraphResponse:
    ws = _workspace_id(ctx, body.workspace_id)
    try:
        report = CitationGraphService(db).analyse(
            organisation_id=ctx.organisation.id,
            workspace_id=ws,
            created_by=ctx.user.id,
            spec=CitationGraphSpec(
                website_id=body.website_id,
                name=body.name,
                topic_cluster=body.topic_cluster,
                client_brand=body.client_brand,
                competitor_brands=body.competitor_brands,
                client_domains=body.client_domains,
                competitor_domains=body.competitor_domains,
                observations=[
                    ObservationSpec(
                        engine_code=o.engine_code,
                        prompt_text=o.prompt_text,
                        answer_excerpt=o.answer_excerpt,
                        topic_label=o.topic_label,
                        model_code=o.model_code,
                        citations=[CitationSpec(**c.model_dump()) for c in o.citations],
                        entities=[
                            EntityMentionSpec(**e.model_dump()) for e in o.entities
                        ],
                    )
                    for o in body.observations
                ],
                notes=body.notes,
                cis_weights=body.cis_weights,
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_logger.log(
        AuditEvent(
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            action="citation_graph.analyse",
            resource_type="citation_graph_analysis",
            resource_id=report.analysis_id,
            workspace_id=ws,
            metadata={
                "topic_cluster": report.topic_cluster,
                "domains": report.domain_count,
                "opportunities": len(report.opportunities),
                "manipulative_spam_rejected": True,
            },
        )
    )
    return _to_response(report)


@router.get("/analyses/{analysis_id}", response_model=CitationGraphResponse)
def get_citation_graph_analysis(
    analysis_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> CitationGraphResponse:
    report = CitationGraphService(db).get_report(
        analysis_id=analysis_id,
        organisation_id=ctx.organisation.id,
    )
    if report is None:
        raise HTTPException(status_code=404, detail="Citation Graph analysis not found")
    return _to_response(report)
