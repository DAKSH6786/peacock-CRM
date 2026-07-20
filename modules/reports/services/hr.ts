import "server-only";

import type { EmploymentStatus } from "@prisma/client";

import { prisma } from "@/database";
import type { SessionUser } from "@/permissions";
import type {
  ReportDateRange,
  ReportDefinition,
  ReportPayload,
} from "@/modules/reports/types";
import {
  accessibleSeriesSummary,
  buildPayload,
  metric,
  seriesFromMap,
} from "@/modules/reports/helpers";
import { organizationCurrency } from "@/modules/reports/currency";

type HrReportInput = {
  key: string;
  definition: ReportDefinition;
  user: SessionUser & { organizationId: string };
  range: ReportDateRange;
};

const ACTIVE_EMPLOYMENT_STATUSES: EmploymentStatus[] = [
  "ACTIVE",
  "PROBATION",
  "NOTICE",
];
const PRESENT_ATTENDANCE_STATUSES = ["PRESENT", "WFH", "REMOTE"];

function average(total: number, count: number): number {
  return count > 0 ? Math.round((total / count) * 10) / 10 : 0;
}

function percent(numerator: number, denominator: number): number {
  return denominator > 0 ? Math.round((numerator / denominator) * 1000) / 10 : 0;
}

function daysBetween(from: Date, to: Date): number {
  return Math.max(0, Math.round((to.getTime() - from.getTime()) / 86400000));
}

function employeeName(employee: {
  employeeCode: string;
  user: { name: string | null; email?: string | null } | null;
}): string {
  return employee.user?.name ?? employee.user?.email ?? employee.employeeCode;
}

export async function runHrReport(input: HrReportInput): Promise<ReportPayload> {
  const currencyCode = await organizationCurrency(input.user.organizationId);

  switch (input.key) {
    case "hr.headcount":
      return headcount(input, currencyCode);
    case "hr.department-distribution":
      return departmentDistribution(input, currencyCode);
    case "hr.employment-type":
      return employmentType(input, currencyCode);
    case "hr.attendance":
      return attendance(input, currencyCode);
    case "hr.late-arrivals":
      return lateArrivals(input, currencyCode);
    case "hr.absence":
      return absence(input, currencyCode);
    case "hr.leave-utilization":
      return leaveUtilization(input, currencyCode);
    case "hr.attrition":
      return attrition(input, currencyCode);
    case "hr.probation-completion":
      return probationCompletion(input, currencyCode);
    case "hr.recruitment-funnel":
      return recruitmentFunnel(input, currencyCode);
    case "hr.time-to-hire":
      return timeToHire(input, currencyCode);
    case "hr.onboarding-completion":
      return onboardingCompletion(input, currencyCode);
    case "hr.asset-allocation":
      return assetAllocation(input, currencyCode);
    case "hr.document-expiry":
      return documentExpiry(input, currencyCode);
    default:
      return buildPayload({
        definition: input.definition,
        range: input.range,
        currencyCode,
        summary: `${input.definition.title}: no implementation for ${input.key}.`,
      });
  }
}

