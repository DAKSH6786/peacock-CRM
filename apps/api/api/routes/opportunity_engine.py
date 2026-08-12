"""Peacock Opportunity Engine API — always-on ranked opportunities."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas_opportunity_engine import (
    EvidenceResponse,
    OpportunityCatalogResponse,
    OpportunityResponse,
    OpportunityScanRequest,
    OpportunityScanResponse,
    RankingFactorResponse,
    RankingWeightResponse,
    RecordOutcomeRequest,
)
from observability.audit import AuditEvent, AuditLogger
from opportunity_engine import (
    ALWAYS_ON_NOTE,
    DEFAULT_RANKING_WEIGHTS,
    METHODOLOGY,
    METHODOLOGY_NOTE,
    OPPORTUNITY_TYPES,
    RANKING_FEATURES,
    EvidenceInput,
    OpportunityEngineService,
    OpportunityScanSpec,
    OutcomeFeedbackInput,
    SignalInput,
    example_signals_catalog,
)

router = APIRouter(prefix="/opportunities", tags=["opportunities"])
audit_logger = AuditLogger()


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


def _to_response(report) -> OpportunityScanResponse:
    r = report.result
    return OpportunityScanResponse(
        scan_id=report.scan_id,
        name=report.name,
        client_brand=report.client_brand,
        methodology=report.methodology,
        always_on_layer=True,
        ranking_model_version=r.ranking_model_version,
        ranking_is_adaptive=r.ranking_is_adaptive,
        fixed_formula_rejected=True,
        always_on_note=r.always_on_note,
        methodology_note=r.methodology_note,
        summary=r.summary,
        ranking_weights=[RankingWeightResponse(**w.to_dict()) for w in r.ranking_weights],
        opportunities=[
            OpportunityResponse(
                opportunity_key=o.opportunity_key,
                opportunity_type=o.opportunity_type,
                title=o.title,
                description=o.description,
                impact=o.impact,
                urgency=o.urgency,
                confidence=o.confidence,
                difficulty=o.difficulty,
                expected_value=o.expected_value,
                recommended_action=o.recommended_action,
                evidence=[EvidenceResponse(**e.to_dict()) for e in o.evidence],
                rank=o.rank,
                opportunity_score=o.opportunity_score,
                ranking_explanation=o.ranking_explanation,
                ranking_factors=[
                    RankingFactorResponse(**f.to_dict()) for f in o.ranking_factors
                ],
                related_entity=o.related_entity,
                related_url=o.related_url,
            )
            for o in r.opportunities
        ],
    )


@router.get("/catalog", response_model=OpportunityCatalogResponse)
def opportunities_catalog(
    ctx: AuthContext = Depends(get_auth_context),
) -> OpportunityCatalogResponse:
    _ = ctx
    return OpportunityCatalogResponse(
        opportunity_types=list(OPPORTUNITY_TYPES),
        type_examples=example_signals_catalog(),
        ranking_features=list(RANKING_FEATURES),
        default_ranking_weights=dict(DEFAULT_RANKING_WEIGHTS),
        methodology=METHODOLOGY,
        methodology_note=METHODOLOGY_NOTE,
        always_on_note=ALWAYS_ON_NOTE,
        fixed_formula_rejected=True,
    )


@router.post("/scans", response_model=OpportunityScanResponse, status_code=201)
def create_opportunity_scan(
    body: OpportunityScanRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> OpportunityScanResponse:
    ws = _workspace_id(ctx, body.workspace_id)
    try:
        report = OpportunityEngineService(db).run_scan(
            organisation_id=ctx.organisation.id,
            workspace_id=ws,
            created_by=ctx.user.id,
            spec=OpportunityScanSpec(
                website_id=body.website_id,
                name=body.name,
                client_brand=body.client_brand,
                signals=[
                    SignalInput(
                        opportunity_type=s.opportunity_type,
                        title=s.title,
                        description=s.description,
                        impact=s.impact,
                        urgency=s.urgency,
                        confidence=s.confidence,
                        difficulty=s.difficulty,
                        expected_value=s.expected_value,
                        recommended_action=s.recommended_action,
                        evidence=[EvidenceInput(**e.model_dump()) for e in s.evidence],
                        related_entity=s.related_entity,
                        related_url=s.related_url,
                        opportunity_key=s.opportunity_key,
                    )
                    for s in body.signals
                ],
                outcome_feedback=[
                    OutcomeFeedbackInput(**f.model_dump()) for f in body.outcome_feedback
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
            action="opportunity_engine.scan",
            resource_type="opportunity_scan",
            resource_id=report.scan_id,
            workspace_id=ws,
            metadata={
                "opportunity_count": len(report.result.opportunities),
                "fixed_formula_rejected": True,
                "ranking_model_version": report.result.ranking_model_version,
            },
        )
    )
    return _to_response(report)


@router.get("/scans/{scan_id}", response_model=OpportunityScanResponse)
def get_opportunity_scan(
    scan_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> OpportunityScanResponse:
    report = OpportunityEngineService(db).get_scan(
        scan_id=scan_id,
        organisation_id=ctx.organisation.id,
    )
    if report is None:
        raise HTTPException(status_code=404, detail="Opportunity scan not found")
    return _to_response(report)


@router.post("/outcomes", status_code=201)
def record_opportunity_outcome(
    body: RecordOutcomeRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict:
    ws = _workspace_id(ctx, body.workspace_id)
    result = OpportunityEngineService(db).record_outcome(
        organisation_id=ctx.organisation.id,
        workspace_id=ws,
        website_id=body.website_id,
        created_by=ctx.user.id,
        feedback=OutcomeFeedbackInput(**body.feedback.model_dump()),
    )
    audit_logger.log(
        AuditEvent(
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            action="opportunity_engine.outcome",
            resource_type="po_outcome_feedback",
            resource_id=result["feedback_id"],
            workspace_id=ws,
            metadata={"opportunity_type": body.feedback.opportunity_type},
        )
    )
    return result
