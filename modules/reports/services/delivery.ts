import "server-only";

import { prisma } from "@/database";
import type { SessionUser } from "@/permissions";
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
import {
  assertSingleCurrency,
  convertMinorUnits,
  organizationCurrency,
} from "@/modules/reports/currency";

type DeliveryReportInput = {
  key: string;
  definition: ReportDefinition;
  user: SessionUser & { organizationId: string };
  range: ReportDateRange;
};

const ACTIVE_PROJECT_STATUSES = ["ACTIVE", "IN_PROGRESS", "AT_RISK"];
const DONE_STATUSES = ["DONE", "COMPLETED", "APPROVED"];

function percent(numerator: number, denominator: number): number {
  return denominator > 0 ? Math.round((numerator / denominator) * 1000) / 10 : 0;
}

function average(total: number, count: number): number {
  return count > 0 ? Math.round((total / count) * 10) / 10 : 0;
}

function employeeName(employee: {
  employeeCode: string;
  user: { name: string | null; email?: string | null } | null;
}): string {
  return employee.user?.name ?? employee.user?.email ?? employee.employeeCode;
}

async function convertMoney(input: {
  organizationId: string;
  amountMinor: number;
  fromCurrency: string;
  toCurrency: string;
  asOf: Date;
}): Promise<number> {
  const currency = assertSingleCurrency([input.fromCurrency], "Delivery report money row");
  const converted = await convertMinorUnits({
    organizationId: input.organizationId,
    amountMinor: input.amountMinor,
    fromCurrency: currency,
    toCurrency: input.toCurrency,
    asOf: input.asOf,
  });
  return converted.amountMinor;
}

export async function runDeliveryReport(
  input: DeliveryReportInput,
): Promise<ReportPayload> {
  const currencyCode = await organizationCurrency(input.user.organizationId);

  switch (input.key) {
    case "delivery.active-projects":
      return activeProjects(input, currencyCode);
    case "delivery.project-health":
      return projectHealth(input, currencyCode);
    case "delivery.on-time-delivery":
      return onTimeDelivery(input, currencyCode);
    case "delivery.overdue-deliverables":
      return overdueDeliverables(input, currencyCode);
    case "delivery.revision-rate":
      return revisionRate(input, currencyCode);
    case "delivery.employee-utilization":
      return employeeUtilization(input, currencyCode);
    case "delivery.billable-utilization":
      return billableUtilization(input, currencyCode);
    case "delivery.capacity":
      return capacity(input, currencyCode);
    case "delivery.timesheet-compliance":
      return timesheetCompliance(input, currencyCode);
    case "delivery.budget-versus-actual":
      return budgetVersusActual(input, currencyCode);
    case "delivery.margin":
      return margin(input, currencyCode);
    case "delivery.client-feedback":
      return clientFeedback(input, currencyCode);
    default:
      return buildPayload({
        definition: input.definition,
        range: input.range,
        currencyCode,
        summary: `${input.definition.title}: no implementation for ${input.key}.`,
      });
  }
}

