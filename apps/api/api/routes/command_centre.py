"""Peacock Command Centre API — flagship visibility command surface."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from command_centre import (
    CommandCentreCreateSpec,
    CommandCentreService,
    CommandCentreSpec,
    FeedItemSpec,
    SituationSpec,
    VisibilitySignalSpec,
    assemble_command_centre,
    catalog,
)
from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas_command_centre import (
    CommandCentreCatalogResponse,
    CommandCentrePreviewResponse,
    CommandCentreSnapshotRequest,
    CommandCentreSnapshotResponse,
    FeedItemResponse,
    SituationResponse,
    VisibilitySignalResponse,
)
from observability.audit import AuditEvent, AuditLogger

router = APIRouter(prefix="/command-centre", tags=["command-centre"])
audit_logger = AuditLogger()


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


def _result_payload(result) -> dict:
    return {
        "visibility_index": result.visibility_index,
        "visibility_delta": result.visibility_delta,
        "captured_at": result.captured_at.isoformat(),
        "headline": result.headline,
        "signals": [VisibilitySignalResponse(**s.to_dict()) for s in result.signals],
        "situations": [SituationResponse(**s.to_dict()) for s in result.situations],
        "feed_items": [FeedItemResponse(**f.to_dict()) for f in result.feed_items],
        "methodology_note": result.methodology_note,
        "summary": result.summary,
    }


def _to_response(report) -> CommandCentreSnapshotResponse:
    payload = _result_payload(report.result)
    return CommandCentreSnapshotResponse(
        snapshot_id=report.snapshot_id,
        name=report.name,
        client_brand=report.client_brand,
        methodology=report.methodology,
        **payload,
    )


@router.get("/catalog", response_model=CommandCentreCatalogResponse)
def command_centre_catalog(
    ctx: AuthContext = Depends(get_auth_context),
) -> CommandCentreCatalogResponse:
    _ = ctx
    return CommandCentreCatalogResponse(**catalog())


@router.get("/preview", response_model=CommandCentrePreviewResponse)
def command_centre_preview(brand: str = "Acme") -> CommandCentrePreviewResponse:
    """Public demo snapshot for the flagship Command Centre UI."""
    result = assemble_command_centre(CommandCentreSpec(client_brand=brand))
    payload = _result_payload(result)
    return CommandCentrePreviewResponse(client_brand=result.client_brand, **payload)


@router.post("/snapshots", response_model=CommandCentreSnapshotResponse, status_code=201)
def create_command_centre_snapshot(
    body: CommandCentreSnapshotRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> CommandCentreSnapshotResponse:
    ws = _workspace_id(ctx, body.workspace_id)
    try:
        report = CommandCentreService(db).create_snapshot(
            organisation_id=ctx.organisation.id,
            workspace_id=ws,
            created_by=ctx.user.id,
            spec=CommandCentreCreateSpec(
                website_id=body.website_id,
                name=body.name,
                centre=CommandCentreSpec(
                    client_brand=body.brief.client_brand,
                    signals=[
                        VisibilitySignalSpec(
                            dimension=s.dimension, score=s.score, delta=s.delta
                        )
                        for s in body.brief.signals
                    ],
                    situations=[
                        SituationSpec(
                            kind=s.kind,
                            title=s.title,
                            detail=s.detail,
                            severity=s.severity,
                        )
                        for s in body.brief.situations
                    ],
                    feed_items=[
                        FeedItemSpec(
                            headline=f.headline,
                            body=f.body,
                            primary_driver=f.primary_driver,
                            potential_response=f.potential_response,
                            confidence=f.confidence,
                            detected_at=f.detected_at,
                            graph_surface=f.graph_surface,
                            detection_label=f.detection_label,
                        )
                        for f in body.brief.feed_items
                    ],
                    captured_at=body.brief.captured_at,
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
            action="command_centre.snapshot",
            resource_type="command_centre_snapshot",
            resource_id=report.snapshot_id,
            workspace_id=ws,
            metadata={
                "visibility_index": report.result.visibility_index,
                "feed_count": len(report.result.feed_items),
            },
        )
    )
    return _to_response(report)


@router.get("/snapshots/{snapshot_id}", response_model=CommandCentreSnapshotResponse)
def get_command_centre_snapshot(
    snapshot_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> CommandCentreSnapshotResponse:
    report = CommandCentreService(db).get_snapshot(
        snapshot_id=snapshot_id,
        organisation_id=ctx.organisation.id,
    )
    if report is None:
        raise HTTPException(status_code=404, detail="Command Centre snapshot not found")
    return _to_response(report)
