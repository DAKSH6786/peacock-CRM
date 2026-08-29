"""Ask Peacock 2.0 orchestration — persist structured graph answers + evidence."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ask_peacock.analysis import (
    AskSessionResult,
    EvidenceItem,
    StructuredAnswer,
    answer_ask_session,
)
from ask_peacock.models import AskPeacockReport, AskPeacockSpec
from db_models.ask_peacock import METHODOLOGY, METHODOLOGY_NOTE, ApAnswer, ApEvidence, AskPeacockSession
from db_models.base import new_uuid


class AskPeacockService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def ask(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        spec: AskPeacockSpec,
        created_by: str | None = None,
    ) -> AskPeacockReport:
        result = answer_ask_session(spec.session)

        session = AskPeacockSession(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            website_id=spec.website_id,
            name=spec.name,
            client_brand=result.client_brand,
            session_status="completed",
            methodology=METHODOLOGY,
            questions_asked=result.questions_asked,
            answers_produced=result.answers_produced,
            evidence_items=result.evidence_items,
            mean_confidence=result.mean_confidence,
            primary_intent=result.primary_intent,
            summary=result.summary,
            notes=spec.notes,
        )
        self.db.add(session)
        self.db.flush()

        for a in result.answers:
            row = ApAnswer(
                id=new_uuid(),
                organisation_id=organisation_id,
                workspace_id=workspace_id,
                created_by=created_by,
                session_id=session.id,
                question_index=a.question_index,
                question=a.question,
                intent=a.intent,
                intent_label=a.intent_label,
                observed=a.observed,
                inferred=a.inferred,
                recommended=a.recommended,
                forecast=a.forecast,
                confidence=a.confidence,
                confidence_rationale=a.confidence_rationale,
                graph_surfaces_used=",".join(a.graph_surfaces_used),
                answered_at=a.answered_at,
            )
            self.db.add(row)
            self.db.flush()
            for e in a.evidence:
                self.db.add(
                    ApEvidence(
                        id=new_uuid(),
                        organisation_id=organisation_id,
                        workspace_id=workspace_id,
                        created_by=created_by,
                        answer_id=row.id,
                        evidence_index=e.evidence_index,
                        graph_surface=e.graph_surface,
                        claim=e.claim,
                        ref_id=e.ref_id,
                        weight=e.weight,
                        section=e.section,
                    )
                )

        self.db.commit()
        return AskPeacockReport(
            session_id=session.id,
            name=session.name,
            client_brand=session.client_brand,
            methodology=session.methodology,
            result=result,
        )

    def get_session(
        self, *, session_id: str, organisation_id: str
    ) -> AskPeacockReport | None:
        session = self.db.scalar(
            select(AskPeacockSession).where(
                AskPeacockSession.id == session_id,
                AskPeacockSession.organisation_id == organisation_id,
            )
        )
        if session is None:
            return None

        answer_rows = self.db.scalars(
            select(ApAnswer)
            .where(ApAnswer.session_id == session.id)
            .order_by(ApAnswer.question_index.asc())
        ).all()

        answers: list[StructuredAnswer] = []
        for row in answer_rows:
            evidence_rows = self.db.scalars(
                select(ApEvidence)
                .where(ApEvidence.answer_id == row.id)
                .order_by(ApEvidence.evidence_index.asc())
            ).all()
            surfaces = [
                s for s in (row.graph_surfaces_used or "").split(",") if s.strip()
            ]
            answers.append(
                StructuredAnswer(
                    question_index=row.question_index,
                    question=row.question,
                    intent=row.intent,
                    intent_label=row.intent_label,
                    observed=row.observed,
                    inferred=row.inferred,
                    recommended=row.recommended,
                    forecast=row.forecast,
                    confidence=row.confidence,
                    confidence_rationale=row.confidence_rationale,
                    graph_surfaces_used=surfaces,
                    answered_at=row.answered_at,
                    evidence=[
                        EvidenceItem(
                            evidence_index=e.evidence_index,
                            graph_surface=e.graph_surface,
                            claim=e.claim,
                            ref_id=e.ref_id,
                            weight=e.weight,
                            section=e.section,
                        )
                        for e in evidence_rows
                    ],
                )
            )

        result = AskSessionResult(
            client_brand=session.client_brand,
            answers=answers,
            questions_asked=session.questions_asked,
            answers_produced=session.answers_produced,
            evidence_items=session.evidence_items,
            mean_confidence=session.mean_confidence,
            primary_intent=session.primary_intent,
            methodology_note=METHODOLOGY_NOTE,
            summary=session.summary or "",
        )
        return AskPeacockReport(
            session_id=session.id,
            name=session.name,
            client_brand=session.client_brand,
            methodology=session.methodology,
            result=result,
        )
