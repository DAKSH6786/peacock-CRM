"""Probabilistic AI Visibility API — controlled repetitions, never single-shot truth."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas_visibility import (
    VisibilityCampaignRequest,
    VisibilityCampaignResponse,
    VisibilityScoreCardResponse,
)
from geo_engine import (
    CampaignSpec,
    GeoEngine,
    ProbeCellSpec,
    ProbabilisticVisibilityService,
    RateLimitPolicy,
)
from observability.audit import AuditEvent, AuditLogger

router = APIRouter(prefix="/visibility", tags=["probabilistic-ai-visibility"])
audit_logger = AuditLogger()


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


@router.get("/status")
def visibility_status(ctx: AuthContext = Depends(get_auth_context)) -> dict:
    return GeoEngine(ctx.organisation.id).status()


@router.post("/campaigns", response_model=VisibilityCampaignResponse, status_code=201)
def create_visibility_campaign(
    body: VisibilityCampaignRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> VisibilityCampaignResponse:
    ws = _workspace_id(ctx, body.workspace_id)
    try:
        campaign = ProbabilisticVisibilityService(db).create_campaign(
            organisation_id=ctx.organisation.id,
            workspace_id=ws,
            spec=CampaignSpec(
                website_id=body.website_id,
                name=body.name,
                brand_name=body.brand_name,
                competitors=body.competitors,
                notes=body.notes,
                rate_limit=RateLimitPolicy(**body.rate_limit.model_dump()),
                cells=[ProbeCellSpec(**cell.model_dump()) for cell in body.cells],
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_logger.log(
        AuditEvent(
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            action="visibility.campaign.create",
            resource_type="visibility_campaign",
            resource_id=campaign.id,
            workspace_id=ws,
            metadata={
                "cells": len(body.cells),
                "target_repetitions": campaign.target_repetitions,
                "single_shot_rejected": True,
            },
        )
    )
    return VisibilityCampaignResponse(
        campaign_id=campaign.id,
        status=campaign.campaign_status,
        brand_name=campaign.brand_name,
        target_repetitions=campaign.target_repetitions,
        rate_limit={
            "max_calls_per_minute": campaign.max_calls_per_minute,
            "max_concurrent": campaign.max_concurrent,
            "max_total_calls": campaign.max_total_calls,
            "min_interval_ms": campaign.min_interval_ms,
            "target_repetitions": campaign.target_repetitions,
            "max_repetitions": campaign.max_repetitions,
        },
        cell_count=len(body.cells),
        single_shot_rejected=True,
    )


@router.post("/campaigns/{campaign_id}/run", response_model=VisibilityScoreCardResponse)
async def run_visibility_campaign(
    campaign_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> VisibilityScoreCardResponse:
    try:
        card = await ProbabilisticVisibilityService(db).run_campaign(
            campaign_id=campaign_id,
            organisation_id=ctx.organisation.id,
            use_mock=True,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_logger.log(
        AuditEvent(
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            action="visibility.campaign.run",
            resource_type="visibility_campaign",
            resource_id=campaign_id,
            workspace_id=ctx.workspace.id if ctx.workspace else None,
            metadata={
                "observations": card.observation_count,
                "score": card.ai_visibility_score,
                "confidence": card.measurement_confidence,
            },
        )
    )
    return VisibilityScoreCardResponse(**card.to_dict())


@router.get("/campaigns/{campaign_id}/score", response_model=VisibilityScoreCardResponse)
def get_visibility_score(
    campaign_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> VisibilityScoreCardResponse:
    card = ProbabilisticVisibilityService(db).get_score_card(
        campaign_id=campaign_id,
        organisation_id=ctx.organisation.id,
    )
    if card is None:
        raise HTTPException(status_code=404, detail="Score card not found — run the campaign first")
    return VisibilityScoreCardResponse(**card.to_dict())
