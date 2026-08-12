"""Retrieval Pathway Intelligence API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas_retrieval_pathway import (
    BottleneckResponse,
    CauseResponse,
    RetrievalPathwayCatalogResponse,
    RetrievalPathwayRequest,
    RetrievalPathwayResponse,
)
from observability.audit import AuditEvent, AuditLogger
from retrieval_pathway import (
    BOTTLENECK_STAGES,
    FORENSIC_CAUSES,
    LIKELIHOOD_BANDS,
    METHODOLOGY_DISCLAIMER,
    UNCERTAINTY_BANDS,
    ObservedEvidenceInput,
    RetrievalPathwayService,
    RetrievalPathwaySpec,
)

router = APIRouter(prefix="/retrieval-pathway", tags=["retrieval-pathway"])
audit_logger = AuditLogger()


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


def _to_response(report) -> RetrievalPathwayResponse:
    f = report.forensic
    b = f.bottleneck
    return RetrievalPathwayResponse(
        analysis_id=report.analysis_id,
        query_cluster=report.query_cluster,
        client_brand=report.client_brand,
        target_url=report.target_url,
        target_domain=report.target_domain,
        methodology=report.methodology,
        proprietary_ranking_access_claimed=False,
        disclaimer=report.disclaimer,
        estimated_retrieval_likelihood=f.estimated_retrieval_likelihood,
        estimated_selection_likelihood=f.estimated_selection_likelihood,
        retrieval_likelihood_band=f.retrieval_likelihood_band,
        selection_likelihood_band=f.selection_likelihood_band,
        overall_uncertainty=f.overall_uncertainty,
        causes=[CauseResponse(**c.to_dict()) for c in f.causes],
        bottleneck=BottleneckResponse(**b.to_dict()),
        evidence_summary=f.evidence_summary,
        example_display=report.example_display,
    )


@router.get("/catalog", response_model=RetrievalPathwayCatalogResponse)
def retrieval_pathway_catalog(
    ctx: AuthContext = Depends(get_auth_context),
) -> RetrievalPathwayCatalogResponse:
    _ = ctx
    return RetrievalPathwayCatalogResponse(
        forensic_causes=list(FORENSIC_CAUSES),
        likelihood_bands=list(LIKELIHOOD_BANDS),
        uncertainty_bands=list(UNCERTAINTY_BANDS),
        bottleneck_stages=list(BOTTLENECK_STAGES),
        methodology="inferred_retrieval_pathway",
        disclaimer=METHODOLOGY_DISCLAIMER,
        terminology=[
            "inferred retrieval pathway",
            "observed evidence",
            "estimated likelihood",
        ],
    )


@router.post("/analyses", response_model=RetrievalPathwayResponse, status_code=201)
def create_retrieval_pathway_analysis(
    body: RetrievalPathwayRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> RetrievalPathwayResponse:
    ws = _workspace_id(ctx, body.workspace_id)
    try:
        report = RetrievalPathwayService(db).analyse(
            organisation_id=ctx.organisation.id,
            workspace_id=ws,
            created_by=ctx.user.id,
            spec=RetrievalPathwaySpec(
                website_id=body.website_id,
                name=body.name,
                query_cluster=body.query_cluster,
                client_brand=body.client_brand,
                target_url=body.target_url,
                evidence=ObservedEvidenceInput(**body.evidence.model_dump()),
                competitor_urls=body.competitor_urls,
                notes=body.notes,
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_logger.log(
        AuditEvent(
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            action="retrieval_pathway.analyse",
            resource_type="retrieval_pathway_analysis",
            resource_id=report.analysis_id,
            workspace_id=ws,
            metadata={
                "query_cluster": report.query_cluster,
                "bottleneck": report.bottleneck.headline,
                "proprietary_ranking_access_claimed": False,
            },
        )
    )
    return _to_response(report)


@router.get("/analyses/{analysis_id}", response_model=RetrievalPathwayResponse)
def get_retrieval_pathway_analysis(
    analysis_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> RetrievalPathwayResponse:
    report = RetrievalPathwayService(db).get_report(
        analysis_id=analysis_id,
        organisation_id=ctx.organisation.id,
    )
    if report is None:
        raise HTTPException(
            status_code=404, detail="Retrieval Pathway analysis not found"
        )
    return _to_response(report)
