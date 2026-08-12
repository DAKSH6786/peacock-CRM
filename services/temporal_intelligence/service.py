"""Temporal Intelligence orchestration — persist Visibility Timeline."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from db_models.base import new_uuid
from db_models.temporal_intelligence import (
    METHODOLOGY,
    NOISE_GUARDRAIL,
    TemporalTimeline,
    TiChangePoint,
    TiQueryAnswer,
    TiTimelineEvent,
)
from temporal_intelligence.analysis import (
    ChangePointResult,
    EventResult,
    QueryAnswerResult,
    TimelineAnalysisResult,
    analyse_timeline,
)
from temporal_intelligence.models import (
    TemporalIntelligenceReport,
    TemporalIntelligenceSpec,
)


class TemporalIntelligenceService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def analyse(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        spec: TemporalIntelligenceSpec,
        created_by: str | None = None,
    ) -> TemporalIntelligenceReport:
        result = analyse_timeline(spec.timeline)

        timeline = TemporalTimeline(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            website_id=spec.website_id,
            name=spec.name,
            client_brand=spec.timeline.client_brand.strip(),
            window_start=result.window_start,
            window_end=result.window_end,
            analysis_status="completed",
            methodology=METHODOLOGY,
            noise_guardrail=NOISE_GUARDRAIL,
            events_count=result.events_count,
            change_points_count=result.change_points_count,
            alerts_suppressed=result.alerts_suppressed,
            summary=result.summary,
            notes=spec.notes,
        )
        self.db.add(timeline)
        self.db.flush()

        event_ids: list[str] = []
        for e in result.events:
            eid = new_uuid()
            event_ids.append(eid)
            e.event_id = eid
            self.db.add(
                TiTimelineEvent(
                    id=eid,
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    timeline_id=timeline.id,
                    event_kind=e.event_kind,
                    event_label=e.event_label,
                    occurred_at=e.occurred_at,
                    title=e.title,
                    detail=e.detail,
                    magnitude=e.magnitude,
                    direction=e.direction,
                    metric_key=e.metric_key,
                    metric_value=e.metric_value,
                    source_ref=e.source_ref,
                )
            )

        for cp in result.change_points:
            self.db.add(
                TiChangePoint(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    timeline_id=timeline.id,
                    metric_key=cp.metric_key,
                    detected_at=cp.detected_at,
                    score=cp.score,
                    effect_size=cp.effect_size,
                    baseline_mean=cp.baseline_mean,
                    baseline_std=cp.baseline_std,
                    post_mean=cp.post_mean,
                    is_alert=cp.is_alert,
                    suppressed_as_noise=cp.suppressed_as_noise,
                    rationale=cp.rationale,
                )
            )

        for qa in result.query_answers:
            supporting = ",".join(
                event_ids[i]
                for i in qa.supporting_event_indexes
                if 0 <= i < len(event_ids)
            )
            self.db.add(
                TiQueryAnswer(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    timeline_id=timeline.id,
                    intent=qa.intent,
                    question=qa.question,
                    answer=qa.answer,
                    supporting_event_ids=supporting or None,
                    confidence=qa.confidence,
                )
            )

        self.db.commit()
        return TemporalIntelligenceReport(
            timeline_id=timeline.id,
            name=timeline.name,
            client_brand=timeline.client_brand,
            methodology=timeline.methodology,
            result=result,
        )

    def get_timeline(
        self, *, timeline_id: str, organisation_id: str
    ) -> TemporalIntelligenceReport | None:
        timeline = self.db.scalar(
            select(TemporalTimeline).where(
                TemporalTimeline.id == timeline_id,
                TemporalTimeline.organisation_id == organisation_id,
            )
        )
        if timeline is None:
            return None

        event_rows = list(
            self.db.scalars(
                select(TiTimelineEvent)
                .where(TiTimelineEvent.timeline_id == timeline.id)
                .order_by(TiTimelineEvent.occurred_at.asc())
            ).all()
        )
        events = [
            EventResult(
                event_kind=e.event_kind,
                event_label=e.event_label,
                occurred_at=e.occurred_at,
                title=e.title,
                detail=e.detail,
                magnitude=e.magnitude,
                direction=e.direction,
                metric_key=e.metric_key,
                metric_value=e.metric_value,
                source_ref=e.source_ref,
                event_id=e.id,
            )
            for e in event_rows
        ]
        cps = [
            ChangePointResult(
                metric_key=c.metric_key,
                detected_at=c.detected_at,
                score=c.score,
                effect_size=c.effect_size,
                baseline_mean=c.baseline_mean,
                baseline_std=c.baseline_std,
                post_mean=c.post_mean,
                is_alert=c.is_alert,
                suppressed_as_noise=c.suppressed_as_noise,
                rationale=c.rationale,
            )
            for c in self.db.scalars(
                select(TiChangePoint).where(TiChangePoint.timeline_id == timeline.id)
            ).all()
        ]
        id_to_idx = {e.id: i for i, e in enumerate(event_rows)}
        answers = []
        for q in self.db.scalars(
            select(TiQueryAnswer).where(TiQueryAnswer.timeline_id == timeline.id)
        ).all():
            idxs = []
            for eid in (q.supporting_event_ids or "").split(","):
                if eid and eid in id_to_idx:
                    idxs.append(id_to_idx[eid])
            answers.append(
                QueryAnswerResult(
                    intent=q.intent,
                    question=q.question,
                    answer=q.answer,
                    supporting_event_indexes=idxs,
                    confidence=q.confidence,
                )
            )

        from db_models.temporal_intelligence import METHODOLOGY_NOTE

        result = TimelineAnalysisResult(
            window_start=timeline.window_start,
            window_end=timeline.window_end,
            events=events,
            change_points=cps,
            query_answers=answers,
            events_count=timeline.events_count,
            change_points_count=timeline.change_points_count,
            alerts_suppressed=timeline.alerts_suppressed,
            noise_guardrail=timeline.noise_guardrail,
            methodology_note=METHODOLOGY_NOTE,
            summary=timeline.summary or "",
        )
        return TemporalIntelligenceReport(
            timeline_id=timeline.id,
            name=timeline.name,
            client_brand=timeline.client_brand,
            methodology=timeline.methodology,
            result=result,
        )