async function headcount(input: HrReportInput, currencyCode: string): Promise<ReportPayload> {
  const employees = await prisma.employee.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      employmentStatus: { in: ACTIVE_EMPLOYMENT_STATUSES },
    },
    select: {
      id: true,
      employmentStatus: true,
      employmentType: true,
      joiningDate: true,
      employeeCode: true,
      user: { select: { name: true, email: true } },
      department: { select: { name: true } },
    },
    orderBy: { joiningDate: "asc" },
  });
  const statusCounts = new Map<string, number>();
  for (const employee of employees) {
    statusCounts.set(
      employee.employmentStatus,
      (statusCounts.get(employee.employmentStatus) ?? 0) + 1,
    );
  }

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Headcount: ${employees.length} active employees across ${statusCounts.size} employment statuses.`,
    metrics: [metric("Headcount", employees.length, "number")],
    series: seriesFromMap(statusCounts),
    columns: [
      { key: "employee", label: "Employee" },
      { key: "department", label: "Department" },
      { key: "employmentStatus", label: "Status" },
      { key: "employmentType", label: "Type" },
      { key: "joiningDate", label: "Joined" },
    ],
    rows: employees.slice(0, 100).map((employee) => ({
      id: employee.id,
      href: `/employees/${employee.id}`,
      values: {
        employee: employeeName(employee),
        department: employee.department?.name ?? "Unassigned",
        employmentStatus: employee.employmentStatus,
        employmentType: employee.employmentType,
        joiningDate: employee.joiningDate.toISOString().slice(0, 10),
      },
    })),
    drilldownHref: "/employees",
  });
}

async function departmentDistribution(
  input: HrReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const employees = await prisma.employee.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      employmentStatus: { in: ACTIVE_EMPLOYMENT_STATUSES },
    },
    select: { id: true, department: { select: { id: true, name: true } } },
  });
  const counts = new Map<string, number>();
  const ids = new Map<string, string>();
  for (const employee of employees) {
    const label = employee.department?.name ?? "Unassigned";
    ids.set(label, employee.department?.id ?? "unassigned");
    counts.set(label, (counts.get(label) ?? 0) + 1);
  }
  const series = seriesFromMap(counts);

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary:
      series.length > 0
        ? accessibleSeriesSummary("Department distribution", series)
        : "Department distribution: no active employees found.",
    metrics: [metric("Headcount", employees.length, "number")],
    series,
    columns: [
      { key: "department", label: "Department" },
      { key: "headcount", label: "Headcount", format: "number" },
    ],
    rows: series.map((point) => ({
      id: ids.get(point.label) ?? point.label,
      href: "/departments",
      values: { department: point.label, headcount: point.value },
    })),
    drilldownHref: "/departments",
  });
}

async function employmentType(
  input: HrReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const groups = await prisma.employee.groupBy({
    by: ["employmentType"],
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      employmentStatus: { in: ACTIVE_EMPLOYMENT_STATUSES },
    },
    _count: { _all: true },
  });
  const series = groups.map((group) => ({
    label: group.employmentType,
    value: group._count._all,
    href: "/employees",
  }));
  const total = groups.reduce((sum, group) => sum + group._count._all, 0);

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary:
      series.length > 0
        ? accessibleSeriesSummary("Employment type", series)
        : "Employment type: no active employees found.",
    metrics: [metric("Headcount", total, "number")],
    series,
    columns: [
      { key: "employmentType", label: "Employment type" },
      { key: "headcount", label: "Headcount", format: "number" },
    ],
    rows: groups.map((group) => ({
      id: group.employmentType,
      href: "/employees",
      values: { employmentType: group.employmentType, headcount: group._count._all },
    })),
    drilldownHref: "/employees",
  });
}

async function attendance(input: HrReportInput, currencyCode: string): Promise<ReportPayload> {
  const groups = await prisma.attendanceRecord.groupBy({
    by: ["status"],
    where: {
      organizationId: input.user.organizationId,
      date: { gte: input.range.from, lte: input.range.to },
    },
    _count: { _all: true },
  });
  const series = groups.map((group) => ({
    label: group.status,
    value: group._count._all,
    href: "/hr/attendance",
  }));
  const total = groups.reduce((sum, group) => sum + group._count._all, 0);
  const present = groups
    .filter((group) => PRESENT_ATTENDANCE_STATUSES.includes(group.status))
    .reduce((sum, group) => sum + group._count._all, 0);

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Attendance: ${present} present/WFH/remote records out of ${total} attendance records.`,
    metrics: [
      metric("Attendance records", total, "number"),
      metric("Presence rate", percent(present, total), "percent"),
    ],
    series,
    columns: [
      { key: "status", label: "Status" },
      { key: "recordCount", label: "Records", format: "number" },
    ],
    rows: groups.map((group) => ({
      id: group.status,
      href: "/hr/attendance",
      values: { status: group.status, recordCount: group._count._all },
    })),
    drilldownHref: "/hr/attendance",
  });
}

