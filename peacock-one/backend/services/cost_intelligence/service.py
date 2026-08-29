"""Cost Intelligence service — persist Intelligence Budget estimates."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from db_models.base import new_uuid
from db_models.cost_intelligence import (
    CHEAPEST_RELIABLE_POLICY,
    COST_POSITIONING,
    METHODOLOGY,
    IbeMethodCandidate,
    IntelligenceBudgetEstimate,
)
from cost_intelligence.budget_engine import (
    BudgetEstimateResult,
    MethodCandidateResult,
    estimate_budget,
)
from cost_intelligence.models import CostIntelligenceCreateSpec, CostIntelligenceReport


class CostIntelligenceService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def estimate(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        spec: CostIntelligenceCreateSpec,
        created_by: str | None = None,
    ) -> CostIntelligenceReport:
        result = estimate_budget(spec.estimate)

        row = IntelligenceBudgetEstimate(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            website_id=spec.website_id,
            name=spec.name,
            client_brand=result.client_brand,
            workflow_intent=result.workflow_intent,
            decision_value=result.decision_value,
            question=result.question,
            selected_method_kind=result.selected_method_kind,
            selected_method_label=result.selected_method_label,
            selected_peacock_mode=result.selected_peacock_mode,
            selection_rationale=result.selection_rationale,
            rejected_expensive=result.rejected_expensive,
            expected_calls=result.expected_calls,
            expected_tokens=result.expected_tokens,
            expected_searches=result.expected_searches,
            expected_runtime_seconds=result.expected_runtime_seconds,
            expected_cost_usd_micros=result.expected_cost_usd_micros,
            candidates_count=result.candidates_count,
            methodology=METHODOLOGY,
            cost_positioning=COST_POSITIONING,
            policy_note=CHEAPEST_RELIABLE_POLICY,
            summary=result.summary,
            analysed_at=result.analysed_at,
            notes=spec.notes,
        )
        self.db.add(row)
        self.db.flush()

        for c in result.candidates:
            self.db.add(
                IbeMethodCandidate(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    estimate_id=row.id,
                    method_kind=c.method_kind,
                    method_label=c.method_label,
                    peacock_mode=c.peacock_mode,
                    reliable_enough=c.reliable_enough,
                    allowed_for_value=c.allowed_for_value,
                    selected=c.selected,
                    expected_calls=c.expected_calls,
                    expected_tokens=c.expected_tokens,
                    expected_searches=c.expected_searches,
                    expected_runtime_seconds=c.expected_runtime_seconds,
                    expected_cost_usd_micros=c.expected_cost_usd_micros,
                    reliability_score=c.reliability_score,
                    cost_efficiency_score=c.cost_efficiency_score,
                    rejection_reason=c.rejection_reason,
                    rank_order=c.rank_order,
                )
            )

        self.db.commit()
        return CostIntelligenceReport(
            estimate_id=row.id,
            name=row.name,
            client_brand=row.client_brand,
            methodology=row.methodology,
            result=result,
        )

    def get_estimate(
        self, *, estimate_id: str, organisation_id: str
    ) -> CostIntelligenceReport | None:
        row = self.db.scalar(
            select(IntelligenceBudgetEstimate).where(
                IntelligenceBudgetEstimate.id == estimate_id,
                IntelligenceBudgetEstimate.organisation_id == organisation_id,
            )
        )
        if row is None:
            return None

        candidates = [
            MethodCandidateResult(
                method_kind=c.method_kind,
                method_label=c.method_label,
                peacock_mode=c.peacock_mode,
                reliable_enough=c.reliable_enough,
                allowed_for_value=c.allowed_for_value,
                selected=c.selected,
                expected_calls=c.expected_calls,
                expected_tokens=c.expected_tokens,
                expected_searches=c.expected_searches,
                expected_runtime_seconds=c.expected_runtime_seconds,
                expected_cost_usd_micros=c.expected_cost_usd_micros,
                reliability_score=c.reliability_score,
                cost_efficiency_score=c.cost_efficiency_score,
                rejection_reason=c.rejection_reason,
                rank_order=c.rank_order,
            )
            for c in self.db.scalars(
                select(IbeMethodCandidate)
                .where(IbeMethodCandidate.estimate_id == row.id)
                .order_by(IbeMethodCandidate.rank_order.asc())
            ).all()
        ]

        from db_models.cost_intelligence import METHODOLOGY_NOTE

        result = BudgetEstimateResult(
            client_brand=row.client_brand,
            workflow_intent=row.workflow_intent,
            decision_value=row.decision_value,
            question=row.question,
            selected_method_kind=row.selected_method_kind,
            selected_method_label=row.selected_method_label,
            selected_peacock_mode=row.selected_peacock_mode,
            selection_rationale=row.selection_rationale,
            rejected_expensive=row.rejected_expensive,
            expected_calls=row.expected_calls,
            expected_tokens=row.expected_tokens,
            expected_searches=row.expected_searches,
            expected_runtime_seconds=row.expected_runtime_seconds,
            expected_cost_usd_micros=row.expected_cost_usd_micros,
            candidates=candidates,
            candidates_count=row.candidates_count,
            cost_positioning=row.cost_positioning,
            policy_note=row.policy_note,
            methodology_note=METHODOLOGY_NOTE,
            summary=row.summary,
            analysed_at=row.analysed_at,
        )
        return CostIntelligenceReport(
            estimate_id=row.id,
            name=row.name,
            client_brand=row.client_brand,
            methodology=row.methodology,
            result=result,
        )