async function activeProjects(
  input: DeliveryReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const projects = await prisma.project.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      status: { in: ACTIVE_PROJECT_STATUSES },
    },
    select: {
      id: true,
      name: true,
      code: true,
      status: true,
      startDate: true,
      endDate: true,
      clientAccount: { select: { company: { select: { name: true } } } },
      members: { select: { id: true } },
    },
    orderBy: { updatedAt: "desc" },
  });
  const statusCounts = new Map<string, number>();
  for (const project of projects) {
    statusCounts.set(project.status, (statusCounts.get(project.status) ?? 0) + 1);
  }

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Active projects: ${projects.length} projects are active, in progress, or at risk.`,
    metrics: [metric("Active projects", projects.length, "number")],
    series: seriesFromMap(statusCounts),
    columns: [
      { key: "project", label: "Project" },
      { key: "client", label: "Client" },
      { key: "status", label: "Status" },
      { key: "members", label: "Members", format: "number" },
      { key: "endDate", label: "End date" },
    ],
    rows: projects.map((project) => ({
      id: project.id,
      href: `/projects/${project.id}`,
      values: {
        project: `${project.name} (${project.code})`,
        client: project.clientAccount?.company.name ?? "Unassigned",
        status: project.status,
        members: project.members.length,
        endDate: project.endDate?.toISOString().slice(0, 10) ?? null,
      },
    })),
    drilldownHref: "/projects",
  });
}

async function projectHealth(
  input: DeliveryReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const groups = await prisma.project.groupBy({
    by: ["status"],
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      status: { in: ACTIVE_PROJECT_STATUSES },
    },
    _count: { _all: true },
  });
  const series = groups.map((group) => ({
    label: group.status,
    value: group._count._all,
    href: "/projects",
  }));
  const total = groups.reduce((sum, group) => sum + group._count._all, 0);

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary:
      series.length > 0
        ? accessibleSeriesSummary("Project health", series)
        : "Project health: no active delivery projects found.",
    metrics: [metric("Projects reviewed", total, "number")],
    series,
    columns: [
      { key: "status", label: "Status" },
      { key: "projectCount", label: "Projects", format: "number" },
    ],
    rows: groups.map((group) => ({
      id: group.status,
      href: "/projects",
      values: { status: group.status, projectCount: group._count._all },
    })),
    drilldownHref: "/projects",
  });
}

async function onTimeDelivery(
  input: DeliveryReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const milestones = await prisma.projectMilestone.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      dueDate: { gte: input.range.from, lte: input.range.to },
    },
    select: {
      id: true,
      title: true,
      status: true,
      dueDate: true,
      updatedAt: true,
      project: { select: { id: true, name: true } },
    },
    orderBy: { dueDate: "asc" },
  });
  const completed = milestones.filter((milestone) => DONE_STATUSES.includes(milestone.status));
  const onTime = completed.filter(
    (milestone) => milestone.dueDate && milestone.updatedAt <= milestone.dueDate,
  );

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `On-time delivery: ${percent(onTime.length, completed.length)}% of completed milestones were updated by due date.`,
    metrics: [
      metric("On-time rate", percent(onTime.length, completed.length), "percent"),
      metric("Completed milestones", completed.length, "number"),
      metric("Milestones reviewed", milestones.length, "number"),
    ],
    columns: [
      { key: "project", label: "Project" },
      { key: "milestone", label: "Milestone" },
      { key: "status", label: "Status" },
      { key: "dueDate", label: "Due" },
      { key: "onTime", label: "On time" },
    ],
    rows: milestones.map((milestone) => ({
      id: milestone.id,
      href: `/projects/${milestone.project.id}`,
      values: {
        project: milestone.project.name,
        milestone: milestone.title,
        status: milestone.status,
        dueDate: milestone.dueDate?.toISOString().slice(0, 10) ?? null,
        onTime:
          DONE_STATUSES.includes(milestone.status) &&
          milestone.dueDate !== null &&
          milestone.updatedAt <= milestone.dueDate
            ? "Yes"
            : "No",
      },
    })),
    drilldownHref: "/projects",
  });
}

async function overdueDeliverables(
  input: DeliveryReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const today = new Date();
  today.setUTCHours(0, 0, 0, 0);
  const deliverables = await prisma.deliverable.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      dueDate: { lt: today },
      status: { notIn: DONE_STATUSES },
    },
    select: {
      id: true,
      title: true,
      status: true,
      dueDate: true,
      project: { select: { id: true, name: true } },
    },
    orderBy: { dueDate: "asc" },
  });

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Overdue deliverables: ${deliverables.length} deliverables are past due and not completed.`,
    metrics: [metric("Overdue deliverables", deliverables.length, "number")],
    columns: [
      { key: "project", label: "Project" },
      { key: "deliverable", label: "Deliverable" },
      { key: "status", label: "Status" },
      { key: "dueDate", label: "Due" },
    ],
    rows: deliverables.map((deliverable) => ({
      id: deliverable.id,
      href: `/projects/${deliverable.project.id}`,
      values: {
        project: deliverable.project.name,
        deliverable: deliverable.title,
        status: deliverable.status,
        dueDate: deliverable.dueDate?.toISOString().slice(0, 10) ?? null,
      },
    })),
    drilldownHref: "/projects",
  });
}

