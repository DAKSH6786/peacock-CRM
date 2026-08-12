"""Agentic Web Readiness orchestration — persist discoverability assessments."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from agentic_readiness.models import AgenticReadinessReport, AgenticReadinessSpec
from agentic_readiness.scoring import (
    CheckResult,
    GapResult,
    ReadinessAnalysisResult,
    analyse_readiness,
)
from db_models.agentic_readiness import (
    METHODOLOGY,
    METHODOLOGY_NOTE,
    NOT_INDUSTRY_STANDARD,
    SURFACE_SEPARATION,
    AgenticReadinessAnalysis,
    AwrCheckResult,
    AwrGap,
)
from db_models.base import new_uuid


class AgenticReadinessService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def analyse(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        spec: AgenticReadinessSpec,
        created_by: str | None = None,
    ) -> AgenticReadinessReport:
        result = analyse_readiness(spec.readiness)

        analysis = AgenticReadinessAnalysis(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            website_id=spec.website_id,
            name=spec.name,
            client_brand=spec.readiness.client_brand.strip(),
            industry=spec.readiness.industry,
            analysis_status="completed",
            methodology=METHODOLOGY,
            agent_readiness_score=result.agent_readiness_score,
            readiness_band=result.readiness_band,
            checks_passed=result.checks_passed,
            checks_total=result.checks_total,
            separate_from_seo_aeo_geo=True,
            surface_separation_note=SURFACE_SEPARATION,
            not_industry_standard=True,
            not_industry_standard_note=NOT_INDUSTRY_STANDARD,
            methodology_note=METHODOLOGY_NOTE,
            summary=result.summary,
            notes=spec.notes,
        )
        self.db.add(analysis)
        self.db.flush()

        for c in result.checks:
            self.db.add(
                AwrCheckResult(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    analysis_id=analysis.id,
                    check_code=c.check_code,
                    check_label=c.check_label,
                    score=c.score,
                    weight=c.weight,
                    passed=c.passed,
                    evidence_summary=c.evidence_summary,
                    machine_operable_signal=c.machine_operable_signal,
                )
            )

        for g in result.gaps:
            self.db.add(
                AwrGap(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    analysis_id=analysis.id,
                    check_code=g.check_code,
                    title=g.title,
                    severity=g.severity,
                    recommendation=g.recommendation,
                    priority=g.priority,
                )
            )

        self.db.commit()
        return AgenticReadinessReport(
            analysis_id=analysis.id,
            name=analysis.name,
            client_brand=analysis.client_brand,
            methodology=analysis.methodology,
            result=result,
        )

    def get_analysis(
        self, *, analysis_id: str, organisation_id: str
    ) -> AgenticReadinessReport | None:
        analysis = self.db.scalar(
            select(AgenticReadinessAnalysis).where(
                AgenticReadinessAnalysis.id == analysis_id,
                AgenticReadinessAnalysis.organisation_id == organisation_id,
            )
        )
        if analysis is None:
            return None

        checks = [
            CheckResult(
                check_code=c.check_code,
                check_label=c.check_label,
                score=c.score,
                weight=c.weight,
                passed=c.passed,
                evidence_summary=c.evidence_summary,
                machine_operable_signal=c.machine_operable_signal,
            )
            for c in self.db.scalars(
                select(AwrCheckResult).where(AwrCheckResult.analysis_id == analysis.id)
            ).all()
        ]
        gaps = [
            GapResult(
                check_code=g.check_code,
                title=g.title,
                severity=g.severity,
                recommendation=g.recommendation,
                priority=g.priority,
            )
            for g in self.db.scalars(
                select(AwrGap)
                .where(AwrGap.analysis_id == analysis.id)
                .order_by(AwrGap.priority.asc())
            ).all()
        ]
        result = ReadinessAnalysisResult(
            agent_readiness_score=analysis.agent_readiness_score,
            readiness_band=analysis.readiness_band,
            checks=checks,
            gaps=gaps,
            checks_passed=analysis.checks_passed,
            checks_total=analysis.checks_total,
            separate_from_seo_aeo_geo=analysis.separate_from_seo_aeo_geo,
            surface_separation_note=analysis.surface_separation_note,
            not_industry_standard=analysis.not_industry_standard,
            not_industry_standard_note=analysis.not_industry_standard_note,
            methodology_note=analysis.methodology_note,
            summary=analysis.summary or "",
        )
        return AgenticReadinessReport(
            analysis_id=analysis.id,
            name=analysis.name,
            client_brand=analysis.client_brand,
            methodology=analysis.methodology,
            result=result,
        )
