"""Peacock Security for AI Connectors API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ai_connector_security import (
    AiConnectorSecurityCreateSpec,
    AiConnectorSecurityService,
    SecurityScanSpec,
    catalog,
    demo_scan,
)
from api.db import get_db
from api.deps import AuthContext, get_auth_context
from api.schemas_ai_connector_security import (
    ContentSegmentResponse,
    ControlActivationResponse,
    InjectionFindingResponse,
    OutputValidationResponse,
    PermissionCheckResponse,
    PiiFindingResponse,
    SecurityCatalogResponse,
    SecurityPreviewResponse,
    SecurityScanCreateRequest,
    SecurityScanResponse,
    UrlSafetyResponse,
)
from observability.audit import AuditEvent, AuditLogger

router = APIRouter(prefix="/ai-connector-security", tags=["ai-connector-security"])
audit_logger = AuditLogger()


def _workspace_id(ctx: AuthContext, explicit: str | None) -> str:
    workspace_id = explicit or (ctx.workspace.id if ctx.workspace else None)
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
    return workspace_id


def _result_fields(result) -> dict:
    return {
        "connector_kind": result.connector_kind,
        "risk_level": result.risk_level,
        "verdict": result.verdict,
        "injection_findings_count": result.injection_findings_count,
        "pii_findings_count": result.pii_findings_count,
        "url_blocks_count": result.url_blocks_count,
        "permission_denials_count": result.permission_denials_count,
        "output_validation_passed": result.output_validation_passed,
        "tenant_boundary_ok": result.tenant_boundary_ok,
        "crawler_treated_as_data": result.crawler_treated_as_data,
        "secrets_exposure_blocked": result.secrets_exposure_blocked,
        "system_behaviour_change_blocked": result.system_behaviour_change_blocked,
        "controls_active_count": result.controls_active_count,
        "content_segments": [
            ContentSegmentResponse(**s.to_dict()) for s in result.content_segments
        ],
        "injection_findings": [
            InjectionFindingResponse(**f.to_dict()) for f in result.injection_findings
        ],
        "permission_checks": [
            PermissionCheckResponse(**p.to_dict()) for p in result.permission_checks
        ],
        "url_checks": [UrlSafetyResponse(**u.to_dict()) for u in result.url_checks],
        "pii_findings": [PiiFindingResponse(**p.to_dict()) for p in result.pii_findings],
        "output_validations": [
            OutputValidationResponse(**o.to_dict()) for o in result.output_validations
        ],
        "control_activations": [
            ControlActivationResponse(**c.to_dict()) for c in result.control_activations
        ],
        "security_positioning": result.security_positioning,
        "crawler_as_data_policy": result.crawler_as_data_policy,
        "methodology_note": result.methodology_note,
        "summary": result.summary,
        "analysed_at": result.analysed_at.isoformat(),
    }


def _to_response(report) -> SecurityScanResponse:
    return SecurityScanResponse(
        scan_id=report.scan_id,
        name=report.name,
        client_brand=report.client_brand,
        methodology=report.methodology,
        **_result_fields(report.result),
    )


@router.get("/catalog", response_model=SecurityCatalogResponse)
def security_catalog(
    ctx: AuthContext = Depends(get_auth_context),
) -> SecurityCatalogResponse:
    _ = ctx
    return SecurityCatalogResponse(**catalog())


@router.get("/preview", response_model=SecurityPreviewResponse)
def security_preview(brand: str = "Acme") -> SecurityPreviewResponse:
    """Demo: malicious crawler HTML is DATA; injection and secrets blocked."""
    result = demo_scan(brand)
    return SecurityPreviewResponse(
        client_brand=result.client_brand,
        **_result_fields(result),
    )


@router.post("/scans", response_model=SecurityScanResponse, status_code=201)
def create_security_scan(
    body: SecurityScanCreateRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> SecurityScanResponse:
    ws = _workspace_id(ctx, body.workspace_id)
    try:
        report = AiConnectorSecurityService(db).scan(
            organisation_id=ctx.organisation.id,
            workspace_id=ws,
            created_by=ctx.user.id,
            spec=AiConnectorSecurityCreateSpec(
                website_id=body.website_id,
                name=body.name,
                scan=SecurityScanSpec(
                    client_brand=body.brief.client_brand,
                    connector_kind=body.brief.connector_kind,
                    crawler_content=body.brief.crawler_content,
                    candidate_urls=body.brief.candidate_urls,
                    requested_tool_scopes=body.brief.requested_tool_scopes,
                    granted_tool_scopes=body.brief.granted_tool_scopes,
                    granted_connectors=body.brief.granted_connectors,
                    organisation_id=ctx.organisation.id,
                    workspace_id=ws,
                    claimed_organisation_id=(
                        body.brief.claimed_organisation_id or ctx.organisation.id
                    ),
                    model_output=body.brief.model_output,
                    analysed_at=body.brief.analysed_at,
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
            action="ai_connector_security.scan",
            resource_type="ai_connector_security_scan",
            resource_id=report.scan_id,
            workspace_id=ws,
            metadata={
                "verdict": report.result.verdict,
                "risk_level": report.result.risk_level,
                "injection_findings_count": report.result.injection_findings_count,
                "crawler_treated_as_data": report.result.crawler_treated_as_data,
            },
        )
    )
    return _to_response(report)


@router.get("/scans/{scan_id}", response_model=SecurityScanResponse)
def get_security_scan(
    scan_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> SecurityScanResponse:
    report = AiConnectorSecurityService(db).get_scan(
        scan_id=scan_id,
        organisation_id=ctx.organisation.id,
    )
    if report is None:
        raise HTTPException(status_code=404, detail="Security scan not found")
    return _to_response(report)
