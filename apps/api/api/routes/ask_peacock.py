"""Ask Peacock 2.0 API — NL interface over the intelligence graph."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ask_peacock import (
    AskPeacockService,
    AskPeacockSpec,
    AskSessionSpec,
    GraphSignal,
    catalog,
)
from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas_ask_peacock import (
    AskCatalogResponse,
    AskSessionRequest,
    AskSessionResponse,
    EvidenceResponse,
    StructuredAnswerResponse,
)
from observability.audit import AuditEvent, AuditLogger

router = APIRouter(prefix="/ask-peacock", tags=["ask-peacock"])
audit_logger = AuditLogger()


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


def _to_response(report) -> AskSessionResponse:
    r = report.result
    answers = []
    for a in r.answers:
        d = a.to_dict()
        answers.append(
            StructuredAnswerResponse(
                question_index=d["question_index"],
                question=d["question"],
                intent=d["intent"],
                intent_label=d["intent_label"],
                observed=d["observed"],
                inferred=d["inferred"],
                recommended=d["recommended"],
                forecast=d["forecast"],
                confidence=d["confidence"],
                confidence_rationale=d["confidence_rationale"],
                graph_surfaces_used=d["graph_surfaces_used"],
                answered_at=d["answered_at"],
                evidence=[EvidenceResponse(**e) for e in d["evidence"]],
                sections=d["sections"],
            )
        )
    return AskSessionResponse(
        session_id=report.session_id,
        name=report.name,
        client_brand=report.client_brand,
        methodology=report.methodology,
        questions_asked=r.questions_asked,
        answers_produced=r.answers_produced,
        evidence_items=r.evidence_items,
        mean_confidence=r.mean_confidence,
        primary_intent=r.primary_intent,
        methodology_note=r.methodology_note,
        summary=r.summary,
        answers=answers,
    )


@router.get("/catalog", response_model=AskCatalogResponse)
def ask_peacock_catalog(
    ctx: AuthContext = Depends(get_auth_context),
) -> AskCatalogResponse:
    _ = ctx
    return AskCatalogResponse(**catalog())


@router.post("/sessions", response_model=AskSessionResponse, status_code=201)
def create_ask_session(
    body: AskSessionRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> AskSessionResponse:
    ws = _workspace_id(ctx, body.workspace_id)
    try:
        report = AskPeacockService(db).ask(
            organisation_id=ctx.organisation.id,
            workspace_id=ws,
            created_by=ctx.user.id,
            spec=AskPeacockSpec(
                website_id=body.website_id,
                name=body.name,
                session=AskSessionSpec(
                    client_brand=body.brief.client_brand,
                    questions=list(body.brief.questions),
                    signals=[
                        GraphSignal(
                            surface=s.surface,
                            key=s.key,
                            value=s.value,
                            weight=s.weight,
                            ref_id=s.ref_id,
                        )
                        for s in body.brief.signals
                    ],
                    competitor_name=body.brief.competitor_name,
                    budget_amount=body.brief.budget_amount,
                    topic=body.brief.topic,
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
            action="ask_peacock.ask",
            resource_type="ask_peacock_session",
            resource_id=report.session_id,
            workspace_id=ws,
            metadata={
                "questions_asked": report.result.questions_asked,
                "primary_intent": report.result.primary_intent,
                "mean_confidence": report.result.mean_confidence,
            },
        )
    )
    return _to_response(report)


@router.get("/sessions/{session_id}", response_model=AskSessionResponse)
def get_ask_session(
    session_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> AskSessionResponse:
    report = AskPeacockService(db).get_session(
        session_id=session_id,
        organisation_id=ctx.organisation.id,
    )
    if report is None:
        raise HTTPException(status_code=404, detail="Ask Peacock session not found")
    return _to_response(report)
