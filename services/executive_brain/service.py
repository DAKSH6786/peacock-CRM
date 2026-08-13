"""Executive Brain orchestration — persist CEO/CMO briefing."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from db_models.base import new_uuid
from db_models.executive_brain import (
    METHODOLOGY,
    METHODOLOGY_NOTE,
    EbAnswer,
    EbRoleSummary,
    ExecutiveBrainBrief,
)
from executive_brain.models import ExecutiveBrainCreateSpec, ExecutiveBrainReport
from executive_brain.synthesis import (
    ExecutiveAnswerResult,
    ExecutiveBrainResult,
    RoleSummaryResult,
    synthesise_executive_brain,
)


class ExecutiveBrainService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_brief(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        spec: ExecutiveBrainCreateSpec,
        created_by: str | None = None,
    ) -> ExecutiveBrainReport:
        result = synthesise_executive_brain(spec.brief)

        brief = ExecutiveBrainBrief(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            website_id=spec.website_id,
            name=spec.name,
            client_brand=result.client_brand,
            brief_status="completed",
            methodology=METHODOLOGY,
            generated_at=result.generated_at,
            horizon_days=result.horizon_days,
            budget_label=result.budget_label,
            overall_confidence=result.overall_confidence,
            headline=result.headline,
            summary=result.summary,
            notes=spec.notes,
        )
        self.db.add(brief)
        self.db.flush()

        for a in result.answers:
            self.db.add(
                EbAnswer(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    brief_id=brief.id,
                    question_key=a.question_key,
                    question_label=a.question_label,
                    answer=a.answer,
                    evidence_note=a.evidence_note,
                    confidence=a.confidence,
                    rank_order=a.rank_order,
                )
            )
        for r in result.role_summaries:
            self.db.add(
                EbRoleSummary(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    brief_id=brief.id,
                    role=r.role,
                    title=r.title,
                    body=r.body,
                    call_to_action=r.call_to_action,
                )
            )

        self.db.commit()
        return ExecutiveBrainReport(
            brief_id=brief.id,
            name=brief.name,
            client_brand=brief.client_brand,
            methodology=brief.methodology,
            result=result,
        )

    def get_brief(
        self, *, brief_id: str, organisation_id: str
    ) -> ExecutiveBrainReport | None:
        brief = self.db.scalar(
            select(ExecutiveBrainBrief).where(
                ExecutiveBrainBrief.id == brief_id,
                ExecutiveBrainBrief.organisation_id == organisation_id,
            )
        )
        if brief is None:
            return None

        answers = [
            ExecutiveAnswerResult(
                question_key=a.question_key,
                question_label=a.question_label,
                answer=a.answer,
                evidence_note=a.evidence_note,
                confidence=a.confidence,
                rank_order=a.rank_order,
            )
            for a in self.db.scalars(
                select(EbAnswer)
                .where(EbAnswer.brief_id == brief.id)
                .order_by(EbAnswer.rank_order.asc())
            ).all()
        ]
        role_summaries = [
            RoleSummaryResult(
                role=r.role,
                title=r.title,
                body=r.body,
                call_to_action=r.call_to_action,
            )
            for r in self.db.scalars(
                select(EbRoleSummary)
                .where(EbRoleSummary.brief_id == brief.id)
                .order_by(EbRoleSummary.role.asc())
            ).all()
        ]
        # Prefer CEO then CMO order
        role_order = {"ceo": 0, "cmo": 1}
        role_summaries.sort(key=lambda r: role_order.get(r.role, 9))

        result = ExecutiveBrainResult(
            client_brand=brief.client_brand,
            generated_at=brief.generated_at,
            horizon_days=brief.horizon_days,
            budget_label=brief.budget_label or "",
            overall_confidence=brief.overall_confidence,
            headline=brief.headline,
            answers=answers,
            role_summaries=role_summaries,
            methodology_note=METHODOLOGY_NOTE,
            summary=brief.summary or "",
        )
        return ExecutiveBrainReport(
            brief_id=brief.id,
            name=brief.name,
            client_brand=brief.client_brand,
            methodology=brief.methodology,
            result=result,
        )
