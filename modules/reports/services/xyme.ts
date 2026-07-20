import "server-only";

import type { MembershipRole, XYMECategory } from "@prisma/client";

import { prisma } from "@/database";
import type { SessionUser } from "@/permissions";
import { hasPermission } from "@/permissions";
import type {
  ReportDateRange,
  ReportDefinition,
  ReportPayload,
  ReportTableRow,
} from "@/modules/reports/types";
import {
  accessibleSeriesSummary,
  buildPayload,
  metric,
  seriesFromMap,
} from "@/modules/reports/helpers";
import { organizationCurrency } from "@/modules/reports/currency";

type XymeReportInput = {
  key: string;
  definition: ReportDefinition;
  user: SessionUser & { organizationId: string };
  range: ReportDateRange;
};

function average(values: number[]): number {
  return values.length > 0
    ? Math.round(values.reduce((sum, value) => sum + value, 0) / values.length)
    : 0;
}

function averageDecimal(values: number[]): number {
  return values.length > 0
    ? Math.round((values.reduce((sum, value) => sum + value, 0) / values.length) * 10) / 10
    : 0;
}

function hoursBetween(from: Date, to: Date): number {
  return Math.max(0, Math.round((to.getTime() - from.getTime()) / 3600000));
}

async function currentEmployeeId(user: SessionUser & { organizationId: string }) {
  const employee = await prisma.employee.findFirst({
    where: { organizationId: user.organizationId, userId: user.id, deletedAt: null },
    select: { id: true },
  });
  return employee?.id ?? null;
}

function employeeName(employee: {
  employeeCode: string;
  user: { name: string | null; email?: string | null } | null;
}): string {
  return employee.user?.name ?? employee.user?.email ?? employee.employeeCode;
}

export async function runXymeReport(input: XymeReportInput): Promise<ReportPayload> {
  const currencyCode = await organizationCurrency(input.user.organizationId);

  switch (input.key) {
    case "xyme.completion-company":
      return completionCompany(input, currencyCode);
    case "xyme.completion-department":
      return completionDepartment(input, currencyCode);
    case "xyme.completion-manager":
      return completionManager(input, currencyCode);
    case "xyme.average-x":
      return averageCategory(input, currencyCode, "X");
    case "xyme.average-y":
      return averageCategory(input, currencyCode, "Y");
    case "xyme.average-me":
      return averageCategory(input, currencyCode, "ME");
    case "xyme.approval-turnaround":
      return approvalTurnaround(input, currencyCode);
    case "xyme.missing-check-ins":
      return missingCheckIns(input, currencyCode);
    case "xyme.qoq-trend":
      return qoqTrend(input, currencyCode);
    case "xyme.employee-drilldown":
      return employeeDrilldown(input, currencyCode);
    default:
      return buildPayload({
        definition: input.definition,
        range: input.range,
        currencyCode,
        summary: `${input.definition.title}: no implementation for ${input.key}.`,
      });
  }
}

async function completionCompany(
  input: XymeReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const goals = await prisma.xYMEGoal.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      plan: {
        deletedAt: null,
        cycle: {
          deletedAt: null,
          startDate: { lte: input.range.to },
          endDate: { gte: input.range.from },
        },
      },
    },
    select: { id: true, category: true, progressPct: true },
  });
  const categoryMap = new Map<string, number[]>();
  for (const goal of goals) {
    const values = categoryMap.get(goal.category) ?? [];
    values.push(goal.progressPct);
    categoryMap.set(goal.category, values);
  }
  const rows = [...categoryMap.entries()].map(([category, values]) => ({
    id: category,
    values: {
      category,
      goalCount: values.length,
      averageProgressPct: average(values),
    },
    href: "/xyme",
  }));
  const companyAverage = average(goals.map((goal) => goal.progressPct));

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `XYME company completion: ${companyAverage}% average progress across ${goals.length} goals.`,
    metrics: [
      metric("Company XYME progress", companyAverage, "percent"),
      metric("Goals", goals.length, "number"),
    ],
    series: rows.map((row) => ({
      label: String(row.values.category),
      value: Number(row.values.averageProgressPct),
      href: row.href,
    })),
    columns: [
      { key: "category", label: "Category" },
      { key: "goalCount", label: "Goals", format: "number" },
      { key: "averageProgressPct", label: "Average progress", format: "percent" },
    ],
    rows,
    drilldownHref: "/xyme",
  });
}