async function revisionRate(
  input: DeliveryReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const deliverables = await prisma.deliverable.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      createdAt: { gte: input.range.from, lte: input.range.to },
    },
    select: {
      id: true,
      title: true,
      project: { select: { id: true, name: true } },
      versions: { select: { id: true } },
    },
  });
  const totalVersions = deliverables.reduce(
    (sum, deliverable) => sum + deliverable.versions.length,
    0,
  );

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Revision rate: ${average(totalVersions, deliverables.length)} versions per deliverable across ${deliverables.length} deliverables.`,
    metrics: [
      metric("Average versions", average(totalVersions, deliverables.length), "number"),
      metric("Deliverables", deliverables.length, "number"),
    ],
    columns: [
      { key: "project", label: "Project" },
      { key: "deliverable", label: "Deliverable" },
      { key: "versions", label: "Versions", format: "number" },
    ],
    rows: deliverables.map((deliverable) => ({
      id: deliverable.id,
      href: `/projects/${deliverable.project.id}`,
      values: {
        project: deliverable.project.name,
        deliverable: deliverable.title,
        versions: deliverable.versions.length,
      },
    })),
    drilldownHref: "/projects",
  });
}

async function employeeUtilization(
  input: DeliveryReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const allocations = await prisma.resourceAllocation.findMany({
    where: {
      organizationId: input.user.organizationId,
      startDate: { lte: input.range.to },
      OR: [{ endDate: null }, { endDate: { gte: input.range.from } }],
    },
    select: {
      id: true,
      allocationPct: true,
      employeeId: true,
      employee: {
        select: { id: true, employeeCode: true, user: { select: { name: true, email: true } } },
      },
    },
  });
  const byEmployee = new Map<string, { label: string; values: number[] }>();
  for (const allocation of allocations) {
    const current = byEmployee.get(allocation.employeeId) ?? {
      label: employeeName(allocation.employee),
      values: [],
    };
    current.values.push(allocation.allocationPct);
    byEmployee.set(allocation.employeeId, current);
  }
  const rows = [...byEmployee.entries()].map(([employeeId, values]) => ({
    id: employeeId,
    href: `/employees/${employeeId}`,
    values: {
      employee: values.label,
      allocationPct: average(
        values.values.reduce((sum, value) => sum + value, 0),
        values.values.length,
      ),
      allocationCount: values.values.length,
    },
  }));
  const series = rows.map((row) => ({
    label: String(row.values.employee),
    value: Number(row.values.allocationPct),
    href: row.href,
  }));

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary:
      series.length > 0
        ? accessibleSeriesSummary("Employee utilization", series, "percent")
        : "Employee utilization: no resource allocations overlap the selected range.",
    metrics: [metric("Allocated employees", rows.length, "number")],
    series,
    columns: [
      { key: "employee", label: "Employee" },
      { key: "allocationPct", label: "Average allocation", format: "percent" },
      { key: "allocationCount", label: "Allocations", format: "number" },
    ],
    rows,
    drilldownHref: "/employees",
  });
}

async function billableUtilization(
  input: DeliveryReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const entries = await prisma.timeEntry.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      date: { gte: input.range.from, lte: input.range.to },
    },
    select: {
      id: true,
      hours: true,
      billable: true,
      employeeId: true,
      employee: {
        select: { id: true, employeeCode: true, user: { select: { name: true, email: true } } },
      },
    },
  });
  const byEmployee = new Map<string, { label: string; total: number; billable: number }>();
  for (const entry of entries) {
    const current = byEmployee.get(entry.employeeId) ?? {
      label: employeeName(entry.employee),
      total: 0,
      billable: 0,
    };
    const hours = Number(entry.hours);
    current.total += hours;
    if (entry.billable) current.billable += hours;
    byEmployee.set(entry.employeeId, current);
  }
  const rows = [...byEmployee.entries()].map(([employeeId, values]) => ({
    id: employeeId,
    href: `/employees/${employeeId}`,
    values: {
      employee: values.label,
      totalHours: values.total,
      billableHours: values.billable,
      utilizationPct: percent(values.billable, values.total),
    },
  }));
  const totalHours = rows.reduce((sum, row) => sum + Number(row.values.totalHours), 0);
  const billableHours = rows.reduce((sum, row) => sum + Number(row.values.billableHours), 0);

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Billable utilization: ${percent(billableHours, totalHours)}% billable from ${billableHours} billable hours and ${totalHours} total hours.`,
    metrics: [
      metric("Billable utilization", percent(billableHours, totalHours), "percent"),
      metric("Billable hours", billableHours, "number"),
      metric("Total hours", totalHours, "number"),
    ],
    columns: [
      { key: "employee", label: "Employee" },
      { key: "billableHours", label: "Billable hours", format: "number" },
      { key: "totalHours", label: "Total hours", format: "number" },
      { key: "utilizationPct", label: "Utilization", format: "percent" },
    ],
    rows,
    drilldownHref: "/projects/timesheets",
  });
}