async function lateArrivals(
  input: HrReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const rows = await prisma.attendanceRecord.findMany({
    where: {
      organizationId: input.user.organizationId,
      date: { gte: input.range.from, lte: input.range.to },
      status: "LATE",
    },
    select: {
      id: true,
      date: true,
      checkInAt: true,
      employee: {
        select: { id: true, employeeCode: true, user: { select: { name: true, email: true } } },
      },
    },
    orderBy: { date: "desc" },
  });

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Late arrivals: ${rows.length} late attendance records in the selected range.`,
    metrics: [metric("Late arrivals", rows.length, "number")],
    columns: [
      { key: "employee", label: "Employee" },
      { key: "date", label: "Date" },
      { key: "checkInAt", label: "Check-in" },
    ],
    rows: rows.map((row) => ({
      id: row.id,
      href: `/employees/${row.employee.id}`,
      values: {
        employee: employeeName(row.employee),
        date: row.date.toISOString().slice(0, 10),
        checkInAt: row.checkInAt?.toISOString() ?? null,
      },
    })),
    drilldownHref: "/hr/attendance",
  });
}

async function absence(input: HrReportInput, currencyCode: string): Promise<ReportPayload> {
  const records = await prisma.attendanceRecord.findMany({
    where: {
      organizationId: input.user.organizationId,
      date: { gte: input.range.from, lte: input.range.to },
      status: "ABSENT",
    },
    select: {
      id: true,
      date: true,
      employee: {
        select: { id: true, employeeCode: true, user: { select: { name: true, email: true } } },
      },
    },
  });
  const byDate = new Map<string, number>();
  for (const record of records) {
    const key = record.date.toISOString().slice(0, 10);
    byDate.set(key, (byDate.get(key) ?? 0) + 1);
  }
  const series = seriesFromMap(byDate);

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary:
      series.length > 0
        ? accessibleSeriesSummary("Absence by day", series)
        : "Absence: no absent attendance records in the selected range.",
    metrics: [metric("Absence records", records.length, "number")],
    series,
    columns: [
      { key: "employee", label: "Employee" },
      { key: "date", label: "Date" },
    ],
    rows: records.slice(0, 100).map((record) => ({
      id: record.id,
      href: `/employees/${record.employee.id}`,
      values: {
        employee: employeeName(record.employee),
        date: record.date.toISOString().slice(0, 10),
      },
    })),
    drilldownHref: "/hr/attendance",
  });
}

async function leaveUtilization(
  input: HrReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const [requests, balances] = await Promise.all([
    prisma.leaveRequest.findMany({
      where: {
        organizationId: input.user.organizationId,
        deletedAt: null,
        status: "APPROVED",
        startDate: { lte: input.range.to },
        endDate: { gte: input.range.from },
      },
      select: {
        id: true,
        days: true,
        leaveType: { select: { id: true, name: true } },
      },
    }),
    prisma.leaveBalance.findMany({
      where: {
        organizationId: input.user.organizationId,
        year: input.range.from.getUTCFullYear(),
      },
      select: {
        id: true,
        balanceDays: true,
        leaveType: { select: { id: true, name: true } },
      },
    }),
  ]);

  const utilized = new Map<string, { id: string; days: number }>();
  const remaining = new Map<string, number>();
  for (const request of requests) {
    const label = request.leaveType.name;
    const current = utilized.get(label) ?? { id: request.leaveType.id, days: 0 };
    current.days += Number(request.days);
    utilized.set(label, current);
  }
  for (const balance of balances) {
    remaining.set(
      balance.leaveType.name,
      (remaining.get(balance.leaveType.name) ?? 0) + Number(balance.balanceDays),
    );
  }
  const labels = new Set([...utilized.keys(), ...remaining.keys()]);
  const rows = [...labels].map((label) => {
    const usedDays = utilized.get(label)?.days ?? 0;
    const balanceDays = remaining.get(label) ?? 0;
    return {
      id: utilized.get(label)?.id ?? label,
      href: "/hr/leaves",
      values: {
        leaveType: label,
        usedDays,
        balanceDays,
        utilizationPct: percent(usedDays, usedDays + balanceDays),
      },
    };
  });
  const totalUsed = rows.reduce((sum, row) => sum + Number(row.values.usedDays), 0);

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Leave utilization: ${totalUsed} approved leave days used across ${rows.length} leave types.`,
    metrics: [
      metric("Approved leave days", totalUsed, "number"),
      metric("Leave types", rows.length, "number"),
    ],
    columns: [
      { key: "leaveType", label: "Leave type" },
      { key: "usedDays", label: "Used days", format: "number" },
      { key: "balanceDays", label: "Balance days", format: "number" },
      { key: "utilizationPct", label: "Utilization", format: "percent" },
    ],
    rows,
    drilldownHref: "/hr/leaves",
  });
}