async function completionDepartment(
  input: XymeReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const plans = await prisma.xYMEPlan.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      cycle: {
        deletedAt: null,
        startDate: { lte: input.range.to },
        endDate: { gte: input.range.from },
      },
    },
    select: {
      id: true,
      employee: {
        select: {
          department: { select: { id: true, name: true } },
        },
      },
      goals: { where: { deletedAt: null }, select: { progressPct: true } },
    },
  });

  const byDepartment = new Map<string, { id: string; progress: number[]; plans: number }>();
  for (const plan of plans) {
    const department = plan.employee.department;
    const label = department?.name ?? "Unassigned";
    const current = byDepartment.get(label) ?? {
      id: department?.id ?? "unassigned",
      progress: [],
      plans: 0,
    };
    current.progress.push(...plan.goals.map((goal) => goal.progressPct));
    current.plans += 1;
    byDepartment.set(label, current);
  }

  const rows = [...byDepartment.entries()].map(([department, values]) => ({
    id: values.id,
    href: "/departments",
    values: {
      department,
      planCount: values.plans,
      goalCount: values.progress.length,
      averageProgressPct: average(values.progress),
    },
  }));
  const series = rows.map((row) => ({
    label: String(row.values.department),
    value: Number(row.values.averageProgressPct),
    href: row.href,
  }));

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary:
      series.length > 0
        ? accessibleSeriesSummary("XYME completion by department", series, "percent")
        : "XYME completion by department: no active plans in the selected range.",
    metrics: [metric("Departments", rows.length, "number")],
    series,
    columns: [
      { key: "department", label: "Department" },
      { key: "planCount", label: "Plans", format: "number" },
      { key: "goalCount", label: "Goals", format: "number" },
      { key: "averageProgressPct", label: "Average progress", format: "percent" },
    ],
    rows,
    drilldownHref: "/departments",
  });
}

async function completionManager(
  input: XymeReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const plans = await prisma.xYMEPlan.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      cycle: {
        deletedAt: null,
        startDate: { lte: input.range.to },
        endDate: { gte: input.range.from },
      },
    },
    select: {
      id: true,
      employee: {
        select: {
          reportingManager: {
            select: {
              id: true,
              employeeCode: true,
              user: { select: { name: true, email: true } },
            },
          },
        },
      },
      goals: { where: { deletedAt: null }, select: { progressPct: true } },
    },
  });

  const byManager = new Map<string, { id: string; progress: number[]; plans: number }>();
  for (const plan of plans) {
    const manager = plan.employee.reportingManager;
    const label = manager ? employeeName(manager) : "Unassigned";
    const current = byManager.get(label) ?? {
      id: manager?.id ?? "unassigned",
      progress: [],
      plans: 0,
    };
    current.progress.push(...plan.goals.map((goal) => goal.progressPct));
    current.plans += 1;
    byManager.set(label, current);
  }

  const rows = [...byManager.entries()].map(([manager, values]) => ({
    id: values.id,
    href: values.id === "unassigned" ? "/employees" : `/employees/${values.id}`,
    values: {
      manager,
      planCount: values.plans,
      goalCount: values.progress.length,
      averageProgressPct: average(values.progress),
    },
  }));
  const series = rows.map((row) => ({
    label: String(row.values.manager),
    value: Number(row.values.averageProgressPct),
    href: row.href,
  }));

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary:
      series.length > 0
        ? accessibleSeriesSummary("XYME completion by manager", series, "percent")
        : "XYME completion by manager: no active plans in the selected range.",
    metrics: [metric("Managers", rows.length, "number")],
    series,
    columns: [
      { key: "manager", label: "Manager" },
      { key: "planCount", label: "Plans", format: "number" },
      { key: "goalCount", label: "Goals", format: "number" },
      { key: "averageProgressPct", label: "Average progress", format: "percent" },
    ],
    rows,
    drilldownHref: "/employees",
  });
}

