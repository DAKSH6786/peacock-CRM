"""Research Mode orchestration — persist controlled studies."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from db_models.base import new_uuid
from db_models.research_mode import (
    METHODOLOGY,
    ResearchStudy,
    RmFinding,
    RmObservation,
    RmPage,
    RmPrompt,
)
from research_mode.analysis import (
    FindingResult,
    ObservationResult,
    PageResult,
    PromptResult,
    ResearchStudyResult,
    analyse_research_study,
)
from research_mode.models import ResearchModeCreateSpec, ResearchModeReport


class ResearchModeService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def run_study(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        spec: ResearchModeCreateSpec,
        created_by: str | None = None,
    ) -> ResearchModeReport:
        result = analyse_research_study(spec.study)

        study = ResearchStudy(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            website_id=spec.website_id,
            name=spec.name,
            client_brand=result.client_brand,
            research_question=result.research_question,
            hypothesis=result.hypothesis,
            metric_key=result.metric_key,
            metric_label=result.metric_label,
            treatment_description=result.treatment_description,
            study_status="completed",
            methodology=METHODOLOGY,
            laboratory_positioning=result.laboratory_positioning,
            causality_warning=result.causality_warning,
            completed_phases=",".join(result.completed_phases),
            baseline_mean=result.baseline_mean,
            treatment_mean=result.treatment_mean,
            absolute_delta=result.absolute_delta,
            relative_delta_pct=result.relative_delta_pct,
            control_adjusted_delta=result.control_adjusted_delta,
            uncertainty_band=result.uncertainty_band,
            uncertainty_score=result.uncertainty_score,
            finding_verdict=result.finding_verdict,
            finding_summary=result.finding_summary,
            observation_rounds=result.observation_rounds,
            pages_count=result.pages_count,
            prompts_count=result.prompts_count,
            analysed_at=result.analysed_at,
            notes=spec.notes,
        )
        self.db.add(study)
        self.db.flush()

        for p in result.pages:
            self.db.add(
                RmPage(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    study_id=study.id,
                    url=p.url,
                    page_role=p.page_role,
                    label=p.label,
                    rank_order=p.rank_order,
                )
            )
        for p in result.prompts:
            self.db.add(
                RmPrompt(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    study_id=study.id,
                    prompt_text=p.prompt_text,
                    prompt_cluster=p.prompt_cluster,
                    rank_order=p.rank_order,
                )
            )
        for o in result.observations:
            self.db.add(
                RmObservation(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    study_id=study.id,
                    arm=o.arm,
                    round_index=o.round_index,
                    page_url=o.page_url,
                    page_role=o.page_role,
                    prompt_text=o.prompt_text,
                    metric_key=o.metric_key,
                    value=o.value,
                    observed_at=o.observed_at,
                )
            )
        for f in result.findings:
            self.db.add(
                RmFinding(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    study_id=study.id,
                    finding_index=f.finding_index,
                    verdict=f.verdict,
                    claim=f.claim,
                    evidence=f.evidence,
                    uncertainty_band=f.uncertainty_band,
                    uncertainty_rationale=f.uncertainty_rationale,
                    auto_causal_conclusion_rejected=f.auto_causal_conclusion_rejected,
                    next_step=f.next_step,
                )
            )

        self.db.commit()
        return ResearchModeReport(
            study_id=study.id,
            name=study.name,
            client_brand=study.client_brand,
            methodology=study.methodology,
            result=result,
        )

    def get_study(
        self, *, study_id: str, organisation_id: str
    ) -> ResearchModeReport | None:
        study = self.db.scalar(
            select(ResearchStudy).where(
                ResearchStudy.id == study_id,
                ResearchStudy.organisation_id == organisation_id,
            )
        )
        if study is None:
            return None

        pages = [
            PageResult(
                url=p.url,
                page_role=p.page_role,
                label=p.label,
                rank_order=p.rank_order,
            )
            for p in self.db.scalars(
                select(RmPage)
                .where(RmPage.study_id == study.id)
                .order_by(RmPage.rank_order.asc())
            ).all()
        ]
        prompts = [
            PromptResult(
                prompt_text=p.prompt_text,
                prompt_cluster=p.prompt_cluster,
                rank_order=p.rank_order,
            )
            for p in self.db.scalars(
                select(RmPrompt)
                .where(RmPrompt.study_id == study.id)
                .order_by(RmPrompt.rank_order.asc())
            ).all()
        ]
        observations = [
            ObservationResult(
                arm=o.arm,
                round_index=o.round_index,
                page_url=o.page_url,
                page_role=o.page_role,
                prompt_text=o.prompt_text,
                metric_key=o.metric_key,
                value=o.value,
                observed_at=o.observed_at,
            )
            for o in self.db.scalars(
                select(RmObservation)
                .where(RmObservation.study_id == study.id)
                .order_by(
                    RmObservation.arm.asc(),
                    RmObservation.round_index.asc(),
                )
            ).all()
        ]
        findings = [
            FindingResult(
                finding_index=f.finding_index,
                verdict=f.verdict,
                claim=f.claim,
                evidence=f.evidence,
                uncertainty_band=f.uncertainty_band,
                uncertainty_rationale=f.uncertainty_rationale,
                auto_causal_conclusion_rejected=f.auto_causal_conclusion_rejected,
                next_step=f.next_step,
            )
            for f in self.db.scalars(
                select(RmFinding)
                .where(RmFinding.study_id == study.id)
                .order_by(RmFinding.finding_index.asc())
            ).all()
        ]
        from db_models.research_mode import METHODOLOGY_NOTE

        result = ResearchStudyResult(
            client_brand=study.client_brand,
            research_question=study.research_question,
            hypothesis=study.hypothesis,
            metric_key=study.metric_key,
            metric_label=study.metric_label,
            treatment_description=study.treatment_description,
            completed_phases=[
                p for p in (study.completed_phases or "").split(",") if p.strip()
            ],
            pages=pages,
            prompts=prompts,
            observations=observations,
            findings=findings,
            baseline_mean=study.baseline_mean,
            treatment_mean=study.treatment_mean,
            absolute_delta=study.absolute_delta,
            relative_delta_pct=study.relative_delta_pct,
            control_adjusted_delta=study.control_adjusted_delta,
            uncertainty_band=study.uncertainty_band,
            uncertainty_score=study.uncertainty_score,
            finding_verdict=study.finding_verdict,
            finding_summary=study.finding_summary,
            observation_rounds=study.observation_rounds,
            pages_count=study.pages_count,
            prompts_count=study.prompts_count,
            laboratory_positioning=study.laboratory_positioning,
            causality_warning=study.causality_warning,
            methodology_note=METHODOLOGY_NOTE,
            analysed_at=study.analysed_at,
        )
        return ResearchModeReport(
            study_id=study.id,
            name=study.name,
            client_brand=study.client_brand,
            methodology=study.methodology,
            result=result,
        )
