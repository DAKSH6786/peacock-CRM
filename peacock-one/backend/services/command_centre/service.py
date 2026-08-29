"""Command Centre orchestration — persist flagship snapshot."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from command_centre.assembly import (
    CommandCentreResult,
    FeedItemResult,
    SituationResult,
    VisibilitySignalResult,
    assemble_command_centre,
)
from command_centre.models import CommandCentreCreateSpec, CommandCentreReport
from db_models.base import new_uuid
from db_models.command_centre import (
    METHODOLOGY,
    METHODOLOGY_NOTE,
    CcFeedItem,
    CcSituationItem,
    CcVisibilitySignal,
    CommandCentreSnapshot,
)


class CommandCentreService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_snapshot(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        spec: CommandCentreCreateSpec,
        created_by: str | None = None,
    ) -> CommandCentreReport:
        result = assemble_command_centre(spec.centre)

        snap = CommandCentreSnapshot(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            website_id=spec.website_id,
            name=spec.name,
            client_brand=result.client_brand,
            snapshot_status="completed",
            methodology=METHODOLOGY,
            visibility_index=result.visibility_index,
            visibility_delta=result.visibility_delta,
            captured_at=result.captured_at,
            headline=result.headline,
            summary=result.summary,
            notes=spec.notes,
        )
        self.db.add(snap)
        self.db.flush()

        for s in result.signals:
            self.db.add(
                CcVisibilitySignal(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    snapshot_id=snap.id,
                    dimension=s.dimension,
                    label=s.label,
                    score=s.score,
                    delta=s.delta,
                    rank_order=s.rank_order,
                )
            )
        for s in result.situations:
            self.db.add(
                CcSituationItem(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    snapshot_id=snap.id,
                    kind=s.kind,
                    label=s.label,
                    title=s.title,
                    detail=s.detail,
                    severity=s.severity,
                    rank_order=s.rank_order,
                )
            )
        for f in result.feed_items:
            self.db.add(
                CcFeedItem(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    snapshot_id=snap.id,
                    feed_index=f.feed_index,
                    detection_label=f.detection_label,
                    headline=f.headline,
                    body=f.body,
                    primary_driver=f.primary_driver,
                    potential_response=f.potential_response,
                    confidence=f.confidence,
                    detected_at=f.detected_at,
                    graph_surface=f.graph_surface,
                )
            )

        self.db.commit()
        return CommandCentreReport(
            snapshot_id=snap.id,
            name=snap.name,
            client_brand=snap.client_brand,
            methodology=snap.methodology,
            result=result,
        )

    def get_snapshot(
        self, *, snapshot_id: str, organisation_id: str
    ) -> CommandCentreReport | None:
        snap = self.db.scalar(
            select(CommandCentreSnapshot).where(
                CommandCentreSnapshot.id == snapshot_id,
                CommandCentreSnapshot.organisation_id == organisation_id,
            )
        )
        if snap is None:
            return None
        return self._to_report(snap)

    def latest_for_website(
        self, *, website_id: str, organisation_id: str
    ) -> CommandCentreReport | None:
        snap = self.db.scalar(
            select(CommandCentreSnapshot)
            .where(
                CommandCentreSnapshot.website_id == website_id,
                CommandCentreSnapshot.organisation_id == organisation_id,
            )
            .order_by(CommandCentreSnapshot.captured_at.desc())
            .limit(1)
        )
        if snap is None:
            return None
        return self._to_report(snap)

    def _to_report(self, snap: CommandCentreSnapshot) -> CommandCentreReport:
        signals = [
            VisibilitySignalResult(
                dimension=s.dimension,
                label=s.label,
                score=s.score,
                delta=s.delta,
                rank_order=s.rank_order,
            )
            for s in self.db.scalars(
                select(CcVisibilitySignal)
                .where(CcVisibilitySignal.snapshot_id == snap.id)
                .order_by(CcVisibilitySignal.rank_order.asc())
            ).all()
        ]
        situations = [
            SituationResult(
                kind=s.kind,
                label=s.label,
                title=s.title,
                detail=s.detail,
                severity=s.severity,
                rank_order=s.rank_order,
            )
            for s in self.db.scalars(
                select(CcSituationItem)
                .where(CcSituationItem.snapshot_id == snap.id)
                .order_by(CcSituationItem.rank_order.asc())
            ).all()
        ]
        feed_items = [
            FeedItemResult(
                feed_index=f.feed_index,
                detection_label=f.detection_label,
                headline=f.headline,
                body=f.body,
                primary_driver=f.primary_driver,
                potential_response=f.potential_response,
                confidence=f.confidence,
                detected_at=f.detected_at,
                graph_surface=f.graph_surface,
            )
            for f in self.db.scalars(
                select(CcFeedItem)
                .where(CcFeedItem.snapshot_id == snap.id)
                .order_by(CcFeedItem.feed_index.asc())
            ).all()
        ]
        result = CommandCentreResult(
            client_brand=snap.client_brand,
            visibility_index=snap.visibility_index,
            visibility_delta=snap.visibility_delta,
            captured_at=snap.captured_at,
            headline=snap.headline,
            signals=signals,
            situations=situations,
            feed_items=feed_items,
            methodology_note=METHODOLOGY_NOTE,
            summary=snap.summary or "",
        )
        return CommandCentreReport(
            snapshot_id=snap.id,
            name=snap.name,
            client_brand=snap.client_brand,
            methodology=snap.methodology,
            result=result,
        )
