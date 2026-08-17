"""Final Peacock Architecture API — system map + product standard."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from final_architecture import (
    FinalArchitectureCreateSpec,
    FinalArchitectureService,
    FinalArchitectureSpec,
    catalog,
    demo_map,
)
from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas_final_architecture import (
    ArchitectureCatalogResponse,
    ArchitectureMapCreateRequest,
    ArchitectureMapResponse,
    ArchitecturePreviewResponse,
    ObservationSourceResponse,
    PineLaneResponse,
    PipelineStageResponse,
    ProductQuestionResponse,
)
from observability.audit import AuditEvent, AuditLogger

router = APIRouter(prefix="/final-architecture", tags=["final-architecture"])
audit_logger = AuditLogger()


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


def _result_fields(result) -> dict:
    return {
        "stages": [PipelineStageResponse(**s.to_dict()) for s in result.stages],
        "observation_sources": [
            ObservationSourceResponse(**o.to_dict()) for o in result.observation_sources
        ],
        "pine_lanes": [PineLaneResponse(**p.to_dict()) for p in result.pine_lanes],
        "product_questions": [
            ProductQuestionResponse(**q.to_dict()) for q in result.product_questions
        ],
        "stages_count": result.stages_count,
        "observation_sources_count": result.observation_sources_count,
        "pine_lanes_count": result.pine_lanes_count,
        "product_questions_count": result.product_questions_count,
        "learning_loops_to_pine": result.learning_loops_to_pine,
        "not_only_visibility": result.not_only_visibility,
        "product_standard_coverage": result.product_standard_coverage,
        "architecture_diagram": result.architecture_diagram,
        "architecture_positioning": result.architecture_positioning,
        "product_standard": result.product_standard,
        "not_only_visibility_note": result.not_only_visibility_note,
        "methodology_note": result.methodology_note,
        "summary": result.summary,
        "analysed_at": result.analysed_at.isoformat(),
    }


def _to_response(report) -> ArchitectureMapResponse:
    return ArchitectureMapResponse(
        map_id=report.map_id,
        name=report.name,
        client_brand=report.client_brand,
        methodology=report.methodology,
        **_result_fields(report.result),
    )


@router.get("/catalog", response_model=ArchitectureCatalogResponse)
def architecture_catalog(
    ctx: AuthContext = Depends(get_auth_context),
) -> ArchitectureCatalogResponse:
    _ = ctx
    return ArchitectureCatalogResponse(**catalog())


@router.get("/preview", response_model=ArchitecturePreviewResponse)
def architecture_preview(brand: str = "Acme") -> ArchitecturePreviewResponse:
    """Demo Final Peacock Architecture with full product-standard coverage."""
    result = demo_map(brand)
    return ArchitecturePreviewResponse(
        client_brand=result.client_brand,
        **_result_fields(result),
    )


@router.post("/maps", response_model=ArchitectureMapResponse, status_code=201)
def create_architecture_map(
    body: ArchitectureMapCreateRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> ArchitectureMapResponse:
    ws = _workspace_id(ctx, body.workspace_id)
    try:
        report = FinalArchitectureService(db).create_map(
            organisation_id=ctx.organisation.id,
            workspace_id=ws,
            created_by=ctx.user.id,
            spec=FinalArchitectureCreateSpec(
                website_id=body.website_id,
                name=body.name,
                architecture=FinalArchitectureSpec(
                    client_brand=body.brief.client_brand,
                    addressed_questions=body.brief.addressed_questions,
                    assume_full_standard=body.brief.assume_full_standard,
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
            action="final_architecture.map",
            resource_type="final_architecture_map",
            resource_id=report.map_id,
            workspace_id=ws,
            metadata={
                "product_standard_coverage": report.result.product_standard_coverage,
                "learning_loops_to_pine": report.result.learning_loops_to_pine,
                "not_only_visibility": report.result.not_only_visibility,
            },
        )
    )
    return _to_response(report)


@router.get("/maps/{map_id}", response_model=ArchitectureMapResponse)
def get_architecture_map(
    map_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> ArchitectureMapResponse:
    report = FinalArchitectureService(db).get_map(
        map_id=map_id,
        organisation_id=ctx.organisation.id,
    )
    if report is None:
        raise HTTPException(status_code=404, detail="Architecture map not found")
    return _to_response(report)
