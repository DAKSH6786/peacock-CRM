import "server-only";

import type { MembershipRole, Prisma } from "@prisma/client";

import { prisma } from "@/database";
import type { DashboardDateRange } from "@/modules/dashboard/date-range";
import type {
  DashboardPayload,
  MetricValue,
} from "@/modules/dashboard/metrics.types";
import {
  resolveDashboardPersona,
  type DashboardPersona,
} from "@/modules/dashboard/persona";
import type { SessionUser } from "@/permissions";
import { hasPermission, requireOrganization } from "@/permissions";

export type {
  DashboardPayload,
  MetricValue,
  NamedCount,
} from "@/modules/dashboard/metrics.types";

function money(
  label: string,
  value: number,
  currencyCode: string,
  hint?: string,
): MetricValue {
  return { label, value, format: "money", currencyCode, hint };
}

function num(label: string, value: number, hint?: string): MetricValue {
  return { label, value, format: "number", hint };
}

function pct(label: string, value: number, hint?: string): MetricValue {
  return { label, value, format: "percent", hint };
}

async function orgCurrency(organizationId: string): Promise<string> {
  const org = await prisma.organization.findUnique({
    where: { id: organizationId },
    select: { currency: true },
  });
  return org?.currency ?? "INR";
}

async function getEmployeeId(userId: string): Promise<string | null> {
  const employee = await prisma.employee.findFirst({
    where: { userId, deletedAt: null },
    select: { id: true },
  });
  return employee?.id ?? null;
}

export async function getDashboardPayload(
  user: SessionUser,
  range: DashboardDateRange,
): Promise<DashboardPayload> {
  const authed = requireOrganization(user);
  const organizationId = authed.organizationId;
  const persona = resolveDashboardPersona(authed.role);
  const currencyCode = await orgCurrency(organizationId);

  switch (persona) {
    case "founder":
      return buildFounderDashboard(organizationId, range, currencyCode, persona);
    case "sales_leader":
      return buildSalesDashboard(
        organizationId,
        range,
        currencyCode,
        persona,
        authed,
      );
    case "manager":
      return buildManagerDashboard(
        organizationId,
        range,
        currencyCode,
        persona,
        authed.id,
      );
    case "finance":
      return buildFinanceDashboard(organizationId, range, currencyCode, persona);
    case "hr":
      return buildHrDashboard(organizationId, range, currencyCode, persona);
    case "employee":
    default:
      return buildEmployeeDashboard(
        organizationId,
        range,
        currencyCode,
        persona,
        authed.id,
      );
  }
}

async function sumInvoiceTotal(
  organizationId: string,
  where: Prisma.InvoiceWhereInput,
): Promise<number> {
  const result = await prisma.invoice.aggregate({
    where: { organizationId, deletedAt: null, ...where },
    _sum: { totalMinor: true },
  });
  return result._sum.totalMinor ?? 0;
}

async function sumPayments(
  organizationId: string,
  from: Date,
  to: Date,
): Promise<number> {
  const result = await prisma.payment.aggregate({
    where: {
      organizationId,
      deletedAt: null,
      receivedAt: { gte: from, lte: to },
    },
    _sum: { amountMinor: true },
  });
  return result._sum.amountMinor ?? 0;
}

