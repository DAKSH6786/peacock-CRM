"""Peacock Judge 2.0 orchestration — deterministic multi-signal judgments."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from db_models.base import new_uuid
from db_models.judge2 import (
    METHODOLOGY,
    SCORING_OUTSIDE_LLM,
    J2Evidence,
    J2ReversalCondition,
    J2SignalScore,
    Judge2Judgment,
)
from judge2.models import Judge2Report, Judge2Spec
from judge2.scoring import (
    EvidenceResult,
    JudgeResult,
    ReversalConditionResult,
    SignalScoreResult,
    judge_decision,
)


class Judge2Service:
    def __init__(self, db: Session) -> None:
        self.db = db

    def judge(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        spec: Judge2Spec,
        created_by: str | None = None,
    ) -> Judge2Report:
        result = judge_decision(spec.brief)

        row = Judge2Judgment(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            website_id=spec.website_id,
            name=spec.name,
            client_brand=spec.brief.client_brand.strip(),
            decision_question=spec.brief.decision_question.strip(),
            judgment_status="completed",
            methodology=METHODOLOGY,
            scoring_outside_llm=True,
            scoring_note=SCORING_OUTSIDE_LLM,
            recommended_action=result.recommended_action,
            why=result.why,
            expected_upside=result.expected_upside,
            expected_upside_score=result.expected_upside_score,
            risk_summary=result.risk_summary,
            risk_score=result.risk_score,
            confidence=result.confidence,
            alternative=result.alternative,
            what_would_change_decision=result.what_would_change_decision,
            composite_score=result.composite_score,
            action_code=result.action_code,
            council2_session_id=spec.brief.council2_session_id,
            summary=result.summary,
            notes=spec.notes,
        )
        self.db.add(row)
        self.db.flush()

        for s in result.signal_scores:
            self.db.add(
                J2SignalScore(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    judgment_id=row.id,
                    signal_code=s.signal_code,
                    raw_value=s.raw_value,
                    weight=s.weight,
                    inverted=s.inverted,
                    contribution=s.contribution,
                    explanation=s.explanation,
                    computed_outside_llm=True,
                )
            )

        for e in result.evidence:
            self.db.add(
                J2Evidence(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    judgment_id=row.id,
                    evidence_type=e.evidence_type,
                    statement=e.statement,
                    source_ref=e.source_ref,
                    reliability=e.reliability,
                    signal_code=e.signal_code,
                )
            )

        for r in result.reversal_conditions:
            self.db.add(
                J2ReversalCondition(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    judgment_id=row.id,
                    condition_key=r.condition_key,
                    metric_code=r.metric_code,
                    operator=r.operator,
                    threshold=r.threshold,
                    unit=r.unit,
                    statement=r.statement,
                    reevaluate_action=r.reevaluate_action,
                    priority=r.priority,
                )
            )

        self.db.commit()
        return Judge2Report(
            judgment_id=row.id,
            name=row.name,
            client_brand=row.client_brand,
            decision_question=row.decision_question,
            methodology=row.methodology,
            result=result,
        )

    def get_judgment(
        self, *, judgment_id: str, organisation_id: str
    ) -> Judge2Report | None:
        row = self.db.scalar(
            select(Judge2Judgment).where(
                Judge2Judgment.id == judgment_id,
                Judge2Judgment.organisation_id == organisation_id,
            )
        )
        if row is None:
            return None

        signals = [
            SignalScoreResult(
                signal_code=s.signal_code,
                raw_value=s.raw_value,
                weight=s.weight,
                inverted=s.inverted,
                contribution=s.contribution,
                explanation=s.explanation,
                computed_outside_llm=s.computed_outside_llm,
            )
            for s in self.db.scalars(
                select(J2SignalScore).where(J2SignalScore.judgment_id == row.id)
            ).all()
        ]
        evidence = [
            EvidenceResult(
                evidence_type=e.evidence_type,
                statement=e.statement,
                source_ref=e.source_ref,
                reliability=e.reliability,
                signal_code=e.signal_code,
            )
            for e in self.db.scalars(
                select(J2Evidence).where(J2Evidence.judgment_id == row.id)
            ).all()
        ]
        reversals = [
            ReversalConditionResult(
                condition_key=r.condition_key,
                metric_code=r.metric_code,
                operator=r.operator,
                threshold=r.threshold,
                unit=r.unit,
                statement=r.statement,
                reevaluate_action=r.reevaluate_action,
                priority=r.priority,
            )
            for r in self.db.scalars(
                select(J2ReversalCondition).where(
                    J2ReversalCondition.judgment_id == row.id
                )
            ).all()
        ]

        from db_models.judge2 import METHODOLOGY_NOTE

        result = JudgeResult(
            recommended_action=row.recommended_action,
            why=row.why,
            evidence=evidence,
            expected_upside=row.expected_upside,
            expected_upside_score=row.expected_upside_score,
            risk_summary=row.risk_summary,
            risk_score=row.risk_score,
            confidence=row.confidence,
            alternative=row.alternative,
            what_would_change_decision=row.what_would_change_decision,
            reversal_conditions=reversals,
            signal_scores=signals,
            composite_score=row.composite_score,
            action_code=row.action_code,
            scoring_outside_llm=row.scoring_outside_llm,
            scoring_note=row.scoring_note,
            methodology_note=METHODOLOGY_NOTE,
            summary=row.summary or "",
        )
        return Judge2Report(
            judgment_id=row.id,
            name=row.name,
            client_brand=row.client_brand,
            decision_question=row.decision_question,
            methodology=row.methodology,
            result=result,
        )
