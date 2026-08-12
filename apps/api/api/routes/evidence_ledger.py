"""Evidence Ledger API — Evidence → Finding → Recommendation → Action → Outcome."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas_evidence_ledger import (
    ClaimEvidenceRequest,
    EvidenceGraphResponse,
    LedgerActionRequest,
    LedgerEvidenceRequest,
    LedgerFindingRequest,
    LedgerNodeResponse,
    LedgerOutcomeRequest,
    LedgerRecommendationRequest,
)
from evidence_ledger import (
    ClaimEvidencePointer,
    EvidenceLedgerRepository,
    EvidenceType,
    LedgerActionNode,
    LedgerEvidenceNode,
    LedgerFindingNode,
    LedgerOutcomeNode,
    LedgerRecommendationNode,
    SupportingValue,
)
from observability.audit import AuditEvent, AuditLogger

router = APIRouter(prefix="/evidence-ledger", tags=["evidence-ledger"])
audit_logger = AuditLogger()


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


@router.get("/types")
def list_evidence_types(ctx: AuthContext = Depends(get_auth_context)) -> dict:
    return {"evidence_types": [item.value for item in EvidenceType]}


@router.post("/evidences", response_model=LedgerNodeResponse, status_code=201)
def create_evidence(
    body: LedgerEvidenceRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> LedgerNodeResponse:
    workspace_id = _workspace_id(ctx, body.workspace_id)
    try:
        evidence_type = EvidenceType(body.evidence_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid evidence_type: {body.evidence_type}") from exc

    node = EvidenceLedgerRepository(db).record_evidence(
        organisation_id=ctx.organisation.id,
        workspace_id=workspace_id,
        node=LedgerEvidenceNode(
            evidence_type=evidence_type,
            source=body.source,
            observed_at=body.observed_at or datetime.now().astimezone(),
            confidence=body.confidence,
            scope_kind=body.scope_kind,
            scope_ref=body.scope_ref,
            summary=body.summary,
            code=body.code,
            freshness_hours=body.freshness_hours,
            freshness_score=body.freshness_score,
            supporting_value=SupportingValue(
                text=body.supporting_value_text,
                number=body.supporting_value_number,
                boolean=body.supporting_value_bool,
                unit=body.supporting_value_unit,
            ),
            source_url=body.source_url,
            website_id=body.website_id,
            crawl_id=body.crawl_id,
            intelligence_case_id=body.intelligence_case_id,
        ),
    )
    audit_logger.log(
        AuditEvent(
            organisation_id=ctx.organisation.id,
            actor_user_id=ctx.user.id,
            action="evidence_ledger.evidence.create",
            resource_type="ledger_evidence",
            resource_id=node.id or "",
            workspace_id=workspace_id,
            metadata={"evidence_type": str(node.evidence_type), "source": node.source},
        )
    )
    return LedgerNodeResponse(node=node.to_dict())


@router.post("/findings", response_model=LedgerNodeResponse, status_code=201)
def create_finding(
    body: LedgerFindingRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> LedgerNodeResponse:
    workspace_id = _workspace_id(ctx, body.workspace_id)
    node = EvidenceLedgerRepository(db).record_finding(
        organisation_id=ctx.organisation.id,
        workspace_id=workspace_id,
        node=LedgerFindingNode(
            statement=body.statement,
            confidence=body.confidence,
            code=body.code,
            summary=body.summary,
            finding_kind=body.finding_kind,
            agent_name=body.agent_name,
            is_llm_derived=body.is_llm_derived,
            severity=body.severity,
            website_id=body.website_id,
            intelligence_case_id=body.intelligence_case_id,
            evidence_ids=body.evidence_ids,
        ),
        evidence_ids=body.evidence_ids,
    )
    return LedgerNodeResponse(node=node.to_dict())


@router.post("/recommendations", response_model=LedgerNodeResponse, status_code=201)
def create_recommendation(
    body: LedgerRecommendationRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> LedgerNodeResponse:
    workspace_id = _workspace_id(ctx, body.workspace_id)
    node = EvidenceLedgerRepository(db).record_recommendation(
        organisation_id=ctx.organisation.id,
        workspace_id=workspace_id,
        node=LedgerRecommendationNode(
            title=body.title,
            rationale=body.rationale,
            priority=body.priority,
            impact=body.impact,
            effort=body.effort,
            confidence=body.confidence,
            code=body.code,
            priority_score=body.priority_score,
            suggested_fix=body.suggested_fix,
            website_id=body.website_id,
            central_recommendation_id=body.central_recommendation_id,
            intelligence_case_id=body.intelligence_case_id,
            finding_ids=body.finding_ids,
        ),
        finding_ids=body.finding_ids,
    )
    return LedgerNodeResponse(node=node.to_dict())


@router.post("/actions", response_model=LedgerNodeResponse, status_code=201)
def create_action(
    body: LedgerActionRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> LedgerNodeResponse:
    workspace_id = _workspace_id(ctx, body.workspace_id)
    node = EvidenceLedgerRepository(db).record_action(
        organisation_id=ctx.organisation.id,
        workspace_id=workspace_id,
        node=LedgerActionNode(
            title=body.title,
            description=body.description,
            code=body.code,
            owner_role=body.owner_role,
            success_metric=body.success_metric,
            action_status=body.action_status,
            due_at=body.due_at,
            website_id=body.website_id,
            roadmap_task_id=body.roadmap_task_id,
            execution_id=body.execution_id,
            recommendation_ids=body.recommendation_ids,
        ),
        recommendation_ids=body.recommendation_ids,
    )
    return LedgerNodeResponse(node=node.to_dict())


@router.post("/outcomes", response_model=LedgerNodeResponse, status_code=201)
def create_outcome(
    body: LedgerOutcomeRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> LedgerNodeResponse:
    workspace_id = _workspace_id(ctx, body.workspace_id)
    node = EvidenceLedgerRepository(db).record_outcome(
        organisation_id=ctx.organisation.id,
        workspace_id=workspace_id,
        node=LedgerOutcomeNode(
            metric_key=body.metric_key,
            metric_value=body.metric_value,
            observed_at=body.observed_at or datetime.now().astimezone(),
            code=body.code,
            baseline_value=body.baseline_value,
            target_value=body.target_value,
            notes=body.notes,
            outcome_kind=body.outcome_kind,
            website_id=body.website_id,
            central_outcome_id=body.central_outcome_id,
            action_ids=body.action_ids,
        ),
        action_ids=body.action_ids,
    )
    return LedgerNodeResponse(node=node.to_dict())


@router.post("/claim-links", response_model=LedgerNodeResponse, status_code=201)
def link_claim(
    body: ClaimEvidenceRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> LedgerNodeResponse:
    workspace_id = _workspace_id(ctx, body.workspace_id)
    pointer = EvidenceLedgerRepository(db).link_claim_to_evidence(
        organisation_id=ctx.organisation.id,
        workspace_id=workspace_id,
        pointer=ClaimEvidencePointer(
            claim_kind=body.claim_kind,
            claim_ref=body.claim_ref,
            evidence_id=body.evidence_id,
            claim_text=body.claim_text,
            role=body.role,
            confidence=body.confidence,
        ),
    )
    return LedgerNodeResponse(node=pointer.to_dict())


@router.get("/graph", response_model=EvidenceGraphResponse)
def get_workspace_graph(
    workspace_id: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> EvidenceGraphResponse:
    ws = _workspace_id(ctx, workspace_id)
    graph = EvidenceLedgerRepository(db).get_graph_for_workspace(
        organisation_id=ctx.organisation.id,
        workspace_id=ws,
        limit=limit,
    )
    return EvidenceGraphResponse(**graph.to_dict())


@router.get("/trace/{evidence_id}", response_model=EvidenceGraphResponse)
def trace_evidence_chain(
    evidence_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> EvidenceGraphResponse:
    graph = EvidenceLedgerRepository(db).trace_from_evidence(evidence_id)
    if graph is None or graph.organisation_id != ctx.organisation.id:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return EvidenceGraphResponse(**graph.to_dict())
