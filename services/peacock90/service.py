"""Peacock 90 2.0 orchestration — persist adaptive roadmaps."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from db_models.base import new_uuid
from db_models.peacock90 import (
    CAPACITY_GUARDRAIL,
    METHODOLOGY,
    METHODOLOGY_NOTE,
    P90CapacityRefusal,
    P90Dependency,
    P90Initiative,
    P90Task,
    Peacock90Plan,
)
from peacock90.models import Peacock90Report, Peacock90Spec
from peacock90.optimiser import (
    CapacityRefusal,
    DependencyResult,
    InitiativeResult,
    RoadmapPlanResult,
    TaskResult,
    optimise_roadmap,
)


class Peacock90Service:
    def __init__(self, db: Session) -> None:
        self.db = db

    def generate(
        self,
        *,
        organisation_id: str,
        workspace_id: str,
        spec: Peacock90Spec,
        created_by: str | None = None,
    ) -> Peacock90Report:
        result = optimise_roadmap(spec.plan)
        c = result.constraints

        plan = Peacock90Plan(
            id=new_uuid(),
            organisation_id=organisation_id,
            workspace_id=workspace_id,
            created_by=created_by,
            website_id=spec.website_id,
            name=spec.name,
            client_brand=spec.plan.client_brand.strip(),
            horizon_days=result.horizon_days,
            methodology=METHODOLOGY,
            plan_status="completed",
            budget_amount=float(c["budget_amount"]),
            budget_currency=str(c.get("budget_currency") or "INR"),
            writers=int(c["writers"]),
            developers=int(c["developers"]),
            seo_specialists=int(c["seo_specialists"]),
            articles_per_month_max=int(c["articles_per_month_max"]),
            approval_capacity_per_week=int(c["approval_capacity_per_week"]),
            risk_tolerance=str(c["risk_tolerance"]),
            business_priorities=",".join(c.get("business_priorities") or []),
            capacity_guardrail=CAPACITY_GUARDRAIL,
            total_impact_score=result.total_impact_score,
            budget_used=result.budget_used,
            articles_planned=result.articles_planned,
            initiatives_selected=result.initiatives_selected,
            initiatives_rejected=result.initiatives_rejected,
            tasks_scheduled=result.tasks_scheduled,
            utilisation_summary=result.utilisation_summary,
            summary=result.summary,
            notes=spec.notes,
        )
        self.db.add(plan)
        self.db.flush()

        initiative_ids: dict[str, str] = {}
        for init in result.initiatives:
            row = P90Initiative(
                id=new_uuid(),
                organisation_id=organisation_id,
                workspace_id=workspace_id,
                created_by=created_by,
                plan_id=plan.id,
                initiative_code=init.initiative_code,
                title=init.title,
                priority_family=init.priority_family,
                selected=init.selected,
                impact_score=init.impact_score,
                effort_score=init.effort_score,
                risk_level=init.risk_level,
                budget_cost=init.budget_cost,
                writer_days=init.writer_days,
                developer_days=init.developer_days,
                seo_days=init.seo_days,
                articles_required=init.articles_required,
                approval_slots=init.approval_slots,
                rank=init.rank,
                rejection_reason=init.rejection_reason,
                rationale=init.rationale,
            )
            self.db.add(row)
            self.db.flush()
            initiative_ids[init.initiative_code] = row.id

        for t in result.tasks:
            self.db.add(
                P90Task(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    plan_id=plan.id,
                    initiative_id=initiative_ids.get(t.initiative_code),
                    task_code=t.task_code,
                    title=t.title,
                    task_kind=t.task_kind,
                    owner_role=t.owner_role,
                    week_index=t.week_index,
                    effort_days=t.effort_days,
                    sequence_order=t.sequence_order,
                    description=t.description,
                )
            )

        for d in result.dependencies:
            self.db.add(
                P90Dependency(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    plan_id=plan.id,
                    predecessor_task_code=d.predecessor_task_code,
                    successor_task_code=d.successor_task_code,
                    edge_label=d.edge_label,
                )
            )

        for r in result.capacity_refusals:
            self.db.add(
                P90CapacityRefusal(
                    id=new_uuid(),
                    organisation_id=organisation_id,
                    workspace_id=workspace_id,
                    created_by=created_by,
                    plan_id=plan.id,
                    requested_label=r.requested_label,
                    requested_amount=r.requested_amount,
                    capacity_limit=r.capacity_limit,
                    unit=r.unit,
                    reason=r.reason,
                )
            )

        self.db.commit()
        return Peacock90Report(
            plan_id=plan.id,
            name=plan.name,
            client_brand=plan.client_brand,
            methodology=plan.methodology,
            result=result,
        )

    def get_plan(self, *, plan_id: str, organisation_id: str) -> Peacock90Report | None:
        plan = self.db.scalar(
            select(Peacock90Plan).where(
                Peacock90Plan.id == plan_id,
                Peacock90Plan.organisation_id == organisation_id,
            )
        )
        if plan is None:
            return None

        initiatives = [
            InitiativeResult(
                initiative_code=i.initiative_code,
                title=i.title,
                priority_family=i.priority_family,
                selected=i.selected,
                impact_score=i.impact_score,
                effort_score=i.effort_score,
                risk_level=i.risk_level,
                budget_cost=i.budget_cost,
                writer_days=i.writer_days,
                developer_days=i.developer_days,
                seo_days=i.seo_days,
                articles_required=i.articles_required,
                approval_slots=i.approval_slots,
                rank=i.rank,
                rejection_reason=i.rejection_reason,
                rationale=i.rationale,
            )
            for i in self.db.scalars(
                select(P90Initiative)
                .where(P90Initiative.plan_id == plan.id)
                .order_by(P90Initiative.rank.asc().nullslast())
            ).all()
        ]

        init_by_id = {
            row.id: row.initiative_code
            for row in self.db.scalars(
                select(P90Initiative).where(P90Initiative.plan_id == plan.id)
            ).all()
        }
        task_rows = list(
            self.db.scalars(
                select(P90Task)
                .where(P90Task.plan_id == plan.id)
                .order_by(P90Task.week_index.asc(), P90Task.sequence_order.asc())
            ).all()
        )
        dep_rows = list(
            self.db.scalars(
                select(P90Dependency).where(P90Dependency.plan_id == plan.id)
            ).all()
        )
        dep_map: dict[str, list[str]] = {}
        for d in dep_rows:
            dep_map.setdefault(d.successor_task_code, []).append(d.predecessor_task_code)

        tasks = [
            TaskResult(
                task_code=t.task_code,
                title=t.title,
                task_kind=t.task_kind,
                owner_role=t.owner_role,
                week_index=t.week_index,
                effort_days=t.effort_days,
                sequence_order=t.sequence_order,
                initiative_code=init_by_id.get(t.initiative_id or "", ""),
                description=t.description,
                depends_on=dep_map.get(t.task_code, []),
            )
            for t in task_rows
        ]

        dependencies = [
            DependencyResult(
                predecessor_task_code=d.predecessor_task_code,
                successor_task_code=d.successor_task_code,
                edge_label=d.edge_label,
            )
            for d in dep_rows
        ]
        refusals = [
            CapacityRefusal(
                requested_label=r.requested_label,
                requested_amount=r.requested_amount,
                capacity_limit=r.capacity_limit,
                unit=r.unit,
                reason=r.reason,
            )
            for r in self.db.scalars(
                select(P90CapacityRefusal).where(P90CapacityRefusal.plan_id == plan.id)
            ).all()
        ]

        result = RoadmapPlanResult(
            horizon_days=plan.horizon_days,
            constraints={
                "budget_amount": plan.budget_amount,
                "budget_currency": plan.budget_currency,
                "writers": plan.writers,
                "developers": plan.developers,
                "seo_specialists": plan.seo_specialists,
                "articles_per_month_max": plan.articles_per_month_max,
                "approval_capacity_per_week": plan.approval_capacity_per_week,
                "business_priorities": [
                    x for x in plan.business_priorities.split(",") if x
                ],
                "risk_tolerance": plan.risk_tolerance,
            },
            initiatives=initiatives,
            tasks=tasks,
            dependencies=dependencies,
            capacity_refusals=refusals,
            total_impact_score=plan.total_impact_score,
            budget_used=plan.budget_used,
            articles_planned=plan.articles_planned,
            initiatives_selected=plan.initiatives_selected,
            initiatives_rejected=plan.initiatives_rejected,
            tasks_scheduled=plan.tasks_scheduled,
            utilisation_summary=plan.utilisation_summary,
            capacity_guardrail=plan.capacity_guardrail,
            methodology_note=METHODOLOGY_NOTE,
            dependency_example=[
                "Fix canonical issue",
                "Recrawl",
                "Update content",
                "Request indexing",
                "Monitor",
            ],
            summary=plan.summary or "",
        )
        return Peacock90Report(
            plan_id=plan.id,
            name=plan.name,
            client_brand=plan.client_brand,
            methodology=plan.methodology,
            result=result,
        )