async function capacity(
  input: DeliveryReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const [plans, headcount, allocations] = await Promise.all([
    prisma.capacityPlan.findMany({
      where: {
        organizationId: input.user.organizationId,
        periodStart: { lte: input.range.to },
        periodEnd: { gte: input.range.from },
      },
      select: {
        id: true,
        name: true,
        plannedHours: true,
        periodStart: true,
        periodEnd: true,
        project: { select: { id: true, name: true } },
      },
    }),
    prisma.employee.count({
      where: {
        organizationId: input.user.organizationId,
        deletedAt: null,
        employmentStatus: { in: ["ACTIVE", "PROBATION", "NOTICE"] },
      },
    }),
    prisma.resourceAllocation.findMany({
      where: {
        organizationId: input.user.organizationId,
        startDate: { lte: input.range.to },
        OR: [{ endDate: null }, { endDate: { gte: input.range.from } }],
      },
      select: { allocationPct: true },
    }),
  ]);
  const plannedHours = plans.reduce((sum, plan) => sum + Number(plan.plannedHours), 0);
  const allocatedPctTotal = allocations.reduce(
    (sum, allocation) => sum + allocation.allocationPct,
    0,
  );

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Capacity: ${plannedHours} planned hours, ${headcount} active employees, and ${average(allocatedPctTotal, allocations.length)}% average allocation.`,
    metrics: [
      metric("Planned hours", plannedHours, "number"),
      metric("Active employees", headcount, "number"),
      metric("Average allocation", average(allocatedPctTotal, allocations.length), "percent"),
    ],
    columns: [
      { key: "plan", label: "Plan" },
      { key: "project", label: "Project" },
      { key: "plannedHours", label: "Planned hours", format: "number" },
      { key: "periodStart", label: "Start" },
      { key: "periodEnd", label: "End" },
    ],
    rows: plans.map((plan) => ({
      id: plan.id,
      href: plan.project ? `/projects/${plan.project.id}` : "/projects",
      values: {
        plan: plan.name,
        project: plan.project?.name ?? "Unassigned",
        plannedHours: Number(plan.plannedHours),
        periodStart: plan.periodStart.toISOString().slice(0, 10),
        periodEnd: plan.periodEnd.toISOString().slice(0, 10),
      },
    })),
    drilldownHref: "/projects",
  });
}

async function timesheetCompliance(
  input: DeliveryReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const [employees, entries] = await Promise.all([
    prisma.employee.findMany({
      where: {
        organizationId: input.user.organizationId,
        deletedAt: null,
        employmentStatus: { in: ["ACTIVE", "PROBATION", "NOTICE"] },
      },
      select: {
        id: true,
        employeeCode: true,
        user: { select: { name: true, email: true } },
      },
    }),
    prisma.timeEntry.findMany({
      where: {
        organizationId: input.user.organizationId,
        deletedAt: null,
        date: { gte: input.range.from, lte: input.range.to },
      },
      select: { employeeId: true, hours: true },
    }),
  ]);
  const hoursByEmployee = new Map<string, number>();
  for (const entry of entries) {
    hoursByEmployee.set(
      entry.employeeId,
      (hoursByEmployee.get(entry.employeeId) ?? 0) + Number(entry.hours),
    );
  }
  const compliant = employees.filter((employee) => hoursByEmployee.has(employee.id)).length;

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Timesheet compliance: ${percent(compliant, employees.length)}% of active employees have time entries in the selected range.`,
    metrics: [
      metric("Compliance rate", percent(compliant, employees.length), "percent"),
      metric("Employees with time entries", compliant, "number"),
      metric("Active employees", employees.length, "number"),
    ],
    columns: [
      { key: "employee", label: "Employee" },
      { key: "hours", label: "Hours", format: "number" },
      { key: "hasTimesheet", label: "Has timesheet" },
    ],
    rows: employees.map((employee) => ({
      id: employee.id,
      href: `/employees/${employee.id}`,
      values: {
        employee: employeeName(employee),
        hours: hoursByEmployee.get(employee.id) ?? 0,
        hasTimesheet: hoursByEmployee.has(employee.id) ? "Yes" : "No",
      },
    })),
    drilldownHref: "/projects/timesheets",
  });
}

