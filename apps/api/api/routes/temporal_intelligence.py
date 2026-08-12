"""Peacock Temporal Intelligence API — Visibility Timeline + change points."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas_temporal_intelligence import (
    ChangePointResponse,
    EventResponse,
    QueryAnswerResponse,
    TemporalCatalogResponse,
    TemporalTimelineRequest,
    TemporalTimelineResponse,
)
from observability.audit import AuditEvent, AuditLogger
from temporal_intelligence import (
    MetricSeries,
    MetricSeriesPoint,
    TemporalIntelligenceService,
    TemporalIntelligenceSpec,
    TimelineEventInput,
    TimelineSpec,
    catalog,
)

router = APIRouter(prefix="/temporal", tags=["temporal"])
audit_logger = AuditLogger()


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


def _to_response(report) -> TemporalTimelineResponse:
    r = report.result
    return TemporalTimelineResponse(
        timeline_id=report.timeline_id,
        name=report.name,
        client_brand=report.client_brand,
        methodology=report.methodology,
        window_start=r.window_start.isoformat(),
        window_end=r.window_end.isoformat(),
        events=[EventResponse(**e.to_dict()) for e in r.events],
        change_points=[ChangePointResponse(**c.to_dict()) for c in r.change_points],
        query_answers=[QueryAnswerResponse(**q.to_dict()) for q in r.query_answers],
        events_count=r.events_count,
        change_points_count=r.change_points_count,
        alerts_suppressed=r.alerts_suppressed,
        noise_guardrail=r.noise_guardrail,
        methodology_note=r.methodology_note,
        summary=r.summary,
    )


@router.get("/catalog", response_model=TemporalCatalogResponse)
def temporal_catalog(
    ctx: AuthContext = Depends(get_auth_context),
) -> TemporalCatalogResponse:
    _ = ctx
    return TemporalCatalogResponse(**catalog())


@router.post("/timelines", response_model=TemporalTimelineResponse, status_code=201)
def create_temporal_timeline(
    body: TemporalTimelineRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> TemporalTimelineResponse:
    ws = _workspace_id(ctx, body.workspace_id)
    try:
        report = TemporalIntelligenceService(db).analyse(
            organisation_id=ctx.organisation.id,
            workspace_id=ws,
            created_by=ctx.user.id,
            spec=TemporalIntelligenceSpec(
                website_id=body.website_id,
                name=body.name,
                timeline=TimelineSpec(
                    client_brand=body.brief.client_brand,
                    window_start=body.brief.window_start,
                    window_end=body.brief.window_end,
                    events=[
                        TimelineEventInput(**e.model_dump()) for e in body.brief.events
                    ],
                    series=[
                        MetricSeries(
                            metric_key=s.metric_key,
                            points=[
                                MetricSeriesPoint(**p.model_dump()) for p in s.points
                            ],
                        )
                        for s in body.brief.series
                    ],
                    questions=list(body.brief.questions),
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
            action="temporal.analyse",
            resource_type="temporal_timeline",
            resource_id=report.timeline_id,
            workspace_id=ws,
            metadata={
                "events_count": report.result.events_count,
                "change_points_count": report.result.change_points_count,
                "alerts_suppressed": report.result.alerts_suppressed,
            },
        )
    )
    return _to_response(report)


@router.get("/timelines/{timeline_id}", response_model=TemporalTimelineResponse)
def get_temporal_timeline(
    timeline_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> TemporalTimelineResponse:
    report = TemporalIntelligenceService(db).get_timeline(
        timeline_id=timeline_id,
        organisation_id=ctx.organisation.id,
    )
    if report is None:
        raise HTTPException(status_code=404, detail="Timeline not found")
    return _to_response(report)