async function buildFounderDashboard(
  organizationId: string,
  range: DashboardDateRange,
  currencyCode: string,
  persona: DashboardPersona,
): Promise<DashboardPayload> {
  const todayStart = new Date();
  todayStart.setUTCHours(0, 0, 0, 0);
  const todayEnd = new Date();
  todayEnd.setUTCHours(23, 59, 59, 999);

  const [
    periodInvoiceTotal,
    collected,
    outstanding,
    activePipeline,
    weightedPipeline,
    newLeads,
    wonDeals,
    closedDeals,
    activeClients,
    activeProjects,
    atRiskProjects,
    headcount,
    attendanceToday,
    onLeave,
    payrollCost,
    pendingApprovals,
    openRisks,
    objectives,
    billableEntries,
    allEntries,
    agingBuckets,
    recentActivity,
    departmentProgress,
  ] = await Promise.all([
    sumInvoiceTotal(organizationId, {
      issueDate: { gte: range.from, lte: range.to },
      status: { not: "DRAFT" },
    }),
    sumPayments(organizationId, range.from, range.to),
    sumInvoiceTotal(organizationId, {
      balanceMinor: { gt: 0 },
      status: { in: ["SENT", "PARTIAL", "OVERDUE", "OPEN"] },
    }),
    prisma.deal.aggregate({
      where: {
        organizationId,
        deletedAt: null,
        closedAt: null,
      },
      _sum: { valueMinor: true },
      _count: true,
    }),
    prisma.deal.findMany({
      where: { organizationId, deletedAt: null, closedAt: null },
      select: { valueMinor: true, probability: true },
    }),
    prisma.lead.count({
      where: {
        organizationId,
        deletedAt: null,
        createdAt: { gte: range.from, lte: range.to },
      },
    }),
    prisma.deal.count({
      where: {
        organizationId,
        deletedAt: null,
        closedAt: { gte: range.from, lte: range.to },
        stage: { isClosedWon: true },
      },
    }),
    prisma.deal.count({
      where: {
        organizationId,
        deletedAt: null,
        closedAt: { gte: range.from, lte: range.to },
      },
    }),
    prisma.clientCompany.count({
      where: { organizationId, deletedAt: null },
    }),
    prisma.project.count({
      where: {
        organizationId,
        deletedAt: null,
        status: { in: ["ACTIVE", "IN_PROGRESS", "PLANNED"] },
      },
    }),
    prisma.project.count({
      where: {
        organizationId,
        deletedAt: null,
        status: { in: ["AT_RISK", "BLOCKED"] },
      },
    }),
    prisma.employee.count({
      where: {
        organizationId,
        deletedAt: null,
        employmentStatus: { in: ["ACTIVE", "PROBATION", "NOTICE"] },
      },
    }),
    prisma.attendanceRecord.count({
      where: {
        organizationId,
        date: { gte: todayStart, lte: todayEnd },
        status: { in: ["PRESENT", "WFH", "REMOTE"] },
      },
    }),
    prisma.leaveRequest.count({
      where: {
        organizationId,
        status: "APPROVED",
        startDate: { lte: todayEnd },
        endDate: { gte: todayStart },
        deletedAt: null,
      },
    }),
    prisma.employeeMonthlyCost.aggregate({
      where: {
        organizationId,
        month: {
          gte: new Date(
            Date.UTC(range.from.getUTCFullYear(), range.from.getUTCMonth(), 1),
          ),
          lte: new Date(
            Date.UTC(range.from.getUTCFullYear(), range.from.getUTCMonth(), 1),
          ),
        },
      },
      _sum: { costMinor: true },
    }),
    prisma.approvalRequest.count({
      where: {
        organizationId,
        status: "PENDING",
        deletedAt: null,
      },
    }),
    prisma.riskRegister.count({
      where: {
        organizationId,
        deletedAt: null,
        status: { in: ["OPEN", "MITIGATING"] },
      },
    }),
    prisma.objective.findMany({
      where: {
        organizationId,
        deletedAt: null,
        scope: "COMPANY",
      },
      select: { progressPct: true },
      take: 50,
    }),
    prisma.timeEntry.aggregate({
      where: {
        organizationId,
        deletedAt: null,
        billable: true,
        date: { gte: range.from, lte: range.to },
      },
      _sum: { hours: true },
    }),
    prisma.timeEntry.aggregate({
      where: {
        organizationId,
        deletedAt: null,
        date: { gte: range.from, lte: range.to },
      },
      _sum: { hours: true },
    }),
    Promise.all([
      sumInvoiceTotal(organizationId, {
        balanceMinor: { gt: 0 },
        dueDate: { gte: todayStart },
      }),
      sumInvoiceTotal(organizationId, {
        balanceMinor: { gt: 0 },
        dueDate: {
          lt: todayStart,
          gte: new Date(todayStart.getTime() - 30 * 86400000),
        },
      }),
      sumInvoiceTotal(organizationId, {
        balanceMinor: { gt: 0 },
        dueDate: { lt: new Date(todayStart.getTime() - 30 * 86400000) },
      }),
    ]),
    prisma.activityFeed.findMany({
      where: { organizationId },
      orderBy: { createdAt: "desc" },
      take: 8,
      select: {
        id: true,
        summary: true,
        action: true,
        entityType: true,
        createdAt: true,
      },
    }),
    prisma.objective.findMany({
      where: {
        organizationId,
        deletedAt: null,
        scope: "DEPARTMENT",
      },
      select: {
        id: true,
        title: true,
        progressPct: true,
        department: { select: { name: true } },
      },
      take: 8,
    }),
  ]);

  const weighted = weightedPipeline.reduce(
    (sum, deal) =>
      sum + Math.round((deal.valueMinor * (deal.probability ?? 0)) / 100),
    0,
  );
  const conversion =
    closedDeals > 0 ? Math.round((wonDeals / closedDeals) * 1000) / 10 : 0;
  const objectiveAvg =
    objectives.length > 0
      ? Math.round(
          objectives.reduce((s, o) => s + o.progressPct, 0) / objectives.length,
        )
      : 0;
  const billableHours = Number(billableEntries._sum.hours ?? 0);
  const totalHours = Number(allEntries._sum.hours ?? 0);
  const utilization =
    totalHours > 0 ? Math.round((billableHours / totalHours) * 1000) / 10 : 0;

  const profitability = await prisma.projectProfitabilitySnapshot.aggregate({
    where: { organizationId },
    _avg: { profitMinor: true },
    _sum: { revenueMinor: true, costMinor: true },
  });
  const rev = profitability._sum.revenueMinor ?? 0;
  const cost = profitability._sum.costMinor ?? 0;
  const grossMargin = rev > 0 ? Math.round(((rev - cost) / rev) * 1000) / 10 : 0;

  return {
    persona,
    range,
    currencyCode,
    metrics: [
      money("Current-month revenue", periodInvoiceTotal, currencyCode),
      money("Collected revenue", collected, currencyCode),
      money("Outstanding receivables", outstanding, currencyCode),
      money("Active pipeline", activePipeline._sum.valueMinor ?? 0, currencyCode),
      money("Weighted pipeline value", weighted, currencyCode),
      num("New leads", newLeads),
      pct("Conversion rate", conversion),
      num("Active clients", activeClients),
      num("Active projects", activeProjects),
      num("At-risk projects", atRiskProjects),
      pct("Company objective progress", objectiveAvg),
      num("Headcount", headcount),
      num("Attendance today", attendanceToday),
      num("Employees on leave", onLeave),
      money(
        "Total monthly payroll cost",
        payrollCost._sum.costMinor ?? 0,
        currencyCode,
      ),
      pct("Billable utilization", utilization),
      pct("Gross project margin", grossMargin),
      num("Pending approvals", pendingApprovals),
      num("Company risks", openRisks),
    ],
    charts: [
      {
        id: "invoice-aging",
        title: "Invoice aging",
        description: "Outstanding balances by age bucket",
        data: [
          { name: "Current", value: Math.round(agingBuckets[0]! / 100) },
          { name: "1–30d", value: Math.round(agingBuckets[1]! / 100) },
          { name: "30d+", value: Math.round(agingBuckets[2]! / 100) },
        ],
      },
      {
        id: "department-performance",
        title: "Department objectives",
        data: departmentProgress.map((item) => ({
          name: item.department?.name ?? item.title,
          value: item.progressPct,
        })),
      },
    ],
    lists: [
      {
        id: "department-list",
        title: "Department performance",
        items: departmentProgress.map((item) => ({
          id: item.id,
          title: item.department?.name ?? item.title,
          meta: `${item.progressPct}% complete`,
          href: "/departments",
        })),
      },
    ],
    activity: recentActivity.map((item) => ({
      id: item.id,
      title: item.summary ?? item.action,
      description: item.entityType,
      at: item.createdAt.toISOString(),
    })),
  };
}