async function averageCategory(
  input: XymeReportInput,
  currencyCode: string,
  category: XYMECategory,
): Promise<ReportPayload> {
  const goals = await prisma.xYMEGoal.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      category,
      plan: {
        deletedAt: null,
        cycle: {
          deletedAt: null,
          startDate: { lte: input.range.to },
          endDate: { gte: input.range.from },
        },
      },
    },
    select: {
      id: true,
      title: true,
      progressPct: true,
      plan: {
        select: {
          employee: {
            select: {
              id: true,
              employeeCode: true,
              user: { select: { name: true, email: true } },
            },
          },
        },
      },
    },
    orderBy: { progressPct: "desc" },
  });

  const avg = average(goals.map((goal) => goal.progressPct));

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Average ${category} score: ${avg}% across ${goals.length} goals.`,
    metrics: [
      metric(`Average ${category} score`, avg, "percent"),
      metric("Goal count", goals.length, "number"),
    ],
    columns: [
      { key: "employee", label: "Employee" },
      { key: "goal", label: "Goal" },
      { key: "progressPct", label: "Progress", format: "percent" },
    ],
    rows: goals.slice(0, 100).map((goal) => ({
      id: goal.id,
      href: `/employees/${goal.plan.employee.id}`,
      values: {
        employee: employeeName(goal.plan.employee),
        goal: goal.title,
        progressPct: goal.progressPct,
      },
    })),
    drilldownHref: "/xyme",
  });
}

async function approvalTurnaround(
  input: XymeReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const approvals = await prisma.xYMEApproval.findMany({
    where: {
      organizationId: input.user.organizationId,
      decidedAt: { gte: input.range.from, lte: input.range.to },
      status: { in: ["APPROVED", "REJECTED"] },
      plan: { deletedAt: null, submittedAt: { not: null } },
    },
    select: {
      id: true,
      status: true,
      decidedAt: true,
      plan: {
        select: {
          submittedAt: true,
          employee: {
            select: {
              id: true,
              employeeCode: true,
              user: { select: { name: true, email: true } },
            },
          },
        },
      },
    },
    orderBy: { decidedAt: "desc" },
  });
  const rows: ReportTableRow[] = approvals.map((approval) => {
    const submittedAt = approval.plan.submittedAt ?? approval.decidedAt ?? input.range.from;
    const decidedAt = approval.decidedAt ?? submittedAt;
    return {
      id: approval.id,
      href: `/employees/${approval.plan.employee.id}`,
      values: {
        employee: employeeName(approval.plan.employee),
        status: approval.status,
        submittedAt: submittedAt.toISOString().slice(0, 10),
        decidedAt: decidedAt.toISOString().slice(0, 10),
        turnaroundHours: hoursBetween(submittedAt, decidedAt),
      },
    };
  });
  const averageHours = averageDecimal(
    rows.map((row) => Number(row.values.turnaroundHours ?? 0)),
  );

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Goal approval turnaround time: ${averageHours} average hours across ${rows.length} decisions.`,
    metrics: [
      metric("Average turnaround", averageHours, "number"),
      metric("Approval decisions", rows.length, "number"),
    ],
    columns: [
      { key: "employee", label: "Employee" },
      { key: "status", label: "Decision" },
      { key: "submittedAt", label: "Submitted" },
      { key: "decidedAt", label: "Decided" },
      { key: "turnaroundHours", label: "Turnaround hours", format: "number" },
    ],
    rows,
    drilldownHref: "/xyme",
  });
}

