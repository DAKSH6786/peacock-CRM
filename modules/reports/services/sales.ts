import "server-only";

import { prisma } from "@/database";
import type { SessionUser } from "@/permissions";
import { getSalesPerformanceVisibility } from "@/modules/reports/access";
import type {
  ReportDateRange,
  ReportDefinition,
  ReportPayload,
  ReportTableRow,
  SalesPerformanceVisibility,
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

type SalesReportInput = {
  key: string;
  definition: ReportDefinition;
  user: SessionUser & { organizationId: string };
  range: ReportDateRange;
};

type EmployeeLabel = {
  id: string;
  label: string;
};

function percent(numerator: number, denominator: number): number {
  return denominator > 0 ? Math.round((numerator / denominator) * 1000) / 10 : 0;
}

function monthKey(date: Date): string {
  return date.toISOString().slice(0, 7);
}

async function currentEmployeeId(user: SessionUser & { organizationId: string }) {
  const employee = await prisma.employee.findFirst({
    where: { organizationId: user.organizationId, userId: user.id, deletedAt: null },
    select: { id: true },
  });
  return employee?.id ?? null;
}

async function scopedEmployeeIds(input: {
  user: SessionUser & { organizationId: string };
  visibility: SalesPerformanceVisibility;
  peerReport?: boolean;
}): Promise<string[] | undefined> {
  if (
    input.user.role === "SALES" &&
    (input.visibility.salesSelfOnly ||
      (input.peerReport === true && !input.visibility.showPeerLeaderboard))
  ) {
    const employeeId = await currentEmployeeId(input.user);
    return employeeId ? [employeeId] : [];
  }
  return undefined;
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
  const currency = assertSingleCurrency([input.fromCurrency], "Sales report money row");
  const converted = await convertMinorUnits({
    organizationId: input.organizationId,
    amountMinor: input.amountMinor,
    fromCurrency: currency,
    toCurrency: input.toCurrency,
    asOf: input.asOf,
  });
  return converted.amountMinor;
}

export async function runSalesReport(input: SalesReportInput): Promise<ReportPayload> {
  const [currencyCode, visibility] = await Promise.all([
    organizationCurrency(input.user.organizationId),
    getSalesPerformanceVisibility(input.user.organizationId),
  ]);

  switch (input.key) {
    case "sales.target-versus-achievement":
      return targetVersusAchievement(input, currencyCode, visibility);
    case "sales.revenue-by-salesperson":
      return attributionBySalesperson(input, currencyCode, visibility, "CLOSED");
    case "sales.collected-by-salesperson":
      return attributionBySalesperson(input, currencyCode, visibility, "COLLECTED");
    case "sales.cost-versus-revenue":
      return costVersusRevenue(input, currencyCode, visibility);
    case "sales.consecutive-negative-months":
      return consecutiveNegativeMonths(input, currencyCode, visibility);
    case "sales.leaderboard":
      return leaderboard(input, currencyCode, visibility);
    case "sales.commission-estimate":
      return commissionEstimate(input, currencyCode, visibility);
    case "sales.deals-sourced":
      return attributionBySalesperson(input, currencyCode, visibility, "SOURCED");
    case "sales.deals-closed":
      return attributionBySalesperson(input, currencyCode, visibility, "CLOSED");
    case "sales.assisted-revenue":
      return attributionBySalesperson(input, currencyCode, visibility, "ASSISTED");
    case "sales.attribution-breakdown":
      return attributionBreakdown(input, currencyCode, visibility);
    default:
      return buildPayload({
        definition: input.definition,
        range: input.range,
        currencyCode,
        summary: `${input.definition.title}: no implementation for ${input.key}.`,
      });
  }
}

async function targetVersusAchievement(
  input: SalesReportInput,
  currencyCode: string,
  visibility: SalesPerformanceVisibility,
): Promise<ReportPayload> {
  const employeeIds = await scopedEmployeeIds({ user: input.user, visibility, peerReport: true });
  const [targets, achievements] = await Promise.all([
    prisma.salesTarget.findMany({
      where: {
        organizationId: input.user.organizationId,
        deletedAt: null,
        month: { gte: input.range.from, lte: input.range.to },
        ...(employeeIds ? { employeeId: { in: employeeIds } } : {}),
      },
      select: {
        id: true,
        employeeId: true,
        targetMinor: true,
        currencyCode: true,
        month: true,
        employee: {
          select: { id: true, employeeCode: true, user: { select: { name: true, email: true } } },
        },
      },
    }),
    prisma.salesAchievement.findMany({
      where: {
        organizationId: input.user.organizationId,
        month: { gte: input.range.from, lte: input.range.to },
        ...(employeeIds ? { employeeId: { in: employeeIds } } : {}),
      },
      select: {
        id: true,
        employeeId: true,
        achievedMinor: true,
        currencyCode: true,
        month: true,
        employee: {
          select: { id: true, employeeCode: true, user: { select: { name: true, email: true } } },
        },
      },
    }),
  ]);

  const labels = new Map<string, EmployeeLabel>();
  const rows = new Map<string, { targetMinor: number; achievedMinor: number }>();

  for (const target of targets) {
    labels.set(target.employeeId, {
      id: target.employee.id,
      label: employeeName(target.employee),
    });
    const current = rows.get(target.employeeId) ?? { targetMinor: 0, achievedMinor: 0 };
    current.targetMinor += await convertMoney({
      organizationId: input.user.organizationId,
      amountMinor: target.targetMinor,
      fromCurrency: target.currencyCode,
      toCurrency: currencyCode,
      asOf: target.month ?? input.range.to,
    });
    rows.set(target.employeeId, current);
  }

  for (const achievement of achievements) {
    labels.set(achievement.employeeId, {
      id: achievement.employee.id,
      label: employeeName(achievement.employee),
    });
    const current = rows.get(achievement.employeeId) ?? { targetMinor: 0, achievedMinor: 0 };
    current.achievedMinor += await convertMoney({
      organizationId: input.user.organizationId,
      amountMinor: achievement.achievedMinor,
      fromCurrency: achievement.currencyCode,
      toCurrency: currencyCode,
      asOf: achievement.month,
    });
    rows.set(achievement.employeeId, current);
  }

  const tableRows: ReportTableRow[] = [...rows.entries()]
    .map(([employeeId, values]) => ({
      id: employeeId,
      href: `/employees/${labels.get(employeeId)?.id ?? employeeId}`,
      values: {
        salesperson: labels.get(employeeId)?.label ?? employeeId,
        targetMinor: values.targetMinor,
        achievedMinor: values.achievedMinor,
        achievementPct: percent(values.achievedMinor, values.targetMinor),
      },
    }))
    .sort((a, b) => Number(b.values.achievedMinor) - Number(a.values.achievedMinor));

  const totalTarget = tableRows.reduce(
    (sum, row) => sum + Number(row.values.targetMinor ?? 0),
    0,
  );
  const totalAchieved = tableRows.reduce(
    (sum, row) => sum + Number(row.values.achievedMinor ?? 0),
    0,
  );

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Target versus achievement: ${percent(totalAchieved, totalTarget)}% achieved against ${Math.round(totalTarget / 100)} ${currencyCode} target.`,
    metrics: [
      metric("Target", totalTarget, "money"),
      metric("Achievement", totalAchieved, "money"),
      metric("Achievement rate", percent(totalAchieved, totalTarget), "percent"),
    ],
    series: [
      { label: "Target", value: Math.round(totalTarget / 100), href: "/sales/targets" },
      { label: "Achievement", value: Math.round(totalAchieved / 100), href: "/sales/targets" },
    ],
    columns: [
      { key: "salesperson", label: "Salesperson" },
      { key: "targetMinor", label: "Target", format: "money" },
      { key: "achievedMinor", label: "Achievement", format: "money" },
      { key: "achievementPct", label: "Achievement", format: "percent" },
    ],
    rows: tableRows,
    drilldownHref: "/sales/targets",
  });
}

async function attributionBySalesperson(
  input: SalesReportInput,
  currencyCode: string,
  visibility: SalesPerformanceVisibility,
  attributionType: "SOURCED" | "CLOSED" | "COLLECTED" | "ASSISTED",
): Promise<ReportPayload> {
  const employeeIds = await scopedEmployeeIds({ user: input.user, visibility, peerReport: true });
  const attributions = await prisma.employeeRevenueAttribution.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      approvalStatus: "APPROVED",
      attributionType,
      month: { gte: input.range.from, lte: input.range.to },
      ...(employeeIds ? { employeeId: { in: employeeIds } } : {}),
    },
    select: {
      id: true,
      employeeId: true,
      amountMinor: true,
      currencyCode: true,
      month: true,
      attributionType: true,
      employee: {
        select: { id: true, employeeCode: true, user: { select: { name: true, email: true } } },
      },
    },
  });

  const totals = new Map<string, number>();
  const labels = new Map<string, EmployeeLabel>();
  for (const attribution of attributions) {
    labels.set(attribution.employeeId, {
      id: attribution.employee.id,
      label: employeeName(attribution.employee),
    });
    const amountMinor = await convertMoney({
      organizationId: input.user.organizationId,
      amountMinor: attribution.amountMinor,
      fromCurrency: attribution.currencyCode,
      toCurrency: currencyCode,
      asOf: attribution.month,
    });
    totals.set(attribution.employeeId, (totals.get(attribution.employeeId) ?? 0) + amountMinor);
  }

  const tableRows = [...totals.entries()]
    .map(([employeeId, amountMinor]) => ({
      id: employeeId,
      href: `/employees/${labels.get(employeeId)?.id ?? employeeId}`,
      values: {
        salesperson: labels.get(employeeId)?.label ?? employeeId,
        attributionType,
        amountMinor,
      },
    }))
    .sort((a, b) => Number(b.values.amountMinor) - Number(a.values.amountMinor));
  const series = tableRows.map((row) => ({
    label: String(row.values.salesperson),
    value: Math.round(Number(row.values.amountMinor) / 100),
    href: row.href,
  }));
  const totalMinor = tableRows.reduce(
    (sum, row) => sum + Number(row.values.amountMinor ?? 0),
    0,
  );

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary:
      series.length > 0
        ? accessibleSeriesSummary(`${attributionType.toLowerCase()} revenue by salesperson`, series, "money")
        : `${attributionType.toLowerCase()} revenue by salesperson: no approved attributions in the selected range.`,
    metrics: [
      metric(`${attributionType} revenue`, totalMinor, "money"),
      metric("Attribution records", attributions.length, "number"),
    ],
    series,
    columns: [
      { key: "salesperson", label: "Salesperson" },
      { key: "attributionType", label: "Attribution" },
      { key: "amountMinor", label: "Revenue", format: "money" },
    ],
    rows: tableRows,
    drilldownHref: "/sales/attributions",
  });
}

async function costVersusRevenue(
  input: SalesReportInput,
  currencyCode: string,
  visibility: SalesPerformanceVisibility,
): Promise<ReportPayload> {
  if (!visibility.showCostVersusRevenue) {
    return buildPayload({
      definition: input.definition,
      range: input.range,
      currencyCode,
      summary: "Cost-versus-revenue is disabled by sales performance visibility settings.",
    });
  }

  const employeeIds = await scopedEmployeeIds({ user: input.user, visibility, peerReport: true });
  const snapshots = await prisma.employeeProfitabilitySnapshot.findMany({
    where: {
      organizationId: input.user.organizationId,
      month: { gte: input.range.from, lte: input.range.to },
      ...(employeeIds ? { employeeId: { in: employeeIds } } : {}),
    },
    select: {
      id: true,
      employeeId: true,
      month: true,
      costMinor: true,
      revenueMinor: true,
      currencyCode: true,
      employee: {
        select: { id: true, employeeCode: true, user: { select: { name: true, email: true } } },
      },
    },
  });

  const totals = new Map<string, { costMinor: number; revenueMinor: number; label: string }>();
  for (const snapshot of snapshots) {
    const current = totals.get(snapshot.employeeId) ?? {
      costMinor: 0,
      revenueMinor: 0,
      label: employeeName(snapshot.employee),
    };
    current.costMinor += await convertMoney({
      organizationId: input.user.organizationId,
      amountMinor: snapshot.costMinor,
      fromCurrency: snapshot.currencyCode,
      toCurrency: currencyCode,
      asOf: snapshot.month,
    });
    current.revenueMinor += await convertMoney({
      organizationId: input.user.organizationId,
      amountMinor: snapshot.revenueMinor,
      fromCurrency: snapshot.currencyCode,
      toCurrency: currencyCode,
      asOf: snapshot.month,
    });
    totals.set(snapshot.employeeId, current);
  }

  const rows = [...totals.entries()]
    .map(([employeeId, values]) => ({
      id: employeeId,
      href: `/employees/${employeeId}`,
      values: {
        salesperson: values.label,
        revenueMinor: values.revenueMinor,
        costMinor: values.costMinor,
        ratio: percent(values.costMinor, values.revenueMinor),
      },
    }))
    .sort((a, b) => Number(b.values.ratio) - Number(a.values.ratio));
  const revenueMinor = rows.reduce(
    (sum, row) => sum + Number(row.values.revenueMinor ?? 0),
    0,
  );
  const costMinor = rows.reduce((sum, row) => sum + Number(row.values.costMinor ?? 0), 0);

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Cost-versus-revenue ratio: ${percent(costMinor, revenueMinor)}% cost on ${Math.round(revenueMinor / 100)} ${currencyCode} revenue.`,
    metrics: [
      metric("Revenue", revenueMinor, "money"),
      metric("Cost", costMinor, "money"),
      metric("Cost/revenue ratio", percent(costMinor, revenueMinor), "percent"),
    ],
    columns: [
      { key: "salesperson", label: "Salesperson" },
      { key: "revenueMinor", label: "Revenue", format: "money" },
      { key: "costMinor", label: "Cost", format: "money", restricted: true },
      { key: "ratio", label: "Cost/revenue", format: "percent", restricted: true },
    ],
    rows,
    drilldownHref: "/sales/performance",
  });
}