async function buildSalesDashboard(
  organizationId: string,
  range: DashboardDateRange,
  currencyCode: string,
  persona: DashboardPersona,
  user: SessionUser,
): Promise<DashboardPayload> {
  const canSeeCost = hasPermission(
    user.role as MembershipRole,
    "employees:view_compensation",
  );

  const [
    targets,
    achievements,
    stages,
    newLeads,
    followUpsDue,
    overdueFollowUps,
    wonDeals,
    closedDeals,
    avgDeal,
    lostReasons,
    leaderboard,
    costRevenue,
  ] = await Promise.all([
    prisma.salesTarget.aggregate({
      where: {
        organizationId,
        deletedAt: null,
        month: { gte: range.from, lte: range.to },
      },
      _sum: { targetMinor: true },
    }),
    prisma.salesAchievement.aggregate({
      where: {
        organizationId,
        month: { gte: range.from, lte: range.to },
      },
      _sum: { achievedMinor: true },
    }),
    prisma.pipelineStage.findMany({
      where: { organizationId, deletedAt: null },
      select: {
        name: true,
        deals: {
          where: { deletedAt: null, closedAt: null },
          select: { valueMinor: true },
        },
      },
      orderBy: { sortOrder: "asc" },
      take: 12,
    }),
    prisma.lead.count({
      where: {
        organizationId,
        deletedAt: null,
        createdAt: { gte: range.from, lte: range.to },
      },
    }),
    prisma.followUp.count({
      where: {
        organizationId,
        deletedAt: null,
        completedAt: null,
        dueAt: { gte: new Date(), lte: range.to },
      },
    }),
    prisma.followUp.count({
      where: {
        organizationId,
        deletedAt: null,
        completedAt: null,
        dueAt: { lt: new Date() },
      },
    }),
    prisma.deal.count({
      where: {
        organizationId,
        deletedAt: null,
        closedAt: { gte: range.from, lte: range.to },
        stage: { isClosedWon: true },
      },
    }),
    prisma.deal.count({
      where: {
        organizationId,
        deletedAt: null,
        closedAt: { gte: range.from, lte: range.to },
      },
    }),
    prisma.deal.aggregate({
      where: {
        organizationId,
        deletedAt: null,
        closedAt: { gte: range.from, lte: range.to },
        stage: { isClosedWon: true },
      },
      _avg: { valueMinor: true },
    }),
    prisma.deal.groupBy({
      by: ["lostReasonId"],
      where: {
        organizationId,
        deletedAt: null,
        lostReasonId: { not: null },
        closedAt: { gte: range.from, lte: range.to },
      },
      _count: true,
    }),
    prisma.salesAchievement.findMany({
      where: {
        organizationId,
        month: { gte: range.from, lte: range.to },
      },
      include: {
        employee: {
          select: {
            id: true,
            employeeCode: true,
            user: { select: { name: true } },
          },
        },
      },
      orderBy: { achievedMinor: "desc" },
      take: 8,
    }),
    canSeeCost
      ? prisma.employeeProfitabilitySnapshot.findMany({
          where: {
            organizationId,
            month: { gte: range.from, lte: range.to },
          },
          include: {
            employee: {
              select: {
                employeeCode: true,
                user: { select: { name: true } },
              },
            },
          },
          take: 8,
          orderBy: { profitMinor: "desc" },
        })
      : Promise.resolve([]),
  ]);

  const openDeals = await prisma.deal.findMany({
    where: { organizationId, deletedAt: null, closedAt: null },
    select: { valueMinor: true, probability: true },
  });
  const forecast = openDeals.reduce(
    (sum, deal) =>
      sum + Math.round((deal.valueMinor * (deal.probability ?? 0)) / 100),
    0,
  );
  const conversion =
    closedDeals > 0 ? Math.round((wonDeals / closedDeals) * 1000) / 10 : 0;

  const lostReasonIds = lostReasons
    .map((row) => row.lostReasonId)
    .filter((id): id is string => Boolean(id));
  const reasonRows = lostReasonIds.length
    ? await prisma.lostReason.findMany({
        where: { id: { in: lostReasonIds } },
        select: { id: true, name: true },
      })
    : [];
  const reasonMap = new Map(reasonRows.map((r) => [r.id, r.name]));

  return {
    persona,
    range,
    currencyCode,
    metrics: [
      money("Team target", targets._sum.targetMinor ?? 0, currencyCode),
      money(
        "Team achievement",
        achievements._sum.achievedMinor ?? 0,
        currencyCode,
      ),
      money("Forecast revenue", forecast, currencyCode),
      num("New leads", newLeads),
      num("Follow-ups due", followUpsDue),
      num("Overdue follow-ups", overdueFollowUps),
      pct("Conversion rate", conversion),
      money(
        "Average deal size",
        Math.round(avgDeal._avg.valueMinor ?? 0),
        currencyCode,
      ),
    ],
    charts: [
      {
        id: "pipeline-by-stage",
        title: "Pipeline by stage",
        data: stages.map((stage) => ({
          name: stage.name,
          value: Math.round(
            stage.deals.reduce((s, d) => s + d.valueMinor, 0) / 100,
          ),
        })),
      },
      {
        id: "lost-reasons",
        title: "Lost reasons",
        data: lostReasons.map((row) => ({
          name: reasonMap.get(row.lostReasonId ?? "") ?? "Unknown",
          value: row._count,
        })),
      },
    ],
    lists: [
      {
        id: "leaderboard",
        title: "Salesperson leaderboard",
        items: leaderboard.map((row) => ({
          id: row.id,
          title: row.employee.user?.name ?? row.employee.employeeCode,
          meta: `${Math.round(row.achievedMinor / 100)} ${currencyCode}`,
          href: `/employees/${row.employee.id}`,
        })),
      },
      ...(canSeeCost
        ? [
            {
              id: "cost-vs-revenue",
              title: "Cost versus revenue",
              items: costRevenue.map((row) => ({
                id: row.id,
                title: row.employee.user?.name ?? row.employee.employeeCode,
                meta: `Profit ${Math.round(row.profitMinor / 100)} ${currencyCode}`,
                href: `/employees/${row.employeeId}`,
              })),
            },
          ]
        : []),
    ],
    activity: [],
  };
}

