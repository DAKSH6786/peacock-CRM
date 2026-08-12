"""Peacock Entity Intelligence API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas_entity_intelligence import (
    AssociationResponse,
    EntityGapResponse,
    EntityIntelligenceCatalogResponse,
    EntityIntelligenceRequest,
    EntityIntelligenceResponse,
    StrategyResponse,
)
from entity_intelligence import (
    ASSOCIATION_COMPONENTS,
    DEFAULT_ASSOCIATION_WEIGHTS,
    ENTITY_TYPES,
    STRATEGY_ACTIONS,
    EntityIntelligenceService,
)
from entity_intelligence.models import (
    AssociationInputSpec,
    EntityIntelligenceSpec,
    EntityNodeSpec,
)
from observability.audit import AuditEvent, AuditLogger

router = APIRouter(prefix="/entity-intelligence", tags=["entity-intelligence"])
audit_logger = AuditLogger()


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


def _assoc(a) -> AssociationResponse:
    return AssociationResponse(**a.to_dict())


def _to_response(report) -> EntityIntelligenceResponse:
    return EntityIntelligenceResponse(
        analysis_id=report.analysis_id,
        client_brand=report.client_brand,
        methodology=report.methodology,
        entity_count=report.entity_count,
        association_count=report.association_count,
        associations=[_assoc(a) for a in report.associations],
        client_ownership=[_assoc(a) for a in report.client_ownership],
        gaps=[EntityGapResponse(**g.to_dict()) for g in report.gaps],
        strategies=[StrategyResponse(**s.to_dict()) for s in report.strategies],
        association_weights=report.association_weights,
        example_ownership=report.example_ownership,
        example_gap=report.example_gap,
    )


@router.get("/catalog", response_model=EntityIntelligenceCatalogResponse)
def entity_intelligence_catalog(
    ctx: AuthContext = Depends(get_auth_context),
) -> EntityIntelligenceCatalogResponse:
    _ = ctx
    return EntityIntelligenceCatalogResponse(
        entity_types=list(ENTITY_TYPES),
        association_components=list(ASSOCIATION_COMPONENTS),
        default_weights=dict(DEFAULT_ASSOCIATION_WEIGHTS),
        strategy_actions=list(STRATEGY_ACTIONS),
        methodology_note=(
            "Entity Association Strength is a weighted multi-signal score "
            "(co-occurrence, semantic proximity, ownership, citation linkage, "
            "topical centrality, recency, cross-source consistency). "
            "Entity Gaps compare client vs competitor association to a target concept "
            "and generate strategy."
        ),
    )


@router.post("/analyses", response_model=EntityIntelligenceResponse, status_code=201)
def create_entity_intelligence_analysis(
    body: EntityIntelligenceRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> EntityIntelligenceResponse:
    ws = _workspace_id(ctx, body.workspace_id)
    try:
        report = EntityIntelligenceService(db).analyse(
            organisation_id=ctx.organisation.id,
            workspace_id=ws,
            created_by=ctx.user.id,
            spec=EntityIntelligenceSpec(
                website_id=body.website_id,
                name=body.name,
                client_brand=body.client_brand,
                industry=body.industry,
                entities=[EntityNodeSpec(**e.model_dump()) for e in body.entities],
                associations=[
                    AssociationInputSpec(**a.model_dump()) for a in body.associations
                ],
                target_concepts=body.target_concepts,
                notes=body.notes,
                association_weights=body.association_weights,
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_logger.log(
        AuditEvent(
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            action="entity_intelligence.analyse",
            resource_type="entity_intelligence_analysis",
            resource_id=report.analysis_id,
            workspace_id=ws,
            metadata={
                "client_brand": report.client_brand,
                "associations": report.association_count,
                "gaps": len(report.gaps),
            },
        )
    )
    return _to_response(report)


@router.get("/analyses/{analysis_id}", response_model=EntityIntelligenceResponse)
def get_entity_intelligence_analysis(
    analysis_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> EntityIntelligenceResponse:
    report = EntityIntelligenceService(db).get_report(
        analysis_id=analysis_id,
        organisation_id=ctx.organisation.id,
    )
    if report is None:
        raise HTTPException(status_code=404, detail="Entity Intelligence analysis not found")
    return _to_response(report)
