"""Peacock Judge 2.0 API — deterministic multi-signal judgment."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas_judge2 import (
    EvidenceResponse,
    Judge2CatalogResponse,
    Judge2Request,
    Judge2Response,
    ReversalConditionResponse,
    SignalScoreResponse,
)
from judge2 import (
    DEFAULT_JUDGE_WEIGHTS,
    JUDGE_SIGNAL_FAMILIES,
    METHODOLOGY,
    METHODOLOGY_NOTE,
    SCORING_OUTSIDE_LLM,
    EvidenceInput,
    Judge2Service,
    Judge2Spec,
    JudgeBrief,
    ReversalConditionInput,
)
from observability.audit import AuditEvent, AuditLogger

router = APIRouter(prefix="/judge2", tags=["judge2"])
audit_logger = AuditLogger()


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


def _to_response(report) -> Judge2Response:
    r = report.result
    return Judge2Response(
        judgment_id=report.judgment_id,
        name=report.name,
        client_brand=report.client_brand,
        decision_question=report.decision_question,
        methodology=report.methodology,
        scoring_outside_llm=True,
        scoring_note=r.scoring_note,
        methodology_note=r.methodology_note,
        recommended_action=r.recommended_action,
        why=r.why,
        evidence=[EvidenceResponse(**e.to_dict()) for e in r.evidence],
        expected_upside=r.expected_upside,
        expected_upside_score=r.expected_upside_score,
        risk_summary=r.risk_summary,
        risk_score=r.risk_score,
        confidence=r.confidence,
        alternative=r.alternative,
        what_would_change_decision=r.what_would_change_decision,
        reversal_conditions=[
            ReversalConditionResponse(**x.to_dict()) for x in r.reversal_conditions
        ],
        signal_scores=[SignalScoreResponse(**s.to_dict()) for s in r.signal_scores],
        composite_score=r.composite_score,
        action_code=r.action_code,
        summary=r.summary,
    )


@router.get("/catalog", response_model=Judge2CatalogResponse)
def judge2_catalog(
    ctx: AuthContext = Depends(get_auth_context),
) -> Judge2CatalogResponse:
    _ = ctx
    return Judge2CatalogResponse(
        signal_families=list(JUDGE_SIGNAL_FAMILIES),
        default_weights=dict(DEFAULT_JUDGE_WEIGHTS),
        methodology=METHODOLOGY,
        methodology_note=METHODOLOGY_NOTE,
        scoring_outside_llm=True,
        scoring_note=SCORING_OUTSIDE_LLM,
        output_fields=[
            "recommended_action",
            "why",
            "evidence",
            "expected_upside",
            "risk",
            "confidence",
            "alternative",
            "what_would_change_decision",
        ],
        example_reversal_conditions=[
            "If keyword demand declines >40%, re-evaluate.",
            "If Competitor A loses citation dominance, re-evaluate.",
        ],
    )


@router.post("/judgments", response_model=Judge2Response, status_code=201)
def create_judge2_judgment(
    body: Judge2Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> Judge2Response:
    ws = _workspace_id(ctx, body.workspace_id)
    try:
        report = Judge2Service(db).judge(
            organisation_id=ctx.organisation.id,
            workspace_id=ws,
            created_by=ctx.user.id,
            spec=Judge2Spec(
                website_id=body.website_id,
                name=body.name,
                brief=JudgeBrief(
                    decision_question=body.brief.decision_question,
                    client_brand=body.brief.client_brand,
                    signals=dict(body.brief.signals),
                    evidence=[EvidenceInput(**e.model_dump()) for e in body.brief.evidence],
                    reversal_conditions=[
                        ReversalConditionInput(**r.model_dump())
                        for r in body.brief.reversal_conditions
                    ],
                    business_goal_summary=body.brief.business_goal_summary,
                    alternative_hint=body.brief.alternative_hint,
                    council2_session_id=body.brief.council2_session_id,
                    custom_weights=body.brief.custom_weights,
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
            action="judge2.judge",
            resource_type="judge2_judgment",
            resource_id=report.judgment_id,
            workspace_id=ws,
            metadata={
                "scoring_outside_llm": True,
                "action_code": report.result.action_code,
                "composite_score": report.result.composite_score,
                "reversal_conditions": len(report.result.reversal_conditions),
            },
        )
    )
    return _to_response(report)


@router.get("/judgments/{judgment_id}", response_model=Judge2Response)
def get_judge2_judgment(
    judgment_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> Judge2Response:
    report = Judge2Service(db).get_judgment(
        judgment_id=judgment_id,
        organisation_id=ctx.organisation.id,
    )
    if report is None:
        raise HTTPException(status_code=404, detail="Judge 2.0 judgment not found")
    return _to_response(report)