async function buildManagerDashboard(
  organizationId: string,
  range: DashboardDateRange,
  currencyCode: string,
  persona: DashboardPersona,
  userId: string,
): Promise<DashboardPayload> {
  const employeeId = await getEmployeeId(userId);
  const todayStart = new Date();
  todayStart.setUTCHours(0, 0, 0, 0);
  const todayEnd = new Date();
  todayEnd.setUTCHours(23, 59, 59, 999);

  const teamFilter = employeeId
    ? { reportingManagerId: employeeId, deletedAt: null, organizationId }
    : { organizationId, deletedAt: null };

  const team = await prisma.employee.findMany({
    where: teamFilter,
    select: { id: true, userId: true },
  });
  const teamIds = team.map((t) => t.id);
  const teamUserIds = team.map((t) => t.userId);

  const [
    attendance,
    pendingLeave,
    pendingXyme,
    xymePlans,
    overdueTasks,
    deadlines,
    checkIns,
    departmentObjectives,
  ] = await Promise.all([
    prisma.attendanceRecord.count({
      where: {
        organizationId,
        employeeId: { in: teamIds },
        date: { gte: todayStart, lte: todayEnd },
        status: { in: ["PRESENT", "WFH", "REMOTE"] },
      },
    }),
    prisma.leaveRequest.count({
      where: {
        organizationId,
        employeeId: { in: teamIds },
        status: "PENDING",
        deletedAt: null,
      },
    }),
    prisma.xYMEApproval.count({
      where: {
        organizationId,
        status: "PENDING",
        plan: { employeeId: { in: teamIds } },
      },
    }),
    prisma.xYMEPlan.findMany({
      where: {
        organizationId,
        employeeId: { in: teamIds },
        deletedAt: null,
      },
      select: {
        id: true,
        goals: { select: { progressPct: true } },
        employee: {
          select: { id: true, user: { select: { name: true } }, employeeCode: true },
        },
      },
      take: 12,
    }),
    prisma.task.count({
      where: {
        organizationId,
        deletedAt: null,
        status: { notIn: ["DONE", "COMPLETED", "CANCELLED"] },
        dueDate: { lt: todayStart },
        OR: [
          { assigneeId: { in: teamUserIds } },
          { project: { members: { some: { employeeId: { in: teamIds } } } } },
        ],
      },
    }),
    prisma.projectMilestone.findMany({
      where: {
        organizationId,
        deletedAt: null,
        dueDate: { gte: todayStart, lte: range.to },
        project: {
          members: { some: { employeeId: { in: teamIds } } },
        },
      },
      select: {
        id: true,
        title: true,
        dueDate: true,
        project: { select: { name: true, id: true } },
      },
      take: 8,
      orderBy: { dueDate: "asc" },
    }),
    prisma.xYMECheckIn.findMany({
      where: {
        organizationId,
        plan: { employeeId: { in: teamIds } },
        checkedInAt: { gte: range.from, lte: range.to },
      },
      orderBy: { checkedInAt: "desc" },
      take: 8,
      select: {
        id: true,
        note: true,
        checkedInAt: true,
        plan: {
          select: {
            employee: {
              select: { user: { select: { name: true } }, employeeCode: true },
            },
          },
        },
      },
    }),
    prisma.objective.findMany({
      where: {
        organizationId,
        deletedAt: null,
        scope: "DEPARTMENT",
      },
      select: { id: true, title: true, progressPct: true },
      take: 8,
    }),
  ]);

  const workload = await prisma.resourceAllocation.groupBy({
    by: ["employeeId"],
    where: {
      organizationId,
      employeeId: { in: teamIds },
      startDate: { lte: range.to },
      OR: [{ endDate: null }, { endDate: { gte: range.from } }],
    },
    _avg: { allocationPct: true },
  });

  return {
    persona,
    range,
    currencyCode,
    metrics: [
      num("Team attendance today", attendance),
      num("Pending leave requests", pendingLeave),
      num("Pending XYME approvals", pendingXyme),
      num("Overdue tasks", overdueTasks),
      num("Team size", teamIds.length),
      num(
        "Avg team allocation",
        workload.length
          ? Math.round(
              workload.reduce(
                (s, w) => s + (w._avg.allocationPct ?? 0),
                0,
              ) / workload.length,
            )
          : 0,
      ),
    ],
    charts: [
      {
        id: "team-xyme",
        title: "Team XYME progress",
        data: xymePlans.map((plan) => {
          const avg =
            plan.goals.length > 0
              ? Math.round(
                  plan.goals.reduce((s, g) => s + g.progressPct, 0) /
                    plan.goals.length,
                )
              : 0;
          return {
            name: plan.employee.user?.name ?? plan.employee.employeeCode,
            value: avg,
          };
        }),
      },
    ],
    lists: [
      {
        id: "deadlines",
        title: "Project deadlines",
        items: deadlines.map((item) => ({
          id: item.id,
          title: item.title,
          meta: `${item.project.name} · ${item.dueDate?.toISOString().slice(0, 10) ?? ""}`,
          href: `/projects`,
        })),
      },
      {
        id: "objectives",
        title: "Department objectives",
        items: departmentObjectives.map((item) => ({
          id: item.id,
          title: item.title,
          meta: `${item.progressPct}%`,
          href: "/departments",
        })),
      },
    ],
    activity: checkIns.map((item) => ({
      id: item.id,
      title: `${item.plan.employee.user?.name ?? item.plan.employee.employeeCode} checked in`,
      description: item.note ?? "XYME check-in",
      at: item.checkedInAt.toISOString(),
    })),
  };
}

