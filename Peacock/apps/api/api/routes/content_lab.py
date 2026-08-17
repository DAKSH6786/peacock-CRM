"""Peacock Content Lab API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas_content_lab import (
    CitabilityComponentResponse,
    ContentLabCatalogResponse,
    ContentLabRequest,
    ContentLabResponse,
    InfoGainSignalResponse,
    ProposalScoreResponse,
)
from content_lab import (
    CITABILITY_COMPONENTS,
    CITABILITY_DISCLAIMER,
    INFO_GAIN_PENALTIES,
    INFO_GAIN_REWARDS,
    MOAT_FORMAT_PRIORS,
    OPPORTUNITY_DIMENSIONS,
    ContentLabService,
    ProposalInput,
)
from content_lab.models import ContentLabSpec
from observability.audit import AuditEvent, AuditLogger

router = APIRouter(prefix="/content-lab", tags=["content-lab"])
audit_logger = AuditLogger()


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


def _proposal(p) -> ProposalScoreResponse:
    return ProposalScoreResponse(
        title=p.title,
        slug=p.slug,
        content_format=p.content_format,
        angle=p.angle,
        target_url=p.target_url,
        lab_priority_score=p.lab_priority_score,
        opportunities=p.opportunities,
        information_gain_score=p.information_gain_score,
        content_moat_score=p.content_moat_score,
        generative_citability_score=p.generative_citability_score,
        info_gain_signals=[InfoGainSignalResponse(**s.to_dict()) for s in p.info_gain_signals],
        citability_components=[
            CitabilityComponentResponse(**c.to_dict()) for c in p.citability_components
        ],
        moat_rationale=p.moat_rationale,
        recommendation_summary=p.recommendation_summary,
        citability_is_proprietary_estimate=True,
        citability_disclaimer=p.citability_disclaimer,
    )


def _to_response(report) -> ContentLabResponse:
    return ContentLabResponse(
        analysis_id=report.analysis_id,
        client_brand=report.client_brand,
        methodology=report.methodology,
        citability_is_proprietary_estimate=True,
        citability_disclaimer=report.citability_disclaimer,
        proposals=[_proposal(p) for p in report.proposals],
        example_moat=report.example_moat,
        top_recommendation=report.top_recommendation,
    )


@router.get("/catalog", response_model=ContentLabCatalogResponse)
def content_lab_catalog(
    ctx: AuthContext = Depends(get_auth_context),
) -> ContentLabCatalogResponse:
    _ = ctx
    return ContentLabCatalogResponse(
        opportunity_dimensions=list(OPPORTUNITY_DIMENSIONS),
        info_gain_penalties=list(INFO_GAIN_PENALTIES),
        info_gain_rewards=list(INFO_GAIN_REWARDS),
        moat_format_priors=dict(MOAT_FORMAT_PRIORS),
        citability_components=list(CITABILITY_COMPONENTS),
        citability_disclaimer=CITABILITY_DISCLAIMER,
        methodology_note=(
            "Peacock Content Lab evaluates proposed content far beyond keywords: "
            "SEO/AEO/GEO/AI citation opportunity, business value, information gain, "
            "content moat, and generative citability (proprietary estimate, not a "
            "guaranteed third-party ranking factor)."
        ),
    )


@router.post("/analyses", response_model=ContentLabResponse, status_code=201)
def create_content_lab_analysis(
    body: ContentLabRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> ContentLabResponse:
    ws = _workspace_id(ctx, body.workspace_id)
    try:
        report = ContentLabService(db).analyse(
            organisation_id=ctx.organisation.id,
            workspace_id=ws,
            created_by=ctx.user.id,
            spec=ContentLabSpec(
                website_id=body.website_id,
                name=body.name,
                client_brand=body.client_brand,
                topic_cluster=body.topic_cluster,
                proposals=[ProposalInput(**p.model_dump()) for p in body.proposals],
                notes=body.notes,
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_logger.log(
        AuditEvent(
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            action="content_lab.analyse",
            resource_type="content_lab_analysis",
            resource_id=report.analysis_id,
            workspace_id=ws,
            metadata={
                "proposals": len(report.proposals),
                "citability_proprietary_estimate": True,
            },
        )
    )
    return _to_response(report)


@router.get("/analyses/{analysis_id}", response_model=ContentLabResponse)
def get_content_lab_analysis(
    analysis_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> ContentLabResponse:
    report = ContentLabService(db).get_report(
        analysis_id=analysis_id,
        organisation_id=ctx.organisation.id,
    )
    if report is None:
        raise HTTPException(status_code=404, detail="Content Lab analysis not found")
    return _to_response(report)
