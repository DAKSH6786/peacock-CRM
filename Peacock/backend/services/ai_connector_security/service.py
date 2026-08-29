"""AI Connector Security service — persist untrusted LLM I/O scans."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from db_models.base import new_uuid
from db_models.ai_connector_security import (
    CRAWLER_AS_DATA_POLICY,
    METHODOLOGY,
    SECURITY_POSITIONING,
    AcsContentSegment,
    AcsControlActivation,
    AcsInjectionFinding,
    AcsOutputValidation,
    AcsPermissionCheck,
    AcsPiiFinding,
    AcsUrlSafetyCheck,
    AiConnectorSecurityScan,
)
from ai_connector_security.engine import (
    ContentSegmentResult,
    ControlActivationResult,
    InjectionFindingResult,
    OutputValidationResult,
    PermissionCheckResult,
    PiiFindingResult,
    SecurityScanResult,
    UrlSafetyResult,
    analyse_security_scan,
)
from ai_connector_security.models import (
    AiConnectorSecurityCreateSpec,
    AiConnectorSecurityReport,
)


class AiConnectorSecurityService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def scan(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        spec: AiConnectorSecurityCreateSpec,
        created_by: str | None = None,
    ) -> AiConnectorSecurityReport:
        # Enforce tenant ids from auth context into the scan spec
        scan_spec = spec.scan
        scan_spec.organisation_id = organisation_id
        scan_spec.workspace_id = workspace_id
        if not scan_spec.claimed_organisation_id:
            scan_spec.claimed_organisation_id = organisation_id

        result = analyse_security_scan(scan_spec)

        row = AiConnectorSecurityScan(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            website_id=spec.website_id,
            name=spec.name,
            client_brand=result.client_brand,
            connector_kind=result.connector_kind,
            risk_level=result.risk_level,
            verdict=result.verdict,
            injection_findings_count=result.injection_findings_count,
            pii_findings_count=result.pii_findings_count,
            url_blocks_count=result.url_blocks_count,
            permission_denials_count=result.permission_denials_count,
            output_validation_passed=result.output_validation_passed,
            tenant_boundary_ok=result.tenant_boundary_ok,
            crawler_treated_as_data=result.crawler_treated_as_data,
            secrets_exposure_blocked=result.secrets_exposure_blocked,
            system_behaviour_change_blocked=result.system_behaviour_change_blocked,
            controls_active_count=result.controls_active_count,
            methodology=METHODOLOGY,
            security_positioning=SECURITY_POSITIONING,
            crawler_as_data_policy=CRAWLER_AS_DATA_POLICY,
            summary=result.summary,
            analysed_at=result.analysed_at,
            notes=spec.notes,
        )
        self.db.add(row)
        self.db.flush()

        for s in result.content_segments:
            self.db.add(
                AcsContentSegment(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    scan_id=row.id,
                    segment_key=s.segment_key,
                    source_kind=s.source_kind,
                    trust_tier=s.trust_tier,
                    label=s.label,
                    excerpt=s.excerpt,
                    isolated=s.isolated,
                    treated_as_instructions=s.treated_as_instructions,
                    rank_order=s.rank_order,
                )
            )
        for f in result.injection_findings:
            self.db.add(
                AcsInjectionFinding(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    scan_id=row.id,
                    segment_key=f.segment_key,
                    pattern_key=f.pattern_key,
                    severity=f.severity,
                    matched_excerpt=f.matched_excerpt,
                    blocked=f.blocked,
                    rationale=f.rationale,
                )
            )
        for p in result.permission_checks:
            self.db.add(
                AcsPermissionCheck(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    scan_id=row.id,
                    permission_kind=p.permission_kind,
                    scope_or_connector=p.scope_or_connector,
                    allowed=p.allowed,
                    reason=p.reason,
                    rank_order=p.rank_order,
                )
            )
        for u in result.url_checks:
            self.db.add(
                AcsUrlSafetyCheck(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    scan_id=row.id,
                    url=u.url[:2048],
                    scheme=u.scheme,
                    host=u.host[:255],
                    is_private_or_local=u.is_private_or_local,
                    decision=u.decision,
                    reason=u.reason,
                )
            )
        for p in result.pii_findings:
            self.db.add(
                AcsPiiFinding(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    scan_id=row.id,
                    segment_key=p.segment_key,
                    pii_type=p.pii_type,
                    action=p.action,
                    redacted_excerpt=p.redacted_excerpt,
                    confidence=p.confidence,
                )
            )
        for o in result.output_validations:
            self.db.add(
                AcsOutputValidation(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    scan_id=row.id,
                    check_key=o.check_key,
                    passed=o.passed,
                    detail=o.detail,
                )
            )
        for c in result.control_activations:
            self.db.add(
                AcsControlActivation(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    scan_id=row.id,
                    control_kind=c.control_kind,
                    control_label=c.control_label,
                    active=c.active,
                    detail=c.detail,
                    rank_order=c.rank_order,
                )
            )

        self.db.commit()
        return AiConnectorSecurityReport(
            scan_id=row.id,
            name=row.name,
            client_brand=row.client_brand,
            methodology=row.methodology,
            result=result,
        )

    def get_scan(
        self, *, scan_id: str, organisation_id: str
    ) -> AiConnectorSecurityReport | None:
        row = self.db.scalar(
            select(AiConnectorSecurityScan).where(
                AiConnectorSecurityScan.id == scan_id,
                AiConnectorSecurityScan.organisation_id == organisation_id,
            )
        )
        if row is None:
            return None

        segments = [
            ContentSegmentResult(
                segment_key=s.segment_key,
                source_kind=s.source_kind,
                trust_tier=s.trust_tier,
                label=s.label,
                excerpt=s.excerpt,
                isolated=s.isolated,
                treated_as_instructions=s.treated_as_instructions,
                rank_order=s.rank_order,
            )
            for s in self.db.scalars(
                select(AcsContentSegment)
                .where(AcsContentSegment.scan_id == row.id)
                .order_by(AcsContentSegment.rank_order.asc())
            ).all()
        ]
        injections = [
            InjectionFindingResult(
                segment_key=f.segment_key,
                pattern_key=f.pattern_key,
                severity=f.severity,
                matched_excerpt=f.matched_excerpt,
                blocked=f.blocked,
                rationale=f.rationale,
            )
            for f in self.db.scalars(
                select(AcsInjectionFinding).where(AcsInjectionFinding.scan_id == row.id)
            ).all()
        ]
        permissions = [
            PermissionCheckResult(
                permission_kind=p.permission_kind,
                scope_or_connector=p.scope_or_connector,
                allowed=p.allowed,
                reason=p.reason,
                rank_order=p.rank_order,
            )
            for p in self.db.scalars(
                select(AcsPermissionCheck)
                .where(AcsPermissionCheck.scan_id == row.id)
                .order_by(AcsPermissionCheck.rank_order.asc())
            ).all()
        ]
        urls = [
            UrlSafetyResult(
                url=u.url,
                scheme=u.scheme,
                host=u.host,
                is_private_or_local=u.is_private_or_local,
                decision=u.decision,
                reason=u.reason,
            )
            for u in self.db.scalars(
                select(AcsUrlSafetyCheck).where(AcsUrlSafetyCheck.scan_id == row.id)
            ).all()
        ]
        pii = [
            PiiFindingResult(
                segment_key=p.segment_key,
                pii_type=p.pii_type,
                action=p.action,
                redacted_excerpt=p.redacted_excerpt,
                confidence=p.confidence,
            )
            for p in self.db.scalars(
                select(AcsPiiFinding).where(AcsPiiFinding.scan_id == row.id)
            ).all()
        ]
        outputs = [
            OutputValidationResult(
                check_key=o.check_key,
                passed=o.passed,
                detail=o.detail,
            )
            for o in self.db.scalars(
                select(AcsOutputValidation).where(AcsOutputValidation.scan_id == row.id)
            ).all()
        ]
        controls = [
            ControlActivationResult(
                control_kind=c.control_kind,
                control_label=c.control_label,
                active=c.active,
                detail=c.detail,
                rank_order=c.rank_order,
            )
            for c in self.db.scalars(
                select(AcsControlActivation)
                .where(AcsControlActivation.scan_id == row.id)
                .order_by(AcsControlActivation.rank_order.asc())
            ).all()
        ]

        from db_models.ai_connector_security import METHODOLOGY_NOTE

        result = SecurityScanResult(
            client_brand=row.client_brand,
            connector_kind=row.connector_kind,
            risk_level=row.risk_level,
            verdict=row.verdict,
            injection_findings_count=row.injection_findings_count,
            pii_findings_count=row.pii_findings_count,
            url_blocks_count=row.url_blocks_count,
            permission_denials_count=row.permission_denials_count,
            output_validation_passed=row.output_validation_passed,
            tenant_boundary_ok=row.tenant_boundary_ok,
            crawler_treated_as_data=row.crawler_treated_as_data,
            secrets_exposure_blocked=row.secrets_exposure_blocked,
            system_behaviour_change_blocked=row.system_behaviour_change_blocked,
            controls_active_count=row.controls_active_count,
            content_segments=segments,
            injection_findings=injections,
            permission_checks=permissions,
            url_checks=urls,
            pii_findings=pii,
            output_validations=outputs,
            control_activations=controls,
            security_positioning=row.security_positioning,
            crawler_as_data_policy=row.crawler_as_data_policy,
            methodology_note=METHODOLOGY_NOTE,
            summary=row.summary,
            analysed_at=row.analysed_at,
        )
        return AiConnectorSecurityReport(
            scan_id=row.id,
            name=row.name,
            client_brand=row.client_brand,
            methodology=row.methodology,
            result=result,
        )