async function buildEmployeeDashboard(
  organizationId: string,
  range: DashboardDateRange,
  currencyCode: string,
  persona: DashboardPersona,
  userId: string,
): Promise<DashboardPayload> {
  const employeeId = await getEmployeeId(userId);
  const now = new Date();

  const [
    tasks,
    deliverables,
    xymeGoals,
    attendance,
    leaveBalances,
    deadlines,
    announcements,
    approvals,
    documents,
    activity,
  ] = await Promise.all([
    prisma.task.findMany({
      where: {
        organizationId,
        deletedAt: null,
        assigneeId: userId,
        status: { notIn: ["DONE", "COMPLETED", "CANCELLED"] },
      },
      orderBy: { dueDate: "asc" },
      take: 8,
      select: { id: true, title: true, dueDate: true, status: true },
    }),
    employeeId
      ? prisma.deliverableApproval.findMany({
          where: {
            organizationId,
            status: "PENDING",
            reviewerId: userId,
          },
          take: 8,
          select: {
            id: true,
            deliverable: { select: { id: true, title: true } },
          },
        })
      : Promise.resolve([]),
    employeeId
      ? prisma.xYMEGoal.findMany({
          where: {
            organizationId,
            deletedAt: null,
            plan: { employeeId, deletedAt: null },
          },
          select: { id: true, title: true, progressPct: true, category: true },
          take: 8,
        })
      : Promise.resolve([]),
    employeeId
      ? prisma.attendanceRecord.count({
          where: {
            organizationId,
            employeeId,
            date: { gte: range.from, lte: range.to },
            status: { in: ["PRESENT", "WFH", "REMOTE"] },
          },
        })
      : Promise.resolve(0),
    employeeId
      ? prisma.leaveBalance.findMany({
          where: { organizationId, employeeId },
          include: { leaveType: { select: { name: true } } },
          take: 5,
        })
      : Promise.resolve([]),
    prisma.task.findMany({
      where: {
        organizationId,
        deletedAt: null,
        assigneeId: userId,
        dueDate: { gte: now },
      },
      orderBy: { dueDate: "asc" },
      take: 5,
      select: { id: true, title: true, dueDate: true },
    }),
    prisma.announcement.findMany({
      where: {
        organizationId,
        deletedAt: null,
        OR: [{ publishedAt: null }, { publishedAt: { lte: now } }],
      },
      orderBy: { createdAt: "desc" },
      take: 5,
      select: { id: true, title: true, publishedAt: true, createdAt: true },
    }),
    prisma.approvalRequest.findMany({
      where: {
        organizationId,
        deletedAt: null,
        requestedById: userId,
        status: "PENDING",
      },
      take: 5,
      select: { id: true, title: true, status: true },
    }),
    employeeId
      ? prisma.employeeDocument.findMany({
          where: { organizationId, employeeId, deletedAt: null },
          take: 5,
          select: { id: true, title: true },
        })
      : Promise.resolve([]),
    prisma.activityFeed.findMany({
      where: { organizationId, actorId: userId },
      orderBy: { createdAt: "desc" },
      take: 8,
      select: {
        id: true,
        summary: true,
        action: true,
        createdAt: true,
        entityType: true,
      },
    }),
  ]);

  const xymeAvg =
    xymeGoals.length > 0
      ? Math.round(
          xymeGoals.reduce((s, g) => s + g.progressPct, 0) / xymeGoals.length,
        )
      : 0;

  return {
    persona,
    range,
    currencyCode,
    metrics: [
      num("My open tasks", tasks.length),
      num("Deliverables awaiting action", deliverables.length),
      pct("My XYME progress", xymeAvg),
      num("Attendance days in range", attendance),
      num("Pending my approval requests", approvals.length),
    ],
    charts: [
      {
        id: "my-xyme",
        title: "My XYME goals",
        data: xymeGoals.map((goal) => ({
          name: `${goal.category}: ${goal.title}`.slice(0, 24),
          value: goal.progressPct,
        })),
      },
    ],
    lists: [
      {
        id: "tasks",
        title: "My tasks",
        items: tasks.map((task) => ({
          id: task.id,
          title: task.title,
          meta: task.dueDate?.toISOString().slice(0, 10) ?? task.status,
          href: "/tasks",
        })),
      },
      {
        id: "leave",
        title: "My leave balance",
        items: leaveBalances.map((balance) => ({
          id: balance.id,
          title: balance.leaveType.name,
          meta: `${balance.balanceDays.toString()} days`,
          href: "/hr/leaves",
        })),
      },
      {
        id: "deadlines",
        title: "My upcoming deadlines",
        items: deadlines.map((task) => ({
          id: task.id,
          title: task.title,
          meta: task.dueDate?.toISOString().slice(0, 10),
          href: "/tasks",
        })),
      },
      {
        id: "announcements",
        title: "My announcements",
        items: announcements.map((item) => ({
          id: item.id,
          title: item.title,
          meta: (item.publishedAt ?? item.createdAt).toISOString().slice(0, 10),
        })),
      },
      {
        id: "documents",
        title: "My documents",
        items: documents.map((doc) => ({
          id: doc.id,
          title: doc.title,
          href: "/documents",
        })),
      },
      {
        id: "deliverables",
        title: "My deliverables",
        items: deliverables.map((item) => ({
          id: item.id,
          title: item.deliverable.title,
          href: "/deliverables",
        })),
      },
    ],
    activity: activity.map((item) => ({
      id: item.id,
      title: item.summary ?? item.action,
      description: item.entityType,
      at: item.createdAt.toISOString(),
    })),
  };
}

