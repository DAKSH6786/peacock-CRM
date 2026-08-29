"""Probabilistic AI Visibility API — controlled repetitions, never single-shot truth."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import AuthContext, get_auth_context, require_writer
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
from geo_engine.probabilistic_stats import (
    ai_visibility_score,
    bernoulli_estimate,
    engine_disagreement,
    peacock_visibility_confidence,
    temporal_volatility,
)
from observability.audit import AuditEvent, AuditLogger

router = APIRouter(prefix="/visibility", tags=["probabilistic-ai-visibility"])
audit_logger = AuditLogger()

# engine_code -> (brand_mention_successes, citation_successes, top3_successes, repetitions)
_PREVIEW_ENGINE_OBSERVATIONS: dict[str, tuple[int, int, int, int]] = {
    "openai": (8, 5, 6, 10),
    "anthropic": (7, 4, 5, 10),
    "google_ai_overviews": (6, 3, 4, 10),
    "perplexity": (9, 6, 7, 10),
}
_PREVIEW_PERIOD_PROBABILITIES: list[float] = [0.58, 0.63, 0.7, 0.72]
_PREVIEW_COMPETITOR_PROBABILITIES: dict[str, float] = {
    "competitor_a": 0.42,
    "competitor_b": 0.35,
}


class VisibilityRunRequest(BaseModel):
    use_mock: bool = Field(
        default=False,
        description=(
            "When false (default), probes run through LLMGateway VISIBILITY_PROBE. "
            "When true, use deterministic mock probes (tests / offline)."
        ),
    )


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


@router.get("/status")
def visibility_status(ctx: AuthContext = Depends(get_auth_context)) -> dict:
    return GeoEngine(ctx.organisation.id).status()


@router.get("/preview", response_model=VisibilityScoreCardResponse)
def visibility_preview(brand: str = "Acme") -> VisibilityScoreCardResponse:
    """Public demo AI Visibility scorecard from controlled repeated probes."""
    mention_estimates = {
        engine: bernoulli_estimate(mentions, reps)
        for engine, (mentions, _citations, _top3, reps) in _PREVIEW_ENGINE_OBSERVATIONS.items()
    }
    citation_estimates = {
        engine: bernoulli_estimate(citations, reps)
        for engine, (_mentions, citations, _top3, reps) in _PREVIEW_ENGINE_OBSERVATIONS.items()
    }
    top3_estimates = {
        engine: bernoulli_estimate(top3, reps)
        for engine, (_mentions, _citations, top3, reps) in _PREVIEW_ENGINE_OBSERVATIONS.items()
    }

    brand_mention_p = sum(e.probability for e in mention_estimates.values()) / len(mention_estimates)
    citation_p = sum(e.probability for e in citation_estimates.values()) / len(citation_estimates)
    top3_p = sum(e.probability for e in top3_estimates.values()) / len(top3_estimates)
    competitor_gap = max(0.0, brand_mention_p - max(_PREVIEW_COMPETITOR_PROBABILITIES.values(), default=0.0))

    score = ai_visibility_score(
        brand_mention_p=brand_mention_p,
        citation_p=citation_p,
        top3_p=top3_p,
        competitor_gap=competitor_gap,
    )

    disagreement = engine_disagreement([e.probability for e in mention_estimates.values()])
    volatility = temporal_volatility(_PREVIEW_PERIOD_PROBABILITIES)
    mean_variance = sum(e.variance for e in mention_estimates.values()) / len(mention_estimates)
    total_reps = sum(reps for *_ignored, reps in _PREVIEW_ENGINE_OBSERVATIONS.values())

    confidence_score, confidence_label = peacock_visibility_confidence(
        sample_size=total_reps,
        engine_count=len(_PREVIEW_ENGINE_OBSERVATIONS),
        prompt_count=len(_PREVIEW_ENGINE_OBSERVATIONS) * 3,
        period_count=len(_PREVIEW_PERIOD_PROBABILITIES),
        mean_variance=mean_variance,
        mean_engine_disagreement=disagreement,
        mean_temporal_volatility=volatility,
    )

    summary = (
        f"{brand} AI Visibility Score {score}/100 from {total_reps} controlled repetitions "
        f"across {len(_PREVIEW_ENGINE_OBSERVATIONS)} engines. Measurement confidence {confidence_label} "
        f"({confidence_score:.2f}). Never a single-shot measurement."
    )

    return VisibilityScoreCardResponse(
        ai_visibility_score=score,
        measurement_confidence=confidence_label,
        peacock_visibility_confidence=round(confidence_score, 3),
        based_on={
            "engines": len(_PREVIEW_ENGINE_OBSERVATIONS),
            "repetitions": total_reps,
            "periods": len(_PREVIEW_PERIOD_PROBABILITIES),
        },
        brand_mention_probability=round(brand_mention_p, 3),
        citation_probability=round(citation_p, 3),
        top3_recommendation_probability=round(top3_p, 3),
        competitor_probabilities=_PREVIEW_COMPETITOR_PROBABILITIES,
        distributions=[
            {
                "engine": engine,
                "brand_mention_probability": round(mention_estimates[engine].probability, 3),
                "citation_probability": round(citation_estimates[engine].probability, 3),
                "top3_probability": round(top3_estimates[engine].probability, 3),
                "repetitions": reps,
            }
            for engine, (_m, _c, _t, reps) in _PREVIEW_ENGINE_OBSERVATIONS.items()
        ],
        summary=summary,
        computed_at=None,
        single_shot_rejected=True,
        defensible=confidence_label in {"HIGH", "MEDIUM"},
        probe_mode="mock_deterministic",
    )


@router.post("/campaigns", response_model=VisibilityCampaignResponse, status_code=201)
def create_visibility_campaign(
    body: VisibilityCampaignRequest,
    ctx: AuthContext = Depends(require_writer),
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
    request: Request,
    body: VisibilityRunRequest | None = None,
    ctx: AuthContext = Depends(require_writer),
    db: Session = Depends(get_db),
) -> VisibilityScoreCardResponse:
    use_mock = bool(body.use_mock) if body is not None else False
    gateway = None if use_mock else getattr(request.app.state, "llm_gateway", None)
    try:
        card = await ProbabilisticVisibilityService(db).run_campaign(
            campaign_id=campaign_id,
            organisation_id=ctx.organisation.id,
            use_mock=use_mock,
            gateway=gateway,
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
                "probe_mode": card.probe_mode,
                "use_mock": use_mock,
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