async function attrition(input: HrReportInput, currencyCode: string): Promise<ReportPayload> {
  const employees = await prisma.employee.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      exitDate: { gte: input.range.from, lte: input.range.to },
    },
    select: {
      id: true,
      employeeCode: true,
      exitDate: true,
      exitReason: true,
      user: { select: { name: true, email: true } },
      department: { select: { name: true } },
    },
    orderBy: { exitDate: "desc" },
  });
  const headcountAtEnd = await prisma.employee.count({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      joiningDate: { lte: input.range.to },
    },
  });

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Attrition: ${employees.length} employees exited; attrition rate is ${percent(employees.length, headcountAtEnd)}%.`,
    metrics: [
      metric("Exits", employees.length, "number"),
      metric("Attrition rate", percent(employees.length, headcountAtEnd), "percent"),
    ],
    columns: [
      { key: "employee", label: "Employee" },
      { key: "department", label: "Department" },
      { key: "exitDate", label: "Exit date" },
      { key: "exitReason", label: "Reason" },
    ],
    rows: employees.map((employee) => ({
      id: employee.id,
      href: `/employees/${employee.id}`,
      values: {
        employee: employeeName(employee),
        department: employee.department?.name ?? "Unassigned",
        exitDate: employee.exitDate?.toISOString().slice(0, 10) ?? null,
        exitReason: employee.exitReason ?? null,
      },
    })),
    drilldownHref: "/employees",
  });
}

async function probationCompletion(
  input: HrReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const employees = await prisma.employee.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      employmentStatus: "PROBATION",
      probationEndDate: { gte: input.range.from, lte: input.range.to },
    },
    select: {
      id: true,
      employeeCode: true,
      probationEndDate: true,
      joiningDate: true,
      user: { select: { name: true, email: true } },
      reportingManager: {
        select: { id: true, employeeCode: true, user: { select: { name: true, email: true } } },
      },
    },
    orderBy: { probationEndDate: "asc" },
  });

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Probation completion: ${employees.length} probation end dates fall in the selected range.`,
    metrics: [metric("Probation reviews due", employees.length, "number")],
    columns: [
      { key: "employee", label: "Employee" },
      { key: "manager", label: "Manager" },
      { key: "joiningDate", label: "Joined" },
      { key: "probationEndDate", label: "Probation ends" },
    ],
    rows: employees.map((employee) => ({
      id: employee.id,
      href: `/employees/${employee.id}`,
      values: {
        employee: employeeName(employee),
        manager: employee.reportingManager ? employeeName(employee.reportingManager) : "Unassigned",
        joiningDate: employee.joiningDate.toISOString().slice(0, 10),
        probationEndDate: employee.probationEndDate?.toISOString().slice(0, 10) ?? null,
      },
    })),
    drilldownHref: "/employees",
  });
}