async function buildFinanceDashboard(
  organizationId: string,
  range: DashboardDateRange,
  currencyCode: string,
  persona: DashboardPersona,
): Promise<DashboardPayload> {
  const today = new Date();
  today.setUTCHours(0, 0, 0, 0);

  const [
    invoiceTotals,
    paymentsReceived,
    outstanding,
    overdue,
    expenses,
    vendorBills,
    collectionTrend,
    aging,
    revenueByService,
    profitability,
  ] = await Promise.all([
    sumInvoiceTotal(organizationId, {
      issueDate: { gte: range.from, lte: range.to },
      status: { not: "DRAFT" },
    }),
    sumPayments(organizationId, range.from, range.to),
    sumInvoiceTotal(organizationId, { balanceMinor: { gt: 0 } }),
    sumInvoiceTotal(organizationId, {
      balanceMinor: { gt: 0 },
      dueDate: { lt: today },
    }),
    prisma.expense.aggregate({
      where: {
        organizationId,
        deletedAt: null,
        spentAt: { gte: range.from, lte: range.to },
      },
      _sum: { amountMinor: true },
    }),
    prisma.vendorBill.aggregate({
      where: {
        organizationId,
        deletedAt: null,
        createdAt: { gte: range.from, lte: range.to },
      },
      _sum: { amountMinor: true },
    }),
    prisma.payment.findMany({
      where: {
        organizationId,
        deletedAt: null,
        receivedAt: { gte: range.from, lte: range.to },
      },
      select: { receivedAt: true, amountMinor: true },
      orderBy: { receivedAt: "asc" },
    }),
    Promise.all([
      sumInvoiceTotal(organizationId, {
        balanceMinor: { gt: 0 },
        dueDate: { gte: today },
      }),
      sumInvoiceTotal(organizationId, {
        balanceMinor: { gt: 0 },
        dueDate: {
          lt: today,
          gte: new Date(today.getTime() - 30 * 86400000),
        },
      }),
      sumInvoiceTotal(organizationId, {
        balanceMinor: { gt: 0 },
        dueDate: { lt: new Date(today.getTime() - 30 * 86400000) },
      }),
    ]),
    prisma.projectService.groupBy({
      by: ["name"],
      where: { organizationId },
      _count: true,
    }),
    prisma.projectProfitabilitySnapshot.findMany({
      where: { organizationId },
      orderBy: { asOfDate: "desc" },
      take: 8,
      include: { project: { select: { id: true, name: true } } },
    }),
  ]);

  const trendMap = new Map<string, number>();
  for (const payment of collectionTrend) {
    const key = payment.receivedAt.toISOString().slice(0, 10);
    trendMap.set(key, (trendMap.get(key) ?? 0) + payment.amountMinor);
  }

  return {
    persona,
    range,
    currencyCode,
    metrics: [
      money("Invoice totals", invoiceTotals, currencyCode),
      money("Payments received", paymentsReceived, currencyCode),
      money("Outstanding amount", outstanding, currencyCode),
      money("Overdue invoices", overdue, currencyCode),
      money("Expense totals", expenses._sum.amountMinor ?? 0, currencyCode),
      money("Vendor bills", vendorBills._sum.amountMinor ?? 0, currencyCode),
    ],
    charts: [
      {
        id: "cash-collection",
        title: "Cash collection trend",
        data: [...trendMap.entries()].map(([name, value]) => ({
          name,
          value: Math.round(value / 100),
        })),
      },
      {
        id: "receivable-aging",
        title: "Receivable aging",
        data: [
          { name: "Current", value: Math.round(aging[0]! / 100) },
          { name: "1–30d", value: Math.round(aging[1]! / 100) },
          { name: "30d+", value: Math.round(aging[2]! / 100) },
        ],
      },
      {
        id: "revenue-by-service",
        title: "Revenue by service",
        description: "Project service mix (count proxy until billed revenue tags)",
        data: revenueByService.map((row) => ({
          name: row.name,
          value: row._count,
        })),
      },
    ],
    lists: [
      {
        id: "profitability",
        title: "Project profitability",
        items: profitability.map((row) => ({
          id: row.id,
          title: row.project.name,
          meta: `Profit ${Math.round(row.profitMinor / 100)} ${currencyCode}`,
          href: "/projects",
        })),
      },
    ],
    activity: [],
  };
}

