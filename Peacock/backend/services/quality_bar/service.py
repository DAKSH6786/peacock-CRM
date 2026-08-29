"""Quality Bar service — persist Peacock One module completeness assessments."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from db_models.base import new_uuid
from db_models.quality_bar import (
    METHODOLOGY,
    QUALITY_POSITIONING,
    QbGateResult,
    QbRemediationAction,
    QualityBarAssessment,
)
from quality_bar.engine import (
    GateResultView,
    QualityBarResult,
    RemediationActionView,
    assess_quality_bar,
)
from quality_bar.models import QualityBarCreateSpec, QualityBarReport


class QualityBarService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def assess(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        spec: QualityBarCreateSpec,
        created_by: str | None = None,
    ) -> QualityBarReport:
        result = assess_quality_bar(spec.assessment)

        row = QualityBarAssessment(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            website_id=spec.website_id,
            name=spec.name,
            client_brand=result.client_brand,
            module_key=result.module_key,
            module_label=result.module_label,
            completeness_verdict=result.completeness_verdict,
            gates_total=result.gates_total,
            gates_passed=result.gates_passed,
            gates_failed=result.gates_failed,
            completeness_score=result.completeness_score,
            blocked_by=",".join(result.blocked_by) if result.blocked_by else None,
            improvement_summary=result.improvement_summary,
            methodology=METHODOLOGY,
            quality_positioning=QUALITY_POSITIONING,
            summary=result.summary,
            analysed_at=result.analysed_at,
            notes=spec.notes,
        )
        self.db.add(row)
        self.db.flush()

        for g in result.gate_results:
            self.db.add(
                QbGateResult(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    assessment_id=row.id,
                    gate_key=g.gate_key,
                    gate_label=g.gate_label,
                    question=g.question,
                    improvement_if_fail=g.improvement_if_fail,
                    passed=g.passed,
                    answer_yes_problem=g.answer_yes_problem,
                    rationale=g.rationale,
                    evidence_note=g.evidence_note,
                    rank_order=g.rank_order,
                )
            )
        for r in result.remediation_actions:
            self.db.add(
                QbRemediationAction(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    assessment_id=row.id,
                    gate_key=r.gate_key,
                    action_key=r.action_key,
                    action_label=r.action_label,
                    detail=r.detail,
                    links_to_learning=r.links_to_learning,
                    rank_order=r.rank_order,
                )
            )

        self.db.commit()
        return QualityBarReport(
            assessment_id=row.id,
            name=row.name,
            client_brand=row.client_brand,
            methodology=row.methodology,
            result=result,
        )

    def get_assessment(
        self, *, assessment_id: str, organisation_id: str
    ) -> QualityBarReport | None:
        row = self.db.scalar(
            select(QualityBarAssessment).where(
                QualityBarAssessment.id == assessment_id,
                QualityBarAssessment.organisation_id == organisation_id,
            )
        )
        if row is None:
            return None

        gates = [
            GateResultView(
                gate_key=g.gate_key,
                gate_label=g.gate_label,
                question=g.question,
                improvement_if_fail=g.improvement_if_fail,
                passed=g.passed,
                answer_yes_problem=g.answer_yes_problem,
                rationale=g.rationale,
                evidence_note=g.evidence_note,
                rank_order=g.rank_order,
            )
            for g in self.db.scalars(
                select(QbGateResult)
                .where(QbGateResult.assessment_id == row.id)
                .order_by(QbGateResult.rank_order.asc())
            ).all()
        ]
        remediations = [
            RemediationActionView(
                gate_key=r.gate_key,
                action_key=r.action_key,
                action_label=r.action_label,
                detail=r.detail,
                links_to_learning=r.links_to_learning,
                rank_order=r.rank_order,
            )
            for r in self.db.scalars(
                select(QbRemediationAction)
                .where(QbRemediationAction.assessment_id == row.id)
                .order_by(QbRemediationAction.rank_order.asc())
            ).all()
        ]

        from db_models.quality_bar import METHODOLOGY_NOTE

        blocked = [p for p in (row.blocked_by or "").split(",") if p.strip()]
        result = QualityBarResult(
            client_brand=row.client_brand,
            module_key=row.module_key,
            module_label=row.module_label,
            completeness_verdict=row.completeness_verdict,
            gates_total=row.gates_total,
            gates_passed=row.gates_passed,
            gates_failed=row.gates_failed,
            completeness_score=row.completeness_score,
            blocked_by=blocked,
            improvement_summary=row.improvement_summary,
            gate_results=gates,
            remediation_actions=remediations,
            quality_positioning=row.quality_positioning,
            methodology_note=METHODOLOGY_NOTE,
            summary=row.summary,
            analysed_at=row.analysed_at,
        )
        return QualityBarReport(
            assessment_id=row.id,
            name=row.name,
            client_brand=row.client_brand,
            methodology=row.methodology,
            result=result,
        )