async function recruitmentFunnel(
  input: HrReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const groups = await prisma.candidateApplication.groupBy({
    by: ["status"],
    where: {
      organizationId: input.user.organizationId,
      appliedAt: { gte: input.range.from, lte: input.range.to },
    },
    _count: { _all: true },
  });
  const series = groups.map((group) => ({
    label: group.status,
    value: group._count._all,
    href: "/hr/recruitment",
  }));
  const total = groups.reduce((sum, group) => sum + group._count._all, 0);

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary:
      series.length > 0
        ? accessibleSeriesSummary("Recruitment funnel", series)
        : "Recruitment funnel: no applications in the selected range.",
    metrics: [metric("Applications", total, "number")],
    series,
    columns: [
      { key: "stage", label: "Stage" },
      { key: "candidateCount", label: "Candidates", format: "number" },
    ],
    rows: groups.map((group) => ({
      id: group.status,
      href: "/hr/recruitment",
      values: { stage: group.status, candidateCount: group._count._all },
    })),
    drilldownHref: "/hr/recruitment",
  });
}

async function timeToHire(input: HrReportInput, currencyCode: string): Promise<ReportPayload> {
  const offers = await prisma.offer.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      status: "APPROVED",
      acceptedAt: { gte: input.range.from, lte: input.range.to },
    },
    select: {
      id: true,
      offeredAt: true,
      acceptedAt: true,
      application: {
        select: {
          appliedAt: true,
          candidate: { select: { firstName: true, lastName: true } },
          job: { select: { title: true } },
        },
      },
    },
  });
  const rows = offers.map((offer) => {
    const acceptedAt = offer.acceptedAt ?? offer.offeredAt;
    return {
      id: offer.id,
      href: "/hr/recruitment",
      values: {
        candidate: `${offer.application.candidate.firstName} ${offer.application.candidate.lastName ?? ""}`.trim(),
        job: offer.application.job.title,
        appliedAt: offer.application.appliedAt.toISOString().slice(0, 10),
        acceptedAt: acceptedAt.toISOString().slice(0, 10),
        daysToHire: daysBetween(offer.application.appliedAt, acceptedAt),
      },
    };
  });
  const totalDays = rows.reduce((sum, row) => sum + Number(row.values.daysToHire), 0);

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Time to hire: ${average(totalDays, rows.length)} average days across ${rows.length} accepted offers.`,
    metrics: [
      metric("Average days to hire", average(totalDays, rows.length), "days"),
      metric("Accepted offers", rows.length, "number"),
    ],
    columns: [
      { key: "candidate", label: "Candidate" },
      { key: "job", label: "Job" },
      { key: "appliedAt", label: "Applied" },
      { key: "acceptedAt", label: "Accepted" },
      { key: "daysToHire", label: "Days to hire", format: "days" },
    ],
    rows,
    drilldownHref: "/hr/recruitment",
  });
}

async function onboardingCompletion(
  input: HrReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const checklists = await prisma.onboardingChecklist.findMany({
    where: {
      organizationId: input.user.organizationId,
      createdAt: { gte: input.range.from, lte: input.range.to },
    },
    select: {
      id: true,
      title: true,
      status: true,
      employee: {
        select: { id: true, employeeCode: true, user: { select: { name: true, email: true } } },
      },
      tasks: { select: { id: true, completedAt: true } },
    },
  });
  const rows = checklists.map((checklist) => {
    const completed = checklist.tasks.filter((task) => task.completedAt).length;
    return {
      id: checklist.id,
      href: `/employees/${checklist.employee.id}`,
      values: {
        employee: employeeName(checklist.employee),
        checklist: checklist.title,
        status: checklist.status,
        taskCount: checklist.tasks.length,
        completedTasks: completed,
        completionPct: percent(completed, checklist.tasks.length),
      },
    };
  });
  const averageCompletion = average(
    rows.reduce((sum, row) => sum + Number(row.values.completionPct), 0),
    rows.length,
  );

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Onboarding completion: ${averageCompletion}% average completion across ${rows.length} checklists.`,
    metrics: [
      metric("Average completion", averageCompletion, "percent"),
      metric("Onboarding checklists", rows.length, "number"),
    ],
    columns: [
      { key: "employee", label: "Employee" },
      { key: "checklist", label: "Checklist" },
      { key: "status", label: "Status" },
      { key: "taskCount", label: "Tasks", format: "number" },
      { key: "completedTasks", label: "Completed", format: "number" },
      { key: "completionPct", label: "Completion", format: "percent" },
    ],
    rows,
    drilldownHref: "/employees",
  });
}

