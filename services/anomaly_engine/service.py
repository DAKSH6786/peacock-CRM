"""Anomaly Engine orchestration — persist impact-ranked anomalies."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from anomaly_engine.detection import AnomalyResult, AnomalyScanResult, scan_anomalies
from anomaly_engine.models import AnomalyEngineReport, AnomalyEngineSpec
from db_models.anomaly_engine import METHODOLOGY, AeAnomaly, AnomalyScan
from db_models.base import new_uuid


class AnomalyEngineService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def scan(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        spec: AnomalyEngineSpec,
        created_by: str | None = None,
    ) -> AnomalyEngineReport:
        result = scan_anomalies(spec.scan)

        scan = AnomalyScan(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            website_id=spec.website_id,
            name=spec.name,
            client_brand=spec.scan.client_brand.strip(),
            window_start=result.window_start,
            window_end=result.window_end,
            scan_status="completed",
            methodology=METHODOLOGY,
            anomalies_detected=result.anomalies_detected,
            critical_count=result.critical_count,
            high_count=result.high_count,
            top_anomaly_type=result.top_anomaly_type,
            top_impact_score=result.top_impact_score,
            summary=result.summary,
            notes=spec.notes,
        )
        self.db.add(scan)
        self.db.flush()

        for a in result.anomalies:
            self.db.add(
                AeAnomaly(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    scan_id=scan.id,
                    anomaly_type=a.anomaly_type,
                    anomaly_label=a.anomaly_label,
                    title=a.title,
                    detail=a.detail,
                    detected_at=a.detected_at,
                    severity=a.severity,
                    magnitude=a.magnitude,
                    z_score=a.z_score,
                    impact_score=a.impact_score,
                    impact_rank=a.impact_rank,
                    revenue_exposure=a.revenue_exposure,
                    metric_key=a.metric_key,
                    baseline_value=a.baseline_value,
                    current_value=a.current_value,
                    recommended_response=a.recommended_response,
                    is_noise=a.is_noise,
                )
            )

        self.db.commit()
        return AnomalyEngineReport(
            scan_id=scan.id,
            name=scan.name,
            client_brand=scan.client_brand,
            methodology=scan.methodology,
            result=result,
        )

    def get_scan(
        self, *, scan_id: str, organisation_id: str
    ) -> AnomalyEngineReport | None:
        scan = self.db.scalar(
            select(AnomalyScan).where(
                AnomalyScan.id == scan_id,
                AnomalyScan.organisation_id == organisation_id,
            )
        )
        if scan is None:
            return None

        anomalies = [
            AnomalyResult(
                anomaly_type=a.anomaly_type,
                anomaly_label=a.anomaly_label,
                title=a.title,
                detail=a.detail,
                detected_at=a.detected_at,
                severity=a.severity,
                magnitude=a.magnitude,
                z_score=a.z_score,
                impact_score=a.impact_score,
                impact_rank=a.impact_rank,
                revenue_exposure=a.revenue_exposure,
                metric_key=a.metric_key,
                baseline_value=a.baseline_value,
                current_value=a.current_value,
                recommended_response=a.recommended_response,
                is_noise=a.is_noise,
            )
            for a in self.db.scalars(
                select(AeAnomaly)
                .where(AeAnomaly.scan_id == scan.id)
                .order_by(AeAnomaly.impact_rank.asc())
            ).all()
        ]
        from db_models.anomaly_engine import METHODOLOGY_NOTE

        result = AnomalyScanResult(
            window_start=scan.window_start,
            window_end=scan.window_end,
            anomalies=anomalies,
            anomalies_detected=scan.anomalies_detected,
            critical_count=scan.critical_count,
            high_count=scan.high_count,
            top_anomaly_type=scan.top_anomaly_type,
            top_impact_score=scan.top_impact_score,
            methodology_note=METHODOLOGY_NOTE,
            summary=scan.summary or "",
        )
        return AnomalyEngineReport(
            scan_id=scan.id,
            name=scan.name,
            client_brand=scan.client_brand,
            methodology=scan.methodology,
            result=result,
        )
