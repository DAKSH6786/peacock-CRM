"""Peacock Moat Data Model API — proprietary intelligence accumulation."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from moat_data_model import (
    MoatCreateSpec,
    MoatDataModelService,
    MoatRunSpec,
    accumulate_moat,
    catalog,
)
from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas_moat_data_model import (
    EdgeResponse,
    MoatCatalogResponse,
    MoatPreviewResponse,
    MoatRunCreateRequest,
    MoatRunResponse,
    NodeResponse,
    OutcomeResponse,
    PathwayResponse,
)
from observability.audit import AuditEvent, AuditLogger

router = APIRouter(prefix="/moat-data-model", tags=["moat-data-model"])
audit_logger = AuditLogger()


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


def _pathway_response(p) -> PathwayResponse:
    data = p.to_dict()
    return PathwayResponse(
        pathway_kind=data["pathway_kind"],
        pathway_label=data["pathway_label"],
        pathway_key=data["pathway_key"],
        industry=data["industry"],
        topic_key=data["topic_key"],
        expected_score=data["expected_score"],
        actual_score=data["actual_score"],
        outcome_delta=data["outcome_delta"],
        confidence=data["confidence"],
        sample_weight=data["sample_weight"],
        source_system=data["source_system"],
        source_ref=data["source_ref"],
        narrative=data["narrative"],
        rank_order=data["rank_order"],
        nodes=[NodeResponse(**n) for n in data["nodes"]],
        edges=[EdgeResponse(**e) for e in data["edges"]],
        outcomes=[OutcomeResponse(**o) for o in data["outcomes"]],
        chain=data["chain"],
    )


def _result_fields(result) -> dict:
    return {
        "industry": result.industry,
        "pathways": [_pathway_response(p) for p in result.pathways],
        "pathways_count": result.pathways_count,
        "nodes_count": result.nodes_count,
        "edges_count": result.edges_count,
        "outcomes_count": result.outcomes_count,
        "moat_strength_score": result.moat_strength_score,
        "mean_outcome_delta": result.mean_outcome_delta,
        "mean_confidence": result.mean_confidence,
        "pathway_kind_coverage": result.pathway_kind_coverage,
        "moat_positioning": result.moat_positioning,
        "methodology_note": result.methodology_note,
        "not_universal_geo": result.not_universal_geo,
        "summary": result.summary,
        "analysed_at": result.analysed_at.isoformat(),
    }


def _to_response(report) -> MoatRunResponse:
    return MoatRunResponse(
        run_id=report.run_id,
        name=report.name,
        client_brand=report.client_brand,
        methodology=report.methodology,
        **_result_fields(report.result),
    )


@router.get("/catalog", response_model=MoatCatalogResponse)
def moat_catalog(
    ctx: AuthContext = Depends(get_auth_context),
) -> MoatCatalogResponse:
    _ = ctx
    return MoatCatalogResponse(**catalog())


@router.get("/preview", response_model=MoatPreviewResponse)
def moat_preview(
    brand: str = "Acme",
    industry: str | None = "saas_b2b",
) -> MoatPreviewResponse:
    """Public demo of the seven proprietary pathway kinds."""
    result = accumulate_moat(
        MoatRunSpec(client_brand=brand, industry=industry)
    )
    return MoatPreviewResponse(
        client_brand=result.client_brand,
        **_result_fields(result),
    )


@router.post("/runs", response_model=MoatRunResponse, status_code=201)
def create_moat_run(
    body: MoatRunCreateRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> MoatRunResponse:
    ws = _workspace_id(ctx, body.workspace_id)
    try:
        report = MoatDataModelService(db).accumulate(
            organisation_id=ctx.organisation.id,
            workspace_id=ws,
            created_by=ctx.user.id,
            spec=MoatCreateSpec(
                website_id=body.website_id,
                name=body.name,
                run=MoatRunSpec(
                    client_brand=body.brief.client_brand,
                    industry=body.brief.industry,
                    analysed_at=body.brief.analysed_at,
                ),
                notes=body.notes,
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_logger.log(
        AuditEvent(
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            action="moat_data_model.accumulate",
            resource_type="moat_intelligence_run",
            resource_id=report.run_id,
            workspace_id=ws,
            metadata={
                "moat_strength_score": report.result.moat_strength_score,
                "pathways_count": report.result.pathways_count,
                "pathway_kinds": report.result.pathway_kind_coverage,
            },
        )
    )
    return _to_response(report)


@router.get("/runs/{run_id}", response_model=MoatRunResponse)
def get_moat_run(
    run_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> MoatRunResponse:
    report = MoatDataModelService(db).get_run(
        run_id=run_id,
        organisation_id=ctx.organisation.id,
    )
    if report is None:
        raise HTTPException(status_code=404, detail="Moat run not found")
    return _to_response(report)