async function assetAllocation(
  input: HrReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const assignments = await prisma.assetAssignment.findMany({
    where: {
      organizationId: input.user.organizationId,
      assignedAt: { lte: input.range.to },
      OR: [{ returnedAt: null }, { returnedAt: { gte: input.range.from } }],
    },
    select: {
      id: true,
      assignedAt: true,
      returnedAt: true,
      asset: { select: { name: true, assetTag: true, category: true } },
      employee: {
        select: { id: true, employeeCode: true, user: { select: { name: true, email: true } } },
      },
    },
  });
  const categoryCounts = new Map<string, number>();
  for (const assignment of assignments) {
    const category = assignment.asset.category ?? "Uncategorized";
    categoryCounts.set(category, (categoryCounts.get(category) ?? 0) + 1);
  }

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Asset allocation: ${assignments.length} active or overlapping asset assignments across ${categoryCounts.size} categories.`,
    metrics: [metric("Assigned assets", assignments.length, "number")],
    series: seriesFromMap(categoryCounts),
    columns: [
      { key: "asset", label: "Asset" },
      { key: "category", label: "Category" },
      { key: "employee", label: "Employee" },
      { key: "assignedAt", label: "Assigned" },
      { key: "returnedAt", label: "Returned" },
    ],
    rows: assignments.map((assignment) => ({
      id: assignment.id,
      href: `/employees/${assignment.employee.id}`,
      values: {
        asset: `${assignment.asset.name} (${assignment.asset.assetTag})`,
        category: assignment.asset.category ?? "Uncategorized",
        employee: employeeName(assignment.employee),
        assignedAt: assignment.assignedAt.toISOString().slice(0, 10),
        returnedAt: assignment.returnedAt?.toISOString().slice(0, 10) ?? null,
      },
    })),
    drilldownHref: "/employees",
  });
}

async function documentExpiry(
  input: HrReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const start = new Date();
  start.setUTCHours(0, 0, 0, 0);
  const end = new Date(start.getTime() + 60 * 86400000);
  const documents = await prisma.employeeDocument.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      expiresAt: { gte: start, lte: end },
    },
    select: {
      id: true,
      title: true,
      expiresAt: true,
      documentType: { select: { name: true } },
      employee: {
        select: { id: true, employeeCode: true, user: { select: { name: true, email: true } } },
      },
    },
    orderBy: { expiresAt: "asc" },
  });

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Document expiry: ${documents.length} employee documents expire in the next 60 days.`,
    metrics: [metric("Expiring documents", documents.length, "number")],
    columns: [
      { key: "employee", label: "Employee" },
      { key: "document", label: "Document" },
      { key: "documentType", label: "Type" },
      { key: "expiresAt", label: "Expires" },
    ],
    rows: documents.map((document) => ({
      id: document.id,
      href: `/employees/${document.employee.id}`,
      values: {
        employee: employeeName(document.employee),
        document: document.title,
        documentType: document.documentType?.name ?? "Unspecified",
        expiresAt: document.expiresAt?.toISOString().slice(0, 10) ?? null,
      },
    })),
    drilldownHref: "/employees",
  });
}

