"""Peacock 90 2.0 optimisation — max-impact roadmap under constraints + dependency graph."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from db_models.peacock90 import (
    CAPACITY_GUARDRAIL,
    HORIZON_DAYS,
    METHODOLOGY_NOTE,
    PRIORITY_CODES,
    RISK_TOLERANCE_LEVELS,
)


WEEKS_IN_HORIZON = 13  # ~90 days


@dataclass
class ResourceConstraints:
    """Organisation capacity — the optimiser must respect these hard limits."""

    budget_amount: float
    writers: int = 5
    developers: int = 2
    seo_specialists: int = 1
    articles_per_month_max: int = 25
    approval_capacity_per_week: int = 8
    business_priorities: list[str] = field(
        default_factory=lambda: ["technical_seo", "content", "authority"]
    )
    risk_tolerance: str = "medium"
    budget_currency: str = "INR"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def validate(self) -> None:
        if self.budget_amount < 0:
            raise ValueError("budget_amount must be >= 0")
        if self.writers < 0 or self.developers < 0 or self.seo_specialists < 0:
            raise ValueError("headcount cannot be negative")
        if self.articles_per_month_max < 0:
            raise ValueError("articles_per_month_max must be >= 0")
        if self.approval_capacity_per_week < 0:
            raise ValueError("approval_capacity_per_week must be >= 0")
        if self.risk_tolerance not in RISK_TOLERANCE_LEVELS:
            raise ValueError(f"risk_tolerance must be one of {RISK_TOLERANCE_LEVELS}")
        for p in self.business_priorities:
            if p not in PRIORITY_CODES:
                raise ValueError(f"Unknown business priority: {p}")


@dataclass
class TaskTemplate:
    task_code: str
    title: str
    task_kind: str
    owner_role: str  # writer|developer|seo
    effort_days: float
    depends_on: list[str] = field(default_factory=list)
    description: str | None = None


@dataclass
class InitiativeCandidate:
    initiative_code: str
    title: str
    priority_family: str
    impact_score: float
    effort_score: float
    risk_level: str
    budget_cost: float
    writer_days: float
    developer_days: float
    seo_days: float
    articles_required: int
    approval_slots: int
    tasks: list[TaskTemplate]
    aspirational_articles: int | None = None
    rationale: str = ""


@dataclass
class PlanSpec:
    client_brand: str
    constraints: ResourceConstraints
    horizon_days: int = HORIZON_DAYS
    candidates: list[InitiativeCandidate] = field(default_factory=list)


@dataclass(slots=True)
class TaskResult:
    task_code: str
    title: str
    task_kind: str
    owner_role: str
    week_index: int
    effort_days: float
    sequence_order: int
    initiative_code: str
    description: str | None
    depends_on: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DependencyResult:
    predecessor_task_code: str
    successor_task_code: str
    edge_label: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class InitiativeResult:
    initiative_code: str
    title: str
    priority_family: str
    selected: bool
    impact_score: float
    effort_score: float
    risk_level: str
    budget_cost: float
    writer_days: float
    developer_days: float
    seo_days: float
    articles_required: int
    approval_slots: int
    rank: int | None
    rejection_reason: str | None
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CapacityRefusal:
    requested_label: str
    requested_amount: float
    capacity_limit: float
    unit: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RoadmapPlanResult:
    horizon_days: int
    constraints: dict[str, Any]
    initiatives: list[InitiativeResult]
    tasks: list[TaskResult]
    dependencies: list[DependencyResult]
    capacity_refusals: list[CapacityRefusal]
    total_impact_score: float
    budget_used: float
    articles_planned: int
    initiatives_selected: int
    initiatives_rejected: int
    tasks_scheduled: int
    utilisation_summary: str
    capacity_guardrail: str
    methodology_note: str
    dependency_example: list[str]
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "horizon_days": self.horizon_days,
            "constraints": dict(self.constraints),
            "initiatives": [i.to_dict() for i in self.initiatives],
            "tasks": [t.to_dict() for t in self.tasks],
            "dependencies": [d.to_dict() for d in self.dependencies],
            "capacity_refusals": [c.to_dict() for c in self.capacity_refusals],
            "total_impact_score": self.total_impact_score,
            "budget_used": self.budget_used,
            "articles_planned": self.articles_planned,
            "initiatives_selected": self.initiatives_selected,
            "initiatives_rejected": self.initiatives_rejected,
            "tasks_scheduled": self.tasks_scheduled,
            "utilisation_summary": self.utilisation_summary,
            "capacity_guardrail": self.capacity_guardrail,
            "methodology_note": self.methodology_note,
            "dependency_example": list(self.dependency_example),
            "summary": self.summary,
        }


def _risk_allowed(candidate_risk: str, tolerance: str) -> bool:
    order = {"low": 0, "medium": 1, "high": 2}
    return order.get(candidate_risk, 1) <= order.get(tolerance, 1)


def _priority_weight(family: str, priorities: list[str]) -> float:
    if family not in priorities:
        return 0.55
    idx = priorities.index(family)
    return 1.0 - (idx * 0.12)


def _available_days(headcount: int, weeks: int = WEEKS_IN_HORIZON) -> float:
    return float(headcount) * 4.0 * weeks


def default_candidates(constraints: ResourceConstraints) -> list[InitiativeCandidate]:
    """Built-in catalog including the canonical dependency chain example."""
    aspirational = max(constraints.articles_per_month_max * 4, 100)
    articles_90d = constraints.articles_per_month_max * 3

    return [
        InitiativeCandidate(
            initiative_code="fix_canonical_chain",
            title="Fix canonical issues → recrawl → content → index → monitor",
            priority_family="technical_seo",
            impact_score=88.0,
            effort_score=42.0,
            risk_level="low",
            budget_cost=min(80_000.0, max(constraints.budget_amount * 0.15, 1.0)),
            writer_days=6.0,
            developer_days=8.0,
            seo_days=10.0,
            articles_required=0,
            approval_slots=3,
            rationale="Technical SEO unblocker with explicit dependency chain.",
            tasks=[
                TaskTemplate(
                    "fix_canonical",
                    "Fix canonical issue",
                    "technical",
                    "developer",
                    3.0,
                    description="Resolve conflicting/missing canonical tags.",
                ),
                TaskTemplate(
                    "recrawl",
                    "Recrawl",
                    "crawl",
                    "seo",
                    1.5,
                    depends_on=["fix_canonical"],
                    description="Request recrawl after canonical fixes.",
                ),
                TaskTemplate(
                    "update_content",
                    "Update content",
                    "content",
                    "writer",
                    4.0,
                    depends_on=["recrawl"],
                    description="Refresh affected pages post-crawl.",
                ),
                TaskTemplate(
                    "request_indexing",
                    "Request indexing",
                    "indexing",
                    "seo",
                    1.0,
                    depends_on=["update_content"],
                    description="Submit updated URLs for indexing.",
                ),
                TaskTemplate(
                    "monitor_canonical",
                    "Monitor",
                    "monitoring",
                    "seo",
                    2.0,
                    depends_on=["request_indexing"],
                    description="Monitor indexation and canonical resolution.",
                ),
            ],
        ),
        InitiativeCandidate(
            initiative_code="content_expansion_capped",
            title="Publish high-impact articles within capacity",
            priority_family="content",
            impact_score=78.0,
            effort_score=55.0,
            risk_level="medium",
            budget_cost=min(150_000.0, max(constraints.budget_amount * 0.35, 1.0)),
            writer_days=float(constraints.articles_per_month_max) * 1.2,
            developer_days=2.0,
            seo_days=8.0,
            articles_required=articles_90d,
            approval_slots=max(4, constraints.articles_per_month_max // 2),
            aspirational_articles=aspirational,
            rationale=(
                f"Cap publishing at {constraints.articles_per_month_max}/month — "
                f"do not recommend {aspirational} articles when capacity cannot execute them."
            ),
            tasks=[
                TaskTemplate(
                    "content_brief_batch",
                    "Produce content briefs",
                    "content",
                    "seo",
                    4.0,
                ),
                TaskTemplate(
                    "write_articles",
                    "Write articles (capacity-capped)",
                    "content",
                    "writer",
                    float(constraints.articles_per_month_max),
                    depends_on=["content_brief_batch"],
                ),
                TaskTemplate(
                    "edit_approve",
                    "Edit and approve articles",
                    "approval",
                    "seo",
                    5.0,
                    depends_on=["write_articles"],
                ),
                TaskTemplate(
                    "publish_articles",
                    "Publish articles",
                    "content",
                    "developer",
                    2.0,
                    depends_on=["edit_approve"],
                ),
            ],
        ),
        InitiativeCandidate(
            initiative_code="authority_outreach",
            title="Build third-party authority",
            priority_family="authority",
            impact_score=72.0,
            effort_score=48.0,
            risk_level="medium",
            budget_cost=min(120_000.0, max(constraints.budget_amount * 0.25, 1.0)),
            writer_days=10.0,
            developer_days=1.0,
            seo_days=12.0,
            articles_required=4,
            approval_slots=4,
            rationale="Earn citations via targeted digital PR and expert assets.",
            tasks=[
                TaskTemplate(
                    "authority_targets", "Select authority targets", "authority", "seo", 2.0
                ),
                TaskTemplate(
                    "authority_assets",
                    "Create outreach assets",
                    "content",
                    "writer",
                    6.0,
                    depends_on=["authority_targets"],
                ),
                TaskTemplate(
                    "authority_outreach",
                    "Run outreach",
                    "authority",
                    "seo",
                    8.0,
                    depends_on=["authority_assets"],
                ),
            ],
        ),
        InitiativeCandidate(
            initiative_code="geo_aeo_pack",
            title="GEO + AEO answer-presence pack",
            priority_family="geo_aeo",
            impact_score=70.0,
            effort_score=50.0,
            risk_level="medium",
            budget_cost=min(90_000.0, max(constraints.budget_amount * 0.2, 1.0)),
            writer_days=12.0,
            developer_days=4.0,
            seo_days=9.0,
            articles_required=6,
            approval_slots=3,
            rationale="Structured answer blocks and entity clarity for generative engines.",
            tasks=[
                TaskTemplate("geo_audit", "GEO citability audit", "geo", "seo", 3.0),
                TaskTemplate(
                    "geo_rewrites",
                    "Rewrite answer-ready sections",
                    "content",
                    "writer",
                    8.0,
                    depends_on=["geo_audit"],
                ),
                TaskTemplate(
                    "geo_schema",
                    "Ship schema / entity markup",
                    "technical",
                    "developer",
                    3.0,
                    depends_on=["geo_rewrites"],
                ),
            ],
        ),
        InitiativeCandidate(
            initiative_code="mega_content_blast",
            title="100-article blast (aspirational)",
            priority_family="content",
            impact_score=95.0,
            effort_score=95.0,
            risk_level="high",
            budget_cost=500_000.0,
            writer_days=200.0,
            developer_days=20.0,
            seo_days=40.0,
            articles_required=100,
            approval_slots=40,
            aspirational_articles=100,
            rationale="High impact on paper but typically infeasible — optimiser must refuse.",
            tasks=[
                TaskTemplate("mega_write", "Write 100 articles", "content", "writer", 100.0),
            ],
        ),
        InitiativeCandidate(
            initiative_code="conversion_landing_refresh",
            title="Conversion landing refresh",
            priority_family="conversion",
            impact_score=65.0,
            effort_score=35.0,
            risk_level="low",
            budget_cost=min(60_000.0, max(constraints.budget_amount * 0.12, 1.0)),
            writer_days=8.0,
            developer_days=6.0,
            seo_days=4.0,
            articles_required=0,
            approval_slots=2,
            rationale="Refresh money pages after technical foundations.",
            tasks=[
                TaskTemplate("landing_audit", "Landing page audit", "other", "seo", 2.0),
                TaskTemplate(
                    "landing_copy",
                    "Rewrite landing copy",
                    "content",
                    "writer",
                    5.0,
                    depends_on=["landing_audit"],
                ),
                TaskTemplate(
                    "landing_ship",
                    "Ship landing updates",
                    "technical",
                    "developer",
                    4.0,
                    depends_on=["landing_copy"],
                ),
            ],
        ),
    ]


def _feasible(
    cand: InitiativeCandidate,
    remaining: dict[str, float],
    constraints: ResourceConstraints,
) -> tuple[bool, str | None]:
    if cand.budget_cost > remaining["budget"] + 1e-6:
        return False, "Insufficient budget"
    if cand.writer_days > remaining["writer_days"] + 1e-6:
        return False, "Insufficient writer capacity"
    if cand.developer_days > remaining["developer_days"] + 1e-6:
        return False, "Insufficient developer capacity"
    if cand.seo_days > remaining["seo_days"] + 1e-6:
        return False, "Insufficient SEO capacity"
    if cand.articles_required > remaining["articles"] + 1e-6:
        return False, (
            f"Exceeds content capacity ({constraints.articles_per_month_max} articles/month max)"
        )
    if cand.approval_slots > remaining["approvals"] + 1e-6:
        return False, "Insufficient approval capacity"
    return True, None


def _schedule_tasks(
    selected: list[InitiativeCandidate],
) -> tuple[list[TaskResult], list[DependencyResult]]:
    """Topological schedule: predecessors before successors; pack into weeks 1..13."""
    nodes: dict[str, tuple[InitiativeCandidate, TaskTemplate]] = {}
    for init in selected:
        for t in init.tasks:
            code = f"{init.initiative_code}::{t.task_code}"
            nodes[code] = (init, t)

    indeg: dict[str, int] = {c: 0 for c in nodes}
    succ: dict[str, list[str]] = {c: [] for c in nodes}
    for init in selected:
        for t in init.tasks:
            code = f"{init.initiative_code}::{t.task_code}"
            for dep in t.depends_on:
                pred = f"{init.initiative_code}::{dep}"
                if pred not in nodes:
                    continue
                indeg[code] += 1
                succ[pred].append(code)

    ready = sorted([c for c, d in indeg.items() if d == 0])
    order: list[str] = []
    while ready:
        n = ready.pop(0)
        order.append(n)
        for s in succ[n]:
            indeg[s] -= 1
            if indeg[s] == 0:
                ready.append(s)
                ready.sort()

    if len(order) != len(nodes):
        order = list(nodes.keys())

    week_of: dict[str, int] = {}
    role_load: dict[tuple[str, int], float] = {}
    tasks_out: list[TaskResult] = []

    for seq, code in enumerate(order, start=1):
        init, tmpl = nodes[code]
        pred_codes = [f"{init.initiative_code}::{d}" for d in tmpl.depends_on]
        earliest = 1
        for p in pred_codes:
            if p in week_of:
                earliest = max(earliest, week_of[p] + 1)
        week = earliest
        while week <= WEEKS_IN_HORIZON:
            used = role_load.get((tmpl.owner_role, week), 0.0)
            if used + min(tmpl.effort_days, 5.0) <= 5.0 or week == WEEKS_IN_HORIZON:
                break
            week += 1
        week = min(week, WEEKS_IN_HORIZON)
        week_of[code] = week
        role_load[(tmpl.owner_role, week)] = (
            role_load.get((tmpl.owner_role, week), 0.0) + tmpl.effort_days
        )
        tasks_out.append(
            TaskResult(
                task_code=code,
                title=tmpl.title,
                task_kind=tmpl.task_kind,
                owner_role=tmpl.owner_role,
                week_index=week,
                effort_days=tmpl.effort_days,
                sequence_order=seq,
                initiative_code=init.initiative_code,
                description=tmpl.description,
                depends_on=pred_codes,
            )
        )

    deps_out: list[DependencyResult] = []
    for init in selected:
        for t in init.tasks:
            succ_code = f"{init.initiative_code}::{t.task_code}"
            for dep in t.depends_on:
                pred_code = f"{init.initiative_code}::{dep}"
                deps_out.append(
                    DependencyResult(
                        predecessor_task_code=pred_code,
                        successor_task_code=succ_code,
                        edge_label="must_complete_before",
                    )
                )

    tasks_out.sort(key=lambda t: (t.week_index, t.sequence_order))
    return tasks_out, deps_out


def optimise_roadmap(spec: PlanSpec) -> RoadmapPlanResult:
    """Select maximum-impact initiatives within constraints; schedule with dependencies."""
    if not spec.client_brand.strip():
        raise ValueError("client_brand is required")
    if spec.horizon_days <= 0:
        raise ValueError("horizon_days must be positive")
    spec.constraints.validate()
    constraints = spec.constraints

    candidates = list(spec.candidates) if spec.candidates else default_candidates(constraints)
    refusals: list[CapacityRefusal] = []

    for cand in candidates:
        if cand.aspirational_articles is not None:
            if cand.aspirational_articles > constraints.articles_per_month_max:
                refusals.append(
                    CapacityRefusal(
                        requested_label=cand.title,
                        requested_amount=float(cand.aspirational_articles),
                        capacity_limit=float(constraints.articles_per_month_max),
                        unit="articles_per_month",
                        reason=(
                            f"Peacock should not recommend {int(cand.aspirational_articles)} articles "
                            f"if the organisation can execute at most "
                            f"{constraints.articles_per_month_max} articles/month "
                            f"(writers={constraints.writers}, SEO={constraints.seo_specialists})."
                        ),
                    )
                )

    remaining = {
        "budget": float(constraints.budget_amount),
        "writer_days": _available_days(constraints.writers),
        "developer_days": _available_days(constraints.developers),
        "seo_days": _available_days(constraints.seo_specialists),
        "articles": float(constraints.articles_per_month_max * 3),
        "approvals": float(constraints.approval_capacity_per_week * WEEKS_IN_HORIZON),
    }

    scored: list[tuple[float, InitiativeCandidate]] = []
    for cand in candidates:
        weight = _priority_weight(cand.priority_family, constraints.business_priorities)
        efficiency = cand.impact_score / max(1.0, cand.effort_score)
        score = cand.impact_score * weight + efficiency * 10.0
        scored.append((score, cand))
    scored.sort(key=lambda x: x[0], reverse=True)

    selected: list[InitiativeCandidate] = []
    rejected: list[tuple[InitiativeCandidate, str]] = []
    seen_codes: set[str] = set()

    for _score, cand in scored:
        if cand.initiative_code in seen_codes:
            continue
        seen_codes.add(cand.initiative_code)

        if not _risk_allowed(cand.risk_level, constraints.risk_tolerance):
            rejected.append(
                (
                    cand,
                    f"Risk level '{cand.risk_level}' exceeds tolerance '{constraints.risk_tolerance}'",
                )
            )
            continue

        if cand.articles_required > constraints.articles_per_month_max * 3:
            rejected.append(
                (
                    cand,
                    f"Exceeds content capacity ({constraints.articles_per_month_max} articles/month max)",
                )
            )
            continue

        if (
            cand.initiative_code == "mega_content_blast"
            and cand.aspirational_articles is not None
            and cand.aspirational_articles > constraints.articles_per_month_max
        ):
            rejected.append(
                (
                    cand,
                    f"Cannot execute {cand.aspirational_articles} articles with max "
                    f"{constraints.articles_per_month_max}/month",
                )
            )
            continue

        ok, reason = _feasible(cand, remaining, constraints)
        if not ok:
            rejected.append((cand, reason or "Infeasible"))
            continue

        selected.append(cand)
        remaining["budget"] -= cand.budget_cost
        remaining["writer_days"] -= cand.writer_days
        remaining["developer_days"] -= cand.developer_days
        remaining["seo_days"] -= cand.seo_days
        remaining["articles"] -= cand.articles_required
        remaining["approvals"] -= cand.approval_slots

    tasks, deps = _schedule_tasks(selected)

    initiatives_out: list[InitiativeResult] = []
    for rank, cand in enumerate(selected, start=1):
        initiatives_out.append(
            InitiativeResult(
                initiative_code=cand.initiative_code,
                title=cand.title,
                priority_family=cand.priority_family,
                selected=True,
                impact_score=cand.impact_score,
                effort_score=cand.effort_score,
                risk_level=cand.risk_level,
                budget_cost=cand.budget_cost,
                writer_days=cand.writer_days,
                developer_days=cand.developer_days,
                seo_days=cand.seo_days,
                articles_required=cand.articles_required,
                approval_slots=cand.approval_slots,
                rank=rank,
                rejection_reason=None,
                rationale=cand.rationale,
            )
        )
    for cand, reason in rejected:
        initiatives_out.append(
            InitiativeResult(
                initiative_code=cand.initiative_code,
                title=cand.title,
                priority_family=cand.priority_family,
                selected=False,
                impact_score=cand.impact_score,
                effort_score=cand.effort_score,
                risk_level=cand.risk_level,
                budget_cost=cand.budget_cost,
                writer_days=cand.writer_days,
                developer_days=cand.developer_days,
                seo_days=cand.seo_days,
                articles_required=cand.articles_required,
                approval_slots=cand.approval_slots,
                rank=None,
                rejection_reason=reason,
                rationale=cand.rationale,
            )
        )

    budget_used = constraints.budget_amount - remaining["budget"]
    articles_planned = int(sum(c.articles_required for c in selected))
    total_impact = sum(c.impact_score for c in selected)

    util = (
        f"Budget used {budget_used:,.0f} {constraints.budget_currency} of "
        f"{constraints.budget_amount:,.0f}; "
        f"writers {constraints.writers}, developers {constraints.developers}, "
        f"SEO {constraints.seo_specialists}; "
        f"articles planned {articles_planned} "
        f"(max {constraints.articles_per_month_max}/month); "
        f"remaining writer-days {remaining['writer_days']:.0f}, "
        f"dev-days {remaining['developer_days']:.0f}, "
        f"seo-days {remaining['seo_days']:.0f}."
    )

    dependency_example = [
        "Fix canonical issue",
        "Recrawl",
        "Update content",
        "Request indexing",
        "Monitor",
    ]

    summary = (
        f"Peacock 90 2.0 adaptive roadmap for {spec.client_brand}: "
        f"{len(selected)} initiatives selected, {len(rejected)} rejected under capacity, "
        f"{len(tasks)} tasks scheduled across {WEEKS_IN_HORIZON} weeks with dependency graph. "
        f"Total impact {total_impact:.0f}. {CAPACITY_GUARDRAIL}"
    )

    return RoadmapPlanResult(
        horizon_days=spec.horizon_days,
        constraints=constraints.to_dict(),
        initiatives=initiatives_out,
        tasks=tasks,
        dependencies=deps,
        capacity_refusals=refusals,
        total_impact_score=total_impact,
        budget_used=budget_used,
        articles_planned=articles_planned,
        initiatives_selected=len(selected),
        initiatives_rejected=len(rejected),
        tasks_scheduled=len(tasks),
        utilisation_summary=util,
        capacity_guardrail=CAPACITY_GUARDRAIL,
        methodology_note=METHODOLOGY_NOTE,
        dependency_example=dependency_example,
        summary=summary,
    )
