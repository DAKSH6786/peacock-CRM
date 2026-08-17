"""Peacock Council 2.0 API — opposing-role debate, no CoT storage."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas_council2 import (
    AgentResponse,
    ClaimResponse,
    Council2CatalogResponse,
    Council2SessionRequest,
    Council2SessionResponse,
    CounterargumentResponse,
    DecisionResponse,
    DisagreementResponse,
    EvidenceRequestResponse,
    EvidenceResponse,
    RoundResponse,
)
from council2 import (
    COUNCIL_ROLES,
    DEBATE_ROUNDS,
    FORBIDDEN_PROMPTS,
    FORBIDDEN_STORAGE_FIELDS,
    METHODOLOGY,
    METHODOLOGY_NOTE,
    ROLE_MANDATES,
    STORED_ARTIFACT_KINDS,
    ContextFact,
    Council2Service,
    Council2Spec,
    CouncilBrief,
)
from observability.audit import AuditEvent, AuditLogger

router = APIRouter(prefix="/council2", tags=["council2"])
audit_logger = AuditLogger()


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


def _to_response(report) -> Council2SessionResponse:
    r = report.result
    return Council2SessionResponse(
        session_id=report.session_id,
        name=report.name,
        client_brand=report.client_brand,
        methodology=report.methodology,
        decision_question=r.decision_question,
        open_opinion_prompts_rejected=True,
        chain_of_thought_not_stored=True,
        stored_artifact_kinds=list(r.stored_artifact_kinds),
        methodology_note=r.methodology_note,
        summary=r.summary,
        final_decision=r.final_decision,
        final_confidence=r.final_confidence,
        agents=[AgentResponse(**a.to_dict()) for a in r.agents],
        rounds=[RoundResponse(**x.to_dict()) for x in r.rounds],
        claims=[ClaimResponse(**c.to_dict()) for c in r.claims],
        evidence=[EvidenceResponse(**e.to_dict()) for e in r.evidence],
        counterarguments=[CounterargumentResponse(**c.to_dict()) for c in r.counterarguments],
        disagreements=[DisagreementResponse(**d.to_dict()) for d in r.disagreements],
        evidence_requests=[
            EvidenceRequestResponse(**e.to_dict()) for e in r.evidence_requests
        ],
        decisions=[DecisionResponse(**d.to_dict()) for d in r.decisions],
    )


@router.get("/catalog", response_model=Council2CatalogResponse)
def council2_catalog(
    ctx: AuthContext = Depends(get_auth_context),
) -> Council2CatalogResponse:
    _ = ctx
    return Council2CatalogResponse(
        roles=list(COUNCIL_ROLES),
        role_mandates=dict(ROLE_MANDATES),
        debate_rounds=[
            {"round_number": n, "round_code": c, "round_label": l}
            for n, c, l in DEBATE_ROUNDS
        ],
        stored_artifact_kinds=list(STORED_ARTIFACT_KINDS),
        forbidden_prompts=list(FORBIDDEN_PROMPTS),
        forbidden_storage_fields=list(FORBIDDEN_STORAGE_FIELDS),
        methodology=METHODOLOGY,
        methodology_note=METHODOLOGY_NOTE,
        open_opinion_prompts_rejected=True,
        chain_of_thought_not_stored=True,
    )


@router.post("/sessions", response_model=Council2SessionResponse, status_code=201)
def create_council2_session(
    body: Council2SessionRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> Council2SessionResponse:
    ws = _workspace_id(ctx, body.workspace_id)
    try:
        report = Council2Service(db).run_session(
            organisation_id=ctx.organisation.id,
            workspace_id=ws,
            created_by=ctx.user.id,
            spec=Council2Spec(
                website_id=body.website_id,
                name=body.name,
                brief=CouncilBrief(
                    decision_question=body.brief.decision_question,
                    client_brand=body.brief.client_brand,
                    context_summary=body.brief.context_summary,
                    facts=[ContextFact(**f.model_dump()) for f in body.brief.facts],
                    options=list(body.brief.options),
                    model_by_role=dict(body.brief.model_by_role),
                    roles=list(body.brief.roles),
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
            action="council2.debate",
            resource_type="council2_session",
            resource_id=report.session_id,
            workspace_id=ws,
            metadata={
                "open_opinion_prompts_rejected": True,
                "chain_of_thought_not_stored": True,
                "final_confidence": report.result.final_confidence,
                "roles": len(report.result.agents),
            },
        )
    )
    return _to_response(report)


@router.get("/sessions/{session_id}", response_model=Council2SessionResponse)
def get_council2_session(
    session_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> Council2SessionResponse:
    report = Council2Service(db).get_session(
        session_id=session_id,
        organisation_id=ctx.organisation.id,
    )
    if report is None:
        raise HTTPException(status_code=404, detail="Council 2.0 session not found")
    return _to_response(report)