async function latestProjectSnapshots(
  organizationId: string,
  range: ReportDateRange,
) {
  const snapshots = await prisma.projectProfitabilitySnapshot.findMany({
    where: { organizationId, asOfDate: { lte: range.to } },
    select: {
      id: true,
      projectId: true,
      asOfDate: true,
      revenueMinor: true,
      costMinor: true,
      profitMinor: true,
      currencyCode: true,
      project: {
        select: {
          id: true,
          name: true,
          budgetMinor: true,
          currencyCode: true,
        },
      },
    },
    orderBy: [{ projectId: "asc" }, { asOfDate: "desc" }],
  });
  const latest = new Map<string, (typeof snapshots)[number]>();
  for (const snapshot of snapshots) {
    if (!latest.has(snapshot.projectId)) latest.set(snapshot.projectId, snapshot);
  }
  return [...latest.values()];
}

async function budgetVersusActual(
  input: DeliveryReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const snapshots = await latestProjectSnapshots(input.user.organizationId, input.range);
  const budgets = await prisma.projectBudget.findMany({
    where: { organizationId: input.user.organizationId },
    select: {
      id: true,
      projectId: true,
      amountMinor: true,
      currencyCode: true,
      createdAt: true,
    },
  });
  const budgetByProject = new Map<string, number>();
  for (const budget of budgets) {
    const amountMinor = await convertMoney({
      organizationId: input.user.organizationId,
      amountMinor: budget.amountMinor,
      fromCurrency: budget.currencyCode,
      toCurrency: currencyCode,
      asOf: budget.createdAt,
    });
    budgetByProject.set(budget.projectId, (budgetByProject.get(budget.projectId) ?? 0) + amountMinor);
  }

  const rows: ReportTableRow[] = [];
  for (const snapshot of snapshots) {
    const costMinor = await convertMoney({
      organizationId: input.user.organizationId,
      amountMinor: snapshot.costMinor,
      fromCurrency: snapshot.currencyCode,
      toCurrency: currencyCode,
      asOf: snapshot.asOfDate,
    });
    const fallbackBudget =
      snapshot.project.budgetMinor !== null
        ? await convertMoney({
            organizationId: input.user.organizationId,
            amountMinor: snapshot.project.budgetMinor,
            fromCurrency: snapshot.project.currencyCode,
            toCurrency: currencyCode,
            asOf: snapshot.asOfDate,
          })
        : 0;
    const budgetMinor = budgetByProject.get(snapshot.projectId) ?? fallbackBudget;
    rows.push({
      id: snapshot.id,
      href: `/projects/${snapshot.projectId}`,
      values: {
        project: snapshot.project.name,
        budgetMinor,
        costMinor,
        varianceMinor: budgetMinor - costMinor,
        usedPct: percent(costMinor, budgetMinor),
      },
    });
  }
  const totalBudget = rows.reduce((sum, row) => sum + Number(row.values.budgetMinor ?? 0), 0);
  const totalCost = rows.reduce((sum, row) => sum + Number(row.values.costMinor ?? 0), 0);

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Budget versus actual: ${percent(totalCost, totalBudget)}% of budget used across ${rows.length} projects.`,
    metrics: [
      metric("Budget", totalBudget, "money"),
      metric("Actual cost", totalCost, "money"),
      metric("Budget used", percent(totalCost, totalBudget), "percent"),
    ],
    columns: [
      { key: "project", label: "Project" },
      { key: "budgetMinor", label: "Budget", format: "money", restricted: true },
      { key: "costMinor", label: "Actual cost", format: "money", restricted: true },
      { key: "varianceMinor", label: "Variance", format: "money" },
      { key: "usedPct", label: "Used", format: "percent" },
    ],
    rows,
    drilldownHref: "/projects",
  });
}

async function margin(
  input: DeliveryReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const snapshots = await latestProjectSnapshots(input.user.organizationId, input.range);
  const rows: ReportTableRow[] = [];
  for (const snapshot of snapshots) {
    const revenueMinor = await convertMoney({
      organizationId: input.user.organizationId,
      amountMinor: snapshot.revenueMinor,
      fromCurrency: snapshot.currencyCode,
      toCurrency: currencyCode,
      asOf: snapshot.asOfDate,
    });
    const costMinor = await convertMoney({
      organizationId: input.user.organizationId,
      amountMinor: snapshot.costMinor,
      fromCurrency: snapshot.currencyCode,
      toCurrency: currencyCode,
      asOf: snapshot.asOfDate,
    });
    const profitMinor = revenueMinor - costMinor;
    rows.push({
      id: snapshot.id,
      href: `/projects/${snapshot.projectId}`,
      values: {
        project: snapshot.project.name,
        revenueMinor,
        costMinor,
        profitMinor,
        marginPct: percent(profitMinor, revenueMinor),
      },
    });
  }
  const totalRevenue = rows.reduce((sum, row) => sum + Number(row.values.revenueMinor ?? 0), 0);
  const totalProfit = rows.reduce((sum, row) => sum + Number(row.values.profitMinor ?? 0), 0);

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Margin: ${percent(totalProfit, totalRevenue)}% gross margin across ${rows.length} projects.`,
    metrics: [
      metric("Project revenue", totalRevenue, "money"),
      metric("Project profit", totalProfit, "money"),
      metric("Margin", percent(totalProfit, totalRevenue), "percent"),
    ],
    columns: [
      { key: "project", label: "Project" },
      { key: "revenueMinor", label: "Revenue", format: "money" },
      { key: "costMinor", label: "Cost", format: "money", restricted: true },
      { key: "profitMinor", label: "Profit", format: "money", restricted: true },
      { key: "marginPct", label: "Margin", format: "percent", restricted: true },
    ],
    rows,
    drilldownHref: "/projects",
  });
}