async function buildHrDashboard(
  organizationId: string,
  range: DashboardDateRange,
  currencyCode: string,
  persona: DashboardPersona,
): Promise<DashboardPayload> {
  const todayStart = new Date();
  todayStart.setUTCHours(0, 0, 0, 0);
  const todayEnd = new Date();
  todayEnd.setUTCHours(23, 59, 59, 999);
  const in30 = new Date(todayStart.getTime() + 30 * 86400000);

  const [
    headcount,
    attendance,
    leave,
    newJoiners,
    probation,
    birthdays,
    expiringDocs,
    openPositions,
    candidatesByStage,
    onboardingTasks,
    assignedAssets,
  ] = await Promise.all([
    prisma.employee.count({
      where: {
        organizationId,
        deletedAt: null,
        employmentStatus: { in: ["ACTIVE", "PROBATION", "NOTICE"] },
      },
    }),
    prisma.attendanceRecord.count({
      where: {
        organizationId,
        date: { gte: todayStart, lte: todayEnd },
        status: { in: ["PRESENT", "WFH", "REMOTE"] },
      },
    }),
    prisma.leaveRequest.count({
      where: {
        organizationId,
        deletedAt: null,
        status: { in: ["PENDING", "APPROVED"] },
        startDate: { lte: range.to },
        endDate: { gte: range.from },
      },
    }),
    prisma.employee.count({
      where: {
        organizationId,
        deletedAt: null,
        joiningDate: { gte: range.from, lte: range.to },
      },
    }),
    prisma.employee.count({
      where: {
        organizationId,
        deletedAt: null,
        employmentStatus: "PROBATION",
        probationEndDate: { lte: in30 },
      },
    }),
    prisma.employee.findMany({
      where: {
        organizationId,
        deletedAt: null,
        dateOfBirth: { not: null },
      },
      select: {
        id: true,
        dateOfBirth: true,
        user: { select: { name: true } },
        employeeCode: true,
      },
      take: 200,
    }),
    prisma.employeeDocument.count({
      where: {
        organizationId,
        deletedAt: null,
        expiresAt: { gte: todayStart, lte: in30 },
      },
    }),
    prisma.recruitmentJob.count({
      where: { organizationId, deletedAt: null, status: "OPEN" },
    }),
    prisma.candidateApplication.groupBy({
      by: ["status"],
      where: { organizationId },
      _count: true,
    }),
    prisma.onboardingTask.count({
      where: {
        checklist: { organizationId },
        completedAt: null,
      },
    }),
    prisma.assetAssignment.count({
      where: { organizationId, returnedAt: null },
    }),
  ]);

  const upcomingBirthdays = birthdays
    .filter((employee) => {
      if (!employee.dateOfBirth) return false;
      const dob = employee.dateOfBirth;
      const next = new Date(
        Date.UTC(todayStart.getUTCFullYear(), dob.getUTCMonth(), dob.getUTCDate()),
      );
      if (next < todayStart) {
        next.setUTCFullYear(next.getUTCFullYear() + 1);
      }
      return next <= in30;
    })
    .slice(0, 8);

  return {
    persona,
    range,
    currencyCode,
    metrics: [
      num("Headcount", headcount),
      num("Attendance today", attendance),
      num("Leave in range", leave),
      num("New joiners", newJoiners),
      num("Probation reviews due", probation),
      num("Expiring documents", expiringDocs),
      num("Open positions", openPositions),
      num("Pending onboarding tasks", onboardingTasks),
      num("Assigned company assets", assignedAssets),
    ],
    charts: [
      {
        id: "candidates-by-stage",
        title: "Candidates by stage",
        data: candidatesByStage.map((row) => ({
          name: row.status,
          value: row._count,
        })),
      },
    ],
    lists: [
      {
        id: "birthdays",
        title: "Upcoming birthdays",
        items: upcomingBirthdays.map((employee) => ({
          id: employee.id,
          title: employee.user?.name ?? employee.employeeCode,
          meta: employee.dateOfBirth?.toISOString().slice(5, 10),
          href: `/employees/${employee.id}`,
        })),
      },
    ],
    activity: [],
  };
}