async function missingCheckIns(
  input: XymeReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const cutoff = new Date(Date.now() - 7 * 86400000);
  const plans = await prisma.xYMEPlan.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      status: "APPROVED",
      cycle: {
        deletedAt: null,
        startDate: { lte: input.range.to },
        endDate: { gte: input.range.from },
      },
    },
    select: {
      id: true,
      employee: {
        select: {
          id: true,
          employeeCode: true,
          user: { select: { name: true, email: true } },
        },
      },
      checkIns: {
        orderBy: { checkedInAt: "desc" },
        take: 1,
        select: { checkedInAt: true },
      },
    },
  });
  const missing = plans.filter(
    (plan) => !plan.checkIns[0] || plan.checkIns[0].checkedInAt < cutoff,
  );

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Missing check-ins: ${missing.length} approved plans have no check-in in the last 7 days.`,
    metrics: [
      metric("Missing check-ins", missing.length, "number"),
      metric("Approved plans reviewed", plans.length, "number"),
    ],
    columns: [
      { key: "employee", label: "Employee" },
      { key: "lastCheckIn", label: "Last check-in" },
    ],
    rows: missing.map((plan) => ({
      id: plan.id,
      href: `/employees/${plan.employee.id}`,
      values: {
        employee: employeeName(plan.employee),
        lastCheckIn: plan.checkIns[0]?.checkedInAt.toISOString().slice(0, 10) ?? null,
      },
    })),
    drilldownHref: "/xyme",
  });
}

async function qoqTrend(
  input: XymeReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const cycles = await prisma.xYMECycle.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      startDate: { lte: input.range.to },
      endDate: { gte: input.range.from },
    },
    select: {
      id: true,
      name: true,
      quarter: true,
      plans: {
        where: { deletedAt: null },
        select: {
          goals: { where: { deletedAt: null }, select: { progressPct: true } },
        },
      },
    },
    orderBy: [{ startDate: "asc" }],
  });

  const trend = new Map<string, number>();
  const rows = cycles.map((cycle) => {
    const progress = cycle.plans.flatMap((plan) => plan.goals.map((goal) => goal.progressPct));
    const avg = average(progress);
    trend.set(cycle.name, avg);
    return {
      id: cycle.id,
      href: "/xyme",
      values: {
        cycle: cycle.name,
        quarter: cycle.quarter,
        planCount: cycle.plans.length,
        goalCount: progress.length,
        averageProgressPct: avg,
      },
    };
  });
  const series = seriesFromMap(trend);

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary:
      series.length > 0
        ? accessibleSeriesSummary("Quarter-over-quarter XYME trend", series, "percent")
        : "Quarter-over-quarter XYME trend: no cycles overlap the selected range.",
    metrics: [metric("Cycles", rows.length, "number")],
    series,
    columns: [
      { key: "cycle", label: "Cycle" },
      { key: "quarter", label: "Quarter", format: "number" },
      { key: "planCount", label: "Plans", format: "number" },
      { key: "goalCount", label: "Goals", format: "number" },
      { key: "averageProgressPct", label: "Average progress", format: "percent" },
    ],
    rows,
    drilldownHref: "/xyme",
  });
}

async function employeeDrilldown(
  input: XymeReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const canViewEmployees = hasPermission(
    input.user.role as MembershipRole | null,
    "employees:view",
  );
  const ownEmployeeId = canViewEmployees ? null : await currentEmployeeId(input.user);
  const plans = await prisma.xYMEPlan.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      ...(ownEmployeeId ? { employeeId: ownEmployeeId } : {}),
      ...(!canViewEmployees && !ownEmployeeId ? { employeeId: "__no_employee__" } : {}),
      cycle: {
        deletedAt: null,
        startDate: { lte: input.range.to },
        endDate: { gte: input.range.from },
      },
    },
    select: {
      id: true,
      status: true,
      employee: {
        select: {
          id: true,
          employeeCode: true,
          user: { select: { name: true, email: true } },
          department: { select: { name: true } },
        },
      },
      goals: {
        where: { deletedAt: null },
        select: { category: true, progressPct: true },
      },
    },
  });

  const rows = plans.map((plan) => {
    const xGoals = plan.goals.filter((goal) => goal.category === "X");
    const yGoals = plan.goals.filter((goal) => goal.category === "Y");
    const meGoals = plan.goals.filter((goal) => goal.category === "ME");
    return {
      id: plan.id,
      href: `/employees/${plan.employee.id}`,
      values: {
        employee: employeeName(plan.employee),
        department: plan.employee.department?.name ?? "Unassigned",
        status: plan.status,
        goalCount: plan.goals.length,
        averageProgressPct: average(plan.goals.map((goal) => goal.progressPct)),
        xProgressPct: average(xGoals.map((goal) => goal.progressPct)),
        yProgressPct: average(yGoals.map((goal) => goal.progressPct)),
        meProgressPct: average(meGoals.map((goal) => goal.progressPct)),
      },
    };
  });
  const overall = average(rows.map((row) => Number(row.values.averageProgressPct)));

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Employee-level XYME drill-down: ${overall}% average progress across ${rows.length} visible employees.`,
    metrics: [
      metric("Visible employees", rows.length, "number"),
      metric("Average progress", overall, "percent"),
    ],
    columns: [
      { key: "employee", label: "Employee" },
      { key: "department", label: "Department" },
      { key: "status", label: "Status" },
      { key: "goalCount", label: "Goals", format: "number" },
      { key: "averageProgressPct", label: "Average", format: "percent" },
      { key: "xProgressPct", label: "X", format: "percent" },
      { key: "yProgressPct", label: "Y", format: "percent" },
      { key: "meProgressPct", label: "ME", format: "percent" },
    ],
    rows,
    drilldownHref: canViewEmployees ? "/employees" : "/xyme",
  });
}

