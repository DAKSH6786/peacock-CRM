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
    detect_and_rank,
    example_signals_catalog,
)

router = APIRouter(prefix="/opportunities", tags=["opportunities"])
audit_logger = AuditLogger()


def _preview_signals() -> list[SignalInput]:
    """Example keyword & backlink opportunity signals for the public preview."""
    return [
        SignalInput(
            opportunity_type="high_value_topic_available",
            title="'AI visibility monitoring' keyword cluster is underserved",
            description=(
                "Search demand for 'AI visibility monitoring' and related keywords rose "
                "34% quarter-over-quarter with no dominant ranking page in the niche."
            ),
            impact=82.0,
            urgency=70.0,
            confidence=76.0,
            difficulty=38.0,
            expected_value=88.0,
            recommended_action=(
                "Brief and publish a pillar guide targeting the keyword cluster, "
                "supported by 3 linked cluster pages."
            ),
            evidence=[
                EvidenceInput(
                    evidence_type="keyword_demand",
                    statement="Search volume for the cluster rose 34% QoQ across 12 tracked keywords.",
                    strength=80.0,
                )
            ],
            related_entity="AI visibility monitoring",
        ),
        SignalInput(
            opportunity_type="backlink_source_gained_influence",
            title="Referring domain 'martech-review.com' gained authority",
            description=(
                "A previously low-authority review site jumped in domain authority after a "
                "funding announcement and now ranks for high-intent comparison queries."
            ),
            impact=68.0,
            urgency=55.0,
            confidence=64.0,
            difficulty=45.0,
            expected_value=70.0,
            recommended_action=(
                "Pursue an ethical placement (comparison listing or guest data) on the "
                "newly-influential referring domain."
            ),
            evidence=[
                EvidenceInput(
                    evidence_type="backlink_signal",
                    statement="martech-review.com domain authority increased and now sends referral traffic to 2 competitors.",
                    strength=62.0,
                )
            ],
            related_entity="martech-review.com",
        ),
        SignalInput(
            opportunity_type="competitor_content_outdated",
            title="Top-ranking competitor guide on 'backlink audits' is 3 years old",
            description=(
                "The #1 ranking page for 'backlink audit checklist' has not been updated since "
                "2021 and omits AI-citation considerations."
            ),
            impact=74.0,
            urgency=60.0,
            confidence=71.0,
            difficulty=42.0,
            expected_value=76.0,
            recommended_action=(
                "Publish an updated, higher information-gain backlink audit guide that "
                "covers AI-citation backlinks."
            ),
            evidence=[
                EvidenceInput(
                    evidence_type="competitor_content",
                    statement="Competitor page last modified 2021-03; missing AI-citation coverage.",
                    strength=68.0,
                )
            ],
            related_entity="backlink audit checklist",
        ),
        SignalInput(
            opportunity_type="existing_article_decaying",
            title="'Best SEO tools' article traffic decayed 22% in 90 days",
            description=(
                "An existing high-value article is losing organic traffic and keyword "
                "rankings versus 90 days ago."
            ),
            impact=58.0,
            urgency=64.0,
            confidence=69.0,
            difficulty=30.0,
            expected_value=60.0,
            recommended_action=(
                "Refresh evidence, entities, and internal links; re-promote the updated URL."
            ),
            evidence=[
                EvidenceInput(
                    evidence_type="traffic_signal",
                    statement="Organic sessions down 22% and average position dropped from 4.2 to 7.8.",
                    strength=66.0,
                )
            ],
            related_entity="Best SEO tools",
        ),
    ]


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


@router.get("/preview", response_model=OpportunityScanResponse)
def opportunities_preview(brand: str = "Acme") -> OpportunityScanResponse:
    """Public demo scan for the Keyword & Backlink Recommendations module."""
    result = detect_and_rank(_preview_signals())
    r = result
    return OpportunityScanResponse(
        scan_id="preview",
        name=f"{brand} — Keyword & backlink opportunities (preview)",
        client_brand=brand,
        methodology=METHODOLOGY,
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