async function consecutiveNegativeMonths(
  input: SalesReportInput,
  currencyCode: string,
  visibility: SalesPerformanceVisibility,
): Promise<ReportPayload> {
  if (!visibility.showCostVersusRevenue) {
    return buildPayload({
      definition: input.definition,
      range: input.range,
      currencyCode,
      summary: "Consecutive negative-month status is disabled by sales performance visibility settings.",
    });
  }

  const employeeIds = await scopedEmployeeIds({ user: input.user, visibility, peerReport: true });
  const snapshots = await prisma.employeeProfitabilitySnapshot.findMany({
    where: {
      organizationId: input.user.organizationId,
      month: { gte: input.range.from, lte: input.range.to },
      ...(employeeIds ? { employeeId: { in: employeeIds } } : {}),
    },
    select: {
      id: true,
      employeeId: true,
      month: true,
      costMinor: true,
      revenueMinor: true,
      profitMinor: true,
      currencyCode: true,
      employee: {
        select: { id: true, employeeCode: true, user: { select: { name: true, email: true } } },
      },
    },
    orderBy: [{ employeeId: "asc" }, { month: "asc" }],
  });

  const byEmployee = new Map<string, typeof snapshots>();
  for (const snapshot of snapshots) {
    const current = byEmployee.get(snapshot.employeeId) ?? [];
    current.push(snapshot);
    byEmployee.set(snapshot.employeeId, current);
  }

  const rows: ReportTableRow[] = [];
  for (const [employeeId, employeeSnapshots] of byEmployee.entries()) {
    let consecutive = 0;
    for (const snapshot of [...employeeSnapshots].reverse()) {
      if (snapshot.profitMinor < 0) consecutive += 1;
      else break;
    }
    const revenueMinor = await employeeSnapshots.reduce<Promise<number>>(
      async (sumPromise, snapshot) =>
        (await sumPromise) +
        (await convertMoney({
          organizationId: input.user.organizationId,
          amountMinor: snapshot.revenueMinor,
          fromCurrency: snapshot.currencyCode,
          toCurrency: currencyCode,
          asOf: snapshot.month,
        })),
      Promise.resolve(0),
    );
    const costMinor = await employeeSnapshots.reduce<Promise<number>>(
      async (sumPromise, snapshot) =>
        (await sumPromise) +
        (await convertMoney({
          organizationId: input.user.organizationId,
          amountMinor: snapshot.costMinor,
          fromCurrency: snapshot.currencyCode,
          toCurrency: currencyCode,
          asOf: snapshot.month,
        })),
      Promise.resolve(0),
    );
    rows.push({
      id: employeeId,
      href: `/employees/${employeeId}`,
      values: {
        salesperson: employeeName(employeeSnapshots[0]!.employee),
        negativeMonths: consecutive,
        revenueMinor,
        costMinor,
      },
    });
  }

  const affected = rows.filter((row) => Number(row.values.negativeMonths) > 0).length;

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Consecutive negative-month status: ${affected} employees currently have negative months in the selected range.`,
    metrics: [
      metric("Employees with negative streaks", affected, "number"),
      metric("Employees reviewed", rows.length, "number"),
    ],
    columns: [
      { key: "salesperson", label: "Salesperson" },
      { key: "negativeMonths", label: "Consecutive negative months", format: "number" },
      { key: "revenueMinor", label: "Revenue", format: "money", restricted: true },
      { key: "costMinor", label: "Cost", format: "money", restricted: true },
    ],
    rows: rows.sort(
      (a, b) => Number(b.values.negativeMonths) - Number(a.values.negativeMonths),
    ),
    drilldownHref: "/sales/performance",
  });
}

async function leaderboard(
  input: SalesReportInput,
  currencyCode: string,
  visibility: SalesPerformanceVisibility,
): Promise<ReportPayload> {
  const employeeIds = await scopedEmployeeIds({ user: input.user, visibility, peerReport: true });
  const achievements = await prisma.salesAchievement.findMany({
    where: {
      organizationId: input.user.organizationId,
      month: { gte: input.range.from, lte: input.range.to },
      ...(employeeIds ? { employeeId: { in: employeeIds } } : {}),
    },
    select: {
      id: true,
      employeeId: true,
      achievedMinor: true,
      currencyCode: true,
      month: true,
      employee: {
        select: { id: true, employeeCode: true, user: { select: { name: true, email: true } } },
      },
    },
  });

  const totals = new Map<string, { label: string; amountMinor: number }>();
  for (const achievement of achievements) {
    const current = totals.get(achievement.employeeId) ?? {
      label: employeeName(achievement.employee),
      amountMinor: 0,
    };
    current.amountMinor += await convertMoney({
      organizationId: input.user.organizationId,
      amountMinor: achievement.achievedMinor,
      fromCurrency: achievement.currencyCode,
      toCurrency: currencyCode,
      asOf: achievement.month,
    });
    totals.set(achievement.employeeId, current);
  }

  const rows = [...totals.entries()]
    .sort(([, a], [, b]) => b.amountMinor - a.amountMinor)
    .map(([employeeId, values], index) => ({
      id: employeeId,
      href: `/employees/${employeeId}`,
      values: {
        rank: index + 1,
        salesperson: values.label,
        achievedMinor: values.amountMinor,
      },
    }));
  const series = rows.map((row) => ({
    label: String(row.values.salesperson),
    value: Math.round(Number(row.values.achievedMinor) / 100),
    href: row.href,
  }));
  const totalMinor = rows.reduce(
    (sum, row) => sum + Number(row.values.achievedMinor ?? 0),
    0,
  );

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary:
      rows.length > 0
        ? `Sales leaderboard: ${rows[0]?.values.salesperson} leads with ${Math.round(Number(rows[0]?.values.achievedMinor ?? 0) / 100)} ${currencyCode}; total achievement is ${Math.round(totalMinor / 100)} ${currencyCode}.`
        : "Sales leaderboard: no sales achievements in the selected range.",
    metrics: [
      metric("Total achievement", totalMinor, "money"),
      metric("Ranked employees", rows.length, "number"),
    ],
    series,
    columns: [
      { key: "rank", label: "Rank", format: "number" },
      { key: "salesperson", label: "Salesperson" },
      { key: "achievedMinor", label: "Achievement", format: "money" },
    ],
    rows,
    drilldownHref: "/sales/performance",
  });
}

async function commissionEstimate(
  input: SalesReportInput,
  currencyCode: string,
  visibility: SalesPerformanceVisibility,
): Promise<ReportPayload> {
  const employeeIds = await scopedEmployeeIds({ user: input.user, visibility, peerReport: false });
  const records = await prisma.salesCommissionRecord.findMany({
    where: {
      organizationId: input.user.organizationId,
      month: { gte: input.range.from, lte: input.range.to },
      ...(employeeIds ? { employeeId: { in: employeeIds } } : {}),
    },
    select: {
      id: true,
      month: true,
      baseMinor: true,
      commissionMinor: true,
      currencyCode: true,
      approvalStatus: true,
      employee: {
        select: { id: true, employeeCode: true, user: { select: { name: true, email: true } } },
      },
      plan: { select: { name: true } },
    },
    orderBy: { month: "asc" },
  });

  const rows: ReportTableRow[] = [];
  for (const record of records) {
    const baseMinor = await convertMoney({
      organizationId: input.user.organizationId,
      amountMinor: record.baseMinor,
      fromCurrency: record.currencyCode,
      toCurrency: currencyCode,
      asOf: record.month,
    });
    const commissionMinor = await convertMoney({
      organizationId: input.user.organizationId,
      amountMinor: record.commissionMinor,
      fromCurrency: record.currencyCode,
      toCurrency: currencyCode,
      asOf: record.month,
    });
    rows.push({
      id: record.id,
      href: `/employees/${record.employee.id}`,
      values: {
        salesperson: employeeName(record.employee),
        month: monthKey(record.month),
        plan: record.plan?.name ?? "Unassigned",
        status: record.approvalStatus,
        baseMinor,
        commissionMinor,
      },
    });
  }
  const commissionTotal = rows.reduce(
    (sum, row) => sum + Number(row.values.commissionMinor ?? 0),
    0,
  );

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Commission estimate: ${Math.round(commissionTotal / 100)} ${currencyCode} across ${rows.length} commission records.`,
    metrics: [
      metric("Commission estimate", commissionTotal, "money"),
      metric("Commission records", rows.length, "number"),
    ],
    columns: [
      { key: "salesperson", label: "Salesperson" },
      { key: "month", label: "Month" },
      { key: "plan", label: "Plan" },
      { key: "status", label: "Status" },
      { key: "baseMinor", label: "Base", format: "money", restricted: true },
      { key: "commissionMinor", label: "Commission", format: "money", restricted: true },
    ],
    rows,
    drilldownHref: "/sales/commissions",
  });
}