async function clientFeedback(
  input: DeliveryReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const approvals = await prisma.deliverableApproval.findMany({
    where: {
      organizationId: input.user.organizationId,
      createdAt: { gte: input.range.from, lte: input.range.to },
    },
    select: {
      id: true,
      status: true,
      decidedAt: true,
      deliverable: {
        select: {
          title: true,
          project: { select: { id: true, name: true } },
        },
      },
    },
  });
  const counts = new Map<string, number>();
  for (const approval of approvals) {
    counts.set(approval.status, (counts.get(approval.status) ?? 0) + 1);
  }
  const series = seriesFromMap(counts);
  const approved = counts.get("APPROVED") ?? 0;

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Client feedback proxy: ${percent(approved, approvals.length)}% deliverable approvals accepted across ${approvals.length} approval records.`,
    metrics: [
      metric("Approval acceptance rate", percent(approved, approvals.length), "percent"),
      metric("Approval records", approvals.length, "number"),
    ],
    series,
    columns: [
      { key: "project", label: "Project" },
      { key: "deliverable", label: "Deliverable" },
      { key: "status", label: "Status" },
      { key: "decidedAt", label: "Decided" },
    ],
    rows: approvals.map((approval) => ({
      id: approval.id,
      href: `/projects/${approval.deliverable.project.id}`,
      values: {
        project: approval.deliverable.project.name,
        deliverable: approval.deliverable.title,
        status: approval.status,
        decidedAt: approval.decidedAt?.toISOString().slice(0, 10) ?? null,
      },
    })),
    drilldownHref: "/projects",
  });
}