async function attributionBreakdown(
  input: SalesReportInput,
  currencyCode: string,
  visibility: SalesPerformanceVisibility,
): Promise<ReportPayload> {
  const employeeIds = await scopedEmployeeIds({ user: input.user, visibility, peerReport: true });
  const attributions = await prisma.employeeRevenueAttribution.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      approvalStatus: "APPROVED",
      month: { gte: input.range.from, lte: input.range.to },
      ...(employeeIds ? { employeeId: { in: employeeIds } } : {}),
    },
    select: {
      id: true,
      attributionType: true,
      amountMinor: true,
      currencyCode: true,
      month: true,
    },
  });

  const totals = new Map<string, number>();
  for (const attribution of attributions) {
    const amountMinor = await convertMoney({
      organizationId: input.user.organizationId,
      amountMinor: attribution.amountMinor,
      fromCurrency: attribution.currencyCode,
      toCurrency: currencyCode,
      asOf: attribution.month,
    });
    totals.set(
      attribution.attributionType,
      (totals.get(attribution.attributionType) ?? 0) + amountMinor,
    );
  }
  const rows = [...totals.entries()].map(([type, amountMinor]) => ({
    id: type,
    href: "/sales/attributions",
    values: {
      attributionType: type,
      amountMinor,
      recordCount: attributions.filter((item) => item.attributionType === type).length,
    },
  }));
  const totalMinor = rows.reduce(
    (sum, row) => sum + Number(row.values.amountMinor ?? 0),
    0,
  );
  const series = seriesFromMap(totals).map((point) => ({
    ...point,
    value: Math.round(point.value / 100),
    href: "/sales/attributions",
  }));

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary:
      series.length > 0
        ? accessibleSeriesSummary("Revenue attribution breakdown", series, "money")
        : "Revenue attribution breakdown: no approved attribution records in the selected range.",
    metrics: [
      metric("Attributed revenue", totalMinor, "money"),
      metric("Attribution records", attributions.length, "number"),
    ],
    series,
    columns: [
      { key: "attributionType", label: "Attribution" },
      { key: "recordCount", label: "Records", format: "number" },
      { key: "amountMinor", label: "Amount", format: "money" },
    ],
    rows,
    drilldownHref: "/sales/attributions",
  });
}

