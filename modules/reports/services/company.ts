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
  dayKey,
  metric,
  seriesFromMap,
} from "@/modules/reports/helpers";
import {
  assertSingleCurrency,
  convertMinorUnits,
  organizationCurrency,
} from "@/modules/reports/currency";

type CompanyReportInput = {
  key: string;
  definition: ReportDefinition;
  user: SessionUser & { organizationId: string };
  range: ReportDateRange;
};

const OPEN_INVOICE_STATUSES = ["SENT", "PARTIAL", "OVERDUE", "OPEN"];
const ACTIVE_PROJECT_STATUSES = ["ACTIVE", "IN_PROGRESS", "AT_RISK"];

function percent(numerator: number, denominator: number): number {
  return denominator > 0 ? Math.round((numerator / denominator) * 1000) / 10 : 0;
}

function average(total: number, count: number): number {
  return count > 0 ? Math.round(total / count) : 0;
}

async function convertMoney(input: {
  organizationId: string;
  amountMinor: number;
  fromCurrency: string;
  toCurrency: string;
  asOf: Date;
}): Promise<number> {
  const currency = assertSingleCurrency([input.fromCurrency], "Company report money row");
  const converted = await convertMinorUnits({
    organizationId: input.organizationId,
    amountMinor: input.amountMinor,
    fromCurrency: currency,
    toCurrency: input.toCurrency,
    asOf: input.asOf,
  });
  return converted.amountMinor;
}

function moneySeries(map: Map<string, number>) {
  return seriesFromMap(map).map((point) => ({
    ...point,
    value: Math.round(point.value / 100),
  }));
}

export async function runCompanyReport(
  input: CompanyReportInput,
): Promise<ReportPayload> {
  const currencyCode = await organizationCurrency(input.user.organizationId);

  switch (input.key) {
    case "company.revenue-trend":
      return revenueTrend(input, currencyCode);
    case "company.collected-revenue-trend":
      return collectedRevenueTrend(input, currencyCode);
    case "company.pipeline-forecast":
      return pipelineForecast(input, currencyCode);
    case "company.revenue-versus-target":
      return revenueVersusTarget(input, currencyCode);
    case "company.revenue-by-service":
      return revenueByService(input, currencyCode);
    case "company.revenue-by-client":
      return revenueByClient(input, currencyCode);
    case "company.client-concentration":
      return clientConcentration(input, currencyCode);
    case "company.client-retention":
      return clientRetention(input, currencyCode);
    case "company.project-profitability":
      return projectProfitability(input, currencyCode);
    case "company.department-performance":
      return departmentPerformance(input, currencyCode);
    case "company.objective-progress":
      return objectiveProgress(input, currencyCode);
    case "company.headcount-trend":
      return headcountTrend(input, currencyCode);
    case "company.attendance-trend":
      return attendanceTrend(input, currencyCode);
    case "company.expense-trend":
      return expenseTrend(input, currencyCode);
    case "company.receivable-aging":
      return receivableAging(input, currencyCode);
    case "company.cash-collection":
      return collectedRevenueTrend(input, currencyCode);
    case "company.monthly-business-summary":
      return monthlyBusinessSummary(input, currencyCode);
    default:
      return buildPayload({
        definition: input.definition,
        range: input.range,
        currencyCode,
        summary: `${input.definition.title}: no implementation for ${input.key}.`,
      });
  }
}

async function revenueTrend(
  input: CompanyReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const invoices = await prisma.invoice.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      status: { not: "DRAFT" },
      issueDate: { gte: input.range.from, lte: input.range.to },
    },
    select: {
      id: true,
      invoiceNumber: true,
      issueDate: true,
      totalMinor: true,
      currencyCode: true,
      company: { select: { name: true } },
    },
  });
  const totals = new Map<string, number>();
  const rows: ReportTableRow[] = [];
  for (const invoice of invoices) {
    const asOf = invoice.issueDate ?? input.range.to;
    const amountMinor = await convertMoney({
      organizationId: input.user.organizationId,
      amountMinor: invoice.totalMinor,
      fromCurrency: invoice.currencyCode,
      toCurrency: currencyCode,
      asOf,
    });
    if (invoice.issueDate) {
      totals.set(dayKey(invoice.issueDate), (totals.get(dayKey(invoice.issueDate)) ?? 0) + amountMinor);
    }
    rows.push({
      id: invoice.id,
      href: `/finance/invoices/${invoice.id}`,
      values: {
        invoice: invoice.invoiceNumber ?? invoice.id,
        client: invoice.company?.name ?? "Unassigned",
        issueDate: invoice.issueDate?.toISOString().slice(0, 10) ?? null,
        totalMinor: amountMinor,
      },
    });
  }
  const totalMinor = rows.reduce((sum, row) => sum + Number(row.values.totalMinor ?? 0), 0);
  const series = moneySeries(totals);
  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary:
      series.length > 0
        ? accessibleSeriesSummary("Invoiced revenue trend", series, "money")
        : "Invoiced revenue trend: no invoices issued in the selected range.",
    metrics: [
      metric("Invoiced revenue", totalMinor, "money"),
      metric("Invoice count", rows.length, "number"),
    ],
    series,
    columns: [
      { key: "invoice", label: "Invoice" },
      { key: "client", label: "Client" },
      { key: "issueDate", label: "Issue date" },
      { key: "totalMinor", label: "Total", format: "money" },
    ],
    rows,
    drilldownHref: "/finance/invoices",
  });
}

async function collectedRevenueTrend(
  input: CompanyReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const payments = await prisma.payment.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      receivedAt: { gte: input.range.from, lte: input.range.to },
    },
    select: {
      id: true,
      paymentNumber: true,
      amountMinor: true,
      currencyCode: true,
      receivedAt: true,
      method: true,
    },
  });
  const totals = new Map<string, number>();
  const rows: ReportTableRow[] = [];
  for (const payment of payments) {
    const amountMinor = await convertMoney({
      organizationId: input.user.organizationId,
      amountMinor: payment.amountMinor,
      fromCurrency: payment.currencyCode,
      toCurrency: currencyCode,
      asOf: payment.receivedAt,
    });
    totals.set(dayKey(payment.receivedAt), (totals.get(dayKey(payment.receivedAt)) ?? 0) + amountMinor);
    rows.push({
      id: payment.id,
      href: "/finance/payments",
      values: {
        payment: payment.paymentNumber ?? payment.id,
        method: payment.method ?? "Unspecified",
        receivedAt: payment.receivedAt.toISOString().slice(0, 10),
        amountMinor,
      },
    });
  }
  const totalMinor = rows.reduce((sum, row) => sum + Number(row.values.amountMinor ?? 0), 0);
  const series = moneySeries(totals);
  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary:
      series.length > 0
        ? accessibleSeriesSummary("Collected revenue trend", series, "money")
        : "Collected revenue trend: no payments received in the selected range.",
    metrics: [
      metric("Collected revenue", totalMinor, "money"),
      metric("Payment count", rows.length, "number"),
    ],
    series,
    columns: [
      { key: "payment", label: "Payment" },
      { key: "method", label: "Method" },
      { key: "receivedAt", label: "Received" },
      { key: "amountMinor", label: "Amount", format: "money" },
    ],
    rows,
    drilldownHref: "/finance/payments",
  });
}

async function pipelineForecast(
  input: CompanyReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const stages = await prisma.pipelineStage.findMany({
    where: { organizationId: input.user.organizationId, deletedAt: null },
    select: {
      id: true,
      name: true,
      probability: true,
      deals: {
        where: { organizationId: input.user.organizationId, deletedAt: null, closedAt: null },
        select: {
          id: true,
          name: true,
          valueMinor: true,
          probability: true,
          currencyCode: true,
          expectedCloseDate: true,
          createdAt: true,
        },
      },
    },
    orderBy: { sortOrder: "asc" },
  });
  const rows: ReportTableRow[] = [];
  const totals = new Map<string, number>();
  for (const stage of stages) {
    let weightedMinor = 0;
    for (const deal of stage.deals) {
      const amount = Math.round((deal.valueMinor * (deal.probability ?? stage.probability)) / 100);
      weightedMinor += await convertMoney({
        organizationId: input.user.organizationId,
        amountMinor: amount,
        fromCurrency: deal.currencyCode,
        toCurrency: currencyCode,
        asOf: deal.expectedCloseDate ?? deal.createdAt,
      });
    }
    totals.set(stage.name, weightedMinor);
    rows.push({
      id: stage.id,
      href: "/crm/deals",
      values: {
        stage: stage.name,
        openDeals: stage.deals.length,
        probability: stage.probability,
        weightedMinor,
      },
    });
  }
  const totalWeighted = rows.reduce((sum, row) => sum + Number(row.values.weightedMinor ?? 0), 0);
  const series = moneySeries(totals);
  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary:
      series.length > 0
        ? accessibleSeriesSummary("Pipeline forecast by stage", series, "money")
        : "Pipeline forecast: no open deals found.",
    metrics: [
      metric("Weighted pipeline", totalWeighted, "money"),
      metric("Open stages", rows.length, "number"),
    ],
    series,
    columns: [
      { key: "stage", label: "Stage" },
      { key: "openDeals", label: "Open deals", format: "number" },
      { key: "probability", label: "Stage probability", format: "percent" },
      { key: "weightedMinor", label: "Weighted value", format: "money" },
    ],
    rows,
    drilldownHref: "/crm/deals",
  });
}

async function revenueVersusTarget(
  input: CompanyReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const [targets, achievements] = await Promise.all([
    prisma.salesTarget.findMany({
      where: {
        organizationId: input.user.organizationId,
        deletedAt: null,
        month: { gte: input.range.from, lte: input.range.to },
      },
      select: { id: true, targetMinor: true, currencyCode: true, month: true },
    }),
    prisma.salesAchievement.findMany({
      where: {
        organizationId: input.user.organizationId,
        month: { gte: input.range.from, lte: input.range.to },
      },
      select: { id: true, achievedMinor: true, currencyCode: true, month: true },
    }),
  ]);
  let targetMinor = 0;
  for (const target of targets) {
    targetMinor += await convertMoney({
      organizationId: input.user.organizationId,
      amountMinor: target.targetMinor,
      fromCurrency: target.currencyCode,
      toCurrency: currencyCode,
      asOf: target.month ?? input.range.to,
    });
  }
  let achievedMinor = 0;
  for (const achievement of achievements) {
    achievedMinor += await convertMoney({
      organizationId: input.user.organizationId,
      amountMinor: achievement.achievedMinor,
      fromCurrency: achievement.currencyCode,
      toCurrency: currencyCode,
      asOf: achievement.month,
    });
  }
  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Revenue versus target: ${percent(achievedMinor, targetMinor)}% achieved against ${Math.round(targetMinor / 100)} ${currencyCode} target.`,
    metrics: [
      metric("Target", targetMinor, "money"),
      metric("Achievement", achievedMinor, "money"),
      metric("Achievement rate", percent(achievedMinor, targetMinor), "percent"),
    ],
    series: [
      { label: "Target", value: Math.round(targetMinor / 100), href: "/sales/targets" },
      { label: "Achievement", value: Math.round(achievedMinor / 100), href: "/sales/targets" },
    ],
    columns: [
      { key: "measure", label: "Measure" },
      { key: "amountMinor", label: "Amount", format: "money" },
    ],
    rows: [
      { id: "target", href: "/sales/targets", values: { measure: "Target", amountMinor: targetMinor } },
      { id: "achievement", href: "/sales/targets", values: { measure: "Achievement", amountMinor: achievedMinor } },
    ],
    drilldownHref: "/sales/targets",
  });
}

async function revenueByService(
  input: CompanyReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const invoices = await prisma.invoice.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      status: { not: "DRAFT" },
      issueDate: { gte: input.range.from, lte: input.range.to },
    },
    select: {
      id: true,
      totalMinor: true,
      currencyCode: true,
      issueDate: true,
      project: { select: { services: { select: { name: true } } } },
    },
  });
  const totals = new Map<string, number>();
  for (const invoice of invoices) {
    const services =
      invoice.project?.services.length ? invoice.project.services.map((service) => service.name) : ["Unassigned"];
    const amountMinor = await convertMoney({
      organizationId: input.user.organizationId,
      amountMinor: invoice.totalMinor,
      fromCurrency: invoice.currencyCode,
      toCurrency: currencyCode,
      asOf: invoice.issueDate ?? input.range.to,
    });
    for (const service of services) {
      totals.set(service, (totals.get(service) ?? 0) + Math.round(amountMinor / services.length));
    }
  }
  return dimensionMoneyPayload(input, currencyCode, {
    title: "Revenue by service",
    dimension: "service",
    href: "/projects",
    totals,
  });
}

async function revenueByClient(
  input: CompanyReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const totals = await invoiceTotalsByClient(input, currencyCode);
  return dimensionMoneyPayload(input, currencyCode, {
    title: "Revenue by client",
    dimension: "client",
    href: "/finance/invoices",
    totals: totals.amounts,
    ids: totals.ids,
  });
}

async function clientConcentration(
  input: CompanyReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const totals = await invoiceTotalsByClient(input, currencyCode);
  const totalMinor = [...totals.amounts.values()].reduce((sum, value) => sum + value, 0);
  const rows = [...totals.amounts.entries()]
    .sort(([, a], [, b]) => b - a)
    .map(([client, amountMinor]) => ({
      id: totals.ids.get(client) ?? client,
      href: "/finance/invoices",
      values: {
        client,
        amountMinor,
        sharePct: percent(amountMinor, totalMinor),
      },
    }));
  const series = rows.map((row) => ({
    label: String(row.values.client),
    value: Number(row.values.sharePct),
    href: row.href,
  }));
  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary:
      rows.length > 0
        ? `Client concentration: top client ${rows[0]?.values.client} contributes ${rows[0]?.values.sharePct}% of invoiced revenue.`
        : "Client concentration: no invoiced revenue in the selected range.",
    metrics: [
      metric("Invoiced revenue", totalMinor, "money"),
      metric("Client count", rows.length, "number"),
    ],
    series,
    columns: [
      { key: "client", label: "Client" },
      { key: "amountMinor", label: "Revenue", format: "money" },
      { key: "sharePct", label: "Share", format: "percent" },
    ],
    rows,
    drilldownHref: "/finance/invoices",
  });
}

async function invoiceTotalsByClient(
  input: CompanyReportInput,
  currencyCode: string,
): Promise<{ amounts: Map<string, number>; ids: Map<string, string> }> {
  const invoices = await prisma.invoice.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      status: { not: "DRAFT" },
      issueDate: { gte: input.range.from, lte: input.range.to },
    },
    select: {
      totalMinor: true,
      currencyCode: true,
      issueDate: true,
      company: { select: { id: true, name: true } },
    },
  });
  const amounts = new Map<string, number>();
  const ids = new Map<string, string>();
  for (const invoice of invoices) {
    const client = invoice.company?.name ?? "Unassigned";
    ids.set(client, invoice.company?.id ?? "unassigned");
    const amountMinor = await convertMoney({
      organizationId: input.user.organizationId,
      amountMinor: invoice.totalMinor,
      fromCurrency: invoice.currencyCode,
      toCurrency: currencyCode,
      asOf: invoice.issueDate ?? input.range.to,
    });
    amounts.set(client, (amounts.get(client) ?? 0) + amountMinor);
  }
  return { amounts, ids };
}

function dimensionMoneyPayload(
  input: CompanyReportInput,
  currencyCode: string,
  config: {
    title: string;
    dimension: string;
    href: string;
    totals: Map<string, number>;
    ids?: Map<string, string>;
  },
): ReportPayload {
  const rows = [...config.totals.entries()]
    .sort(([, a], [, b]) => b - a)
    .map(([label, amountMinor]) => ({
      id: config.ids?.get(label) ?? label,
      href: config.href,
      values: {
        [config.dimension]: label,
        amountMinor,
      },
    }));
  const totalMinor = rows.reduce((sum, row) => sum + Number(row.values.amountMinor ?? 0), 0);
  const series = rows.map((row) => ({
    label: String(row.values[config.dimension]),
    value: Math.round(Number(row.values.amountMinor) / 100),
    href: row.href,
  }));
  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary:
      series.length > 0
        ? accessibleSeriesSummary(config.title, series, "money")
        : `${config.title}: no invoiced revenue in the selected range.`,
    metrics: [
      metric("Revenue", totalMinor, "money"),
      metric("Groups", rows.length, "number"),
    ],
    series,
    columns: [
      { key: config.dimension, label: config.dimension[0]!.toUpperCase() + config.dimension.slice(1) },
      { key: "amountMinor", label: "Revenue", format: "money" },
    ],
    rows,
    drilldownHref: config.href,
  });
}

async function clientRetention(
  input: CompanyReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const lengthMs = Math.max(1, input.range.to.getTime() - input.range.from.getTime());
  const priorFrom = new Date(input.range.from.getTime() - lengthMs);
  const [prior, current] = await Promise.all([
    prisma.invoice.findMany({
      where: {
        organizationId: input.user.organizationId,
        deletedAt: null,
        status: { not: "DRAFT" },
        issueDate: { gte: priorFrom, lt: input.range.from },
        companyId: { not: null },
      },
      select: { companyId: true, company: { select: { name: true } } },
    }),
    prisma.invoice.findMany({
      where: {
        organizationId: input.user.organizationId,
        deletedAt: null,
        status: { not: "DRAFT" },
        issueDate: { gte: input.range.from, lte: input.range.to },
        companyId: { not: null },
      },
      select: { companyId: true },
    }),
  ]);
  const currentIds = new Set(current.map((invoice) => invoice.companyId).filter(Boolean));
  const priorClients = new Map<string, string>();
  for (const invoice of prior) {
    if (invoice.companyId) priorClients.set(invoice.companyId, invoice.company?.name ?? invoice.companyId);
  }
  const rows = [...priorClients.entries()].map(([id, client]) => ({
    id,
    href: "/crm/clients",
    values: {
      client,
      retained: currentIds.has(id) ? "Yes" : "No",
    },
  }));
  const retained = rows.filter((row) => row.values.retained === "Yes").length;
  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Client retention: ${percent(retained, rows.length)}% of prior-period invoiced clients returned in the selected range.`,
    metrics: [
      metric("Retention rate", percent(retained, rows.length), "percent"),
      metric("Retained clients", retained, "number"),
      metric("Prior clients", rows.length, "number"),
    ],
    columns: [
      { key: "client", label: "Client" },
      { key: "retained", label: "Retained" },
    ],
    rows,
    drilldownHref: "/crm/clients",
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
      project: { select: { id: true, name: true } },
    },
    orderBy: [{ projectId: "asc" }, { asOfDate: "desc" }],
  });
  const latest = new Map<string, (typeof snapshots)[number]>();
  for (const snapshot of snapshots) {
    if (!latest.has(snapshot.projectId)) latest.set(snapshot.projectId, snapshot);
  }
  return [...latest.values()];
}

async function projectProfitability(
  input: CompanyReportInput,
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
  const revenueMinor = rows.reduce((sum, row) => sum + Number(row.values.revenueMinor ?? 0), 0);
  const profitMinor = rows.reduce((sum, row) => sum + Number(row.values.profitMinor ?? 0), 0);
  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Project profitability: ${percent(profitMinor, revenueMinor)}% margin across ${rows.length} projects.`,
    metrics: [
      metric("Project revenue", revenueMinor, "money"),
      metric("Project profit", profitMinor, "money"),
      metric("Margin", percent(profitMinor, revenueMinor), "percent"),
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

async function departmentPerformance(
  input: CompanyReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const objectives = await prisma.objective.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      scope: "DEPARTMENT",
      OR: [{ startDate: null }, { startDate: { lte: input.range.to } }],
      dueDate: { gte: input.range.from },
    },
    select: {
      id: true,
      title: true,
      progressPct: true,
      department: { select: { id: true, name: true } },
    },
  });
  const byDepartment = new Map<string, { id: string; progress: number[]; objectives: number }>();
  for (const objective of objectives) {
    const label = objective.department?.name ?? "Unassigned";
    const current = byDepartment.get(label) ?? {
      id: objective.department?.id ?? "unassigned",
      progress: [],
      objectives: 0,
    };
    current.progress.push(objective.progressPct);
    current.objectives += 1;
    byDepartment.set(label, current);
  }
  const rows = [...byDepartment.entries()].map(([department, values]) => ({
    id: values.id,
    href: "/departments",
    values: {
      department,
      objectiveCount: values.objectives,
      progressPct: average(values.progress.reduce((sum, value) => sum + value, 0), values.progress.length),
    },
  }));
  const series = rows.map((row) => ({
    label: String(row.values.department),
    value: Number(row.values.progressPct),
    href: row.href,
  }));
  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary:
      series.length > 0
        ? accessibleSeriesSummary("Department performance", series, "percent")
        : "Department performance: no department objectives in the selected range.",
    metrics: [metric("Department objectives", objectives.length, "number")],
    series,
    columns: [
      { key: "department", label: "Department" },
      { key: "objectiveCount", label: "Objectives", format: "number" },
      { key: "progressPct", label: "Progress", format: "percent" },
    ],
    rows,
    drilldownHref: "/departments",
  });
}

async function objectiveProgress(
  input: CompanyReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const objectives = await prisma.objective.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      scope: "COMPANY",
      OR: [{ startDate: null }, { startDate: { lte: input.range.to } }],
      dueDate: { gte: input.range.from },
    },
    select: { id: true, title: true, status: true, progressPct: true, dueDate: true },
    orderBy: { dueDate: "asc" },
  });
  const averageProgress = average(
    objectives.reduce((sum, objective) => sum + objective.progressPct, 0),
    objectives.length,
  );
  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Company objective progress: ${averageProgress}% average progress across ${objectives.length} objectives.`,
    metrics: [
      metric("Objective progress", averageProgress, "percent"),
      metric("Company objectives", objectives.length, "number"),
    ],
    columns: [
      { key: "objective", label: "Objective" },
      { key: "status", label: "Status" },
      { key: "progressPct", label: "Progress", format: "percent" },
      { key: "dueDate", label: "Due" },
    ],
    rows: objectives.map((objective) => ({
      id: objective.id,
      href: "/company/objectives",
      values: {
        objective: objective.title,
        status: objective.status,
        progressPct: objective.progressPct,
        dueDate: objective.dueDate?.toISOString().slice(0, 10) ?? null,
      },
    })),
    drilldownHref: "/company/objectives",
  });
}

async function headcountTrend(
  input: CompanyReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const employees = await prisma.employee.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      joiningDate: { lte: input.range.to },
    },
    select: { id: true, joiningDate: true, employmentStatus: true },
  });
  const counts = new Map<string, number>();
  for (const employee of employees) {
    if (employee.joiningDate >= input.range.from) {
      counts.set(dayKey(employee.joiningDate), (counts.get(dayKey(employee.joiningDate)) ?? 0) + 1);
    }
  }
  const activeAtEnd = employees.filter((employee) =>
    ["ACTIVE", "PROBATION", "NOTICE"].includes(employee.employmentStatus),
  ).length;
  const series = seriesFromMap(counts);
  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary:
      series.length > 0
        ? accessibleSeriesSummary("Headcount joining cohort trend", series)
        : `Headcount trend: no new joiners in the selected range; active headcount is ${activeAtEnd}.`,
    metrics: [
      metric("Active headcount", activeAtEnd, "number"),
      metric("New joiners", series.reduce((sum, point) => sum + point.value, 0), "number"),
    ],
    series,
    drilldownHref: "/employees",
  });
}

async function attendanceTrend(
  input: CompanyReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const records = await prisma.attendanceRecord.findMany({
    where: {
      organizationId: input.user.organizationId,
      date: { gte: input.range.from, lte: input.range.to },
      status: { in: ["PRESENT", "WFH", "REMOTE"] },
    },
    select: { id: true, date: true },
  });
  const counts = new Map<string, number>();
  for (const record of records) {
    counts.set(dayKey(record.date), (counts.get(dayKey(record.date)) ?? 0) + 1);
  }
  const series = seriesFromMap(counts);
  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary:
      series.length > 0
        ? accessibleSeriesSummary("Attendance trend", series)
        : "Attendance trend: no present/WFH/remote attendance records in the selected range.",
    metrics: [metric("Attendance records", records.length, "number")],
    series,
    drilldownHref: "/hr/attendance",
  });
}

async function expenseTrend(
  input: CompanyReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const expenses = await prisma.expense.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      OR: [
        { spentAt: { gte: input.range.from, lte: input.range.to } },
        { spentAt: null, createdAt: { gte: input.range.from, lte: input.range.to } },
      ],
    },
    select: {
      id: true,
      amountMinor: true,
      currencyCode: true,
      spentAt: true,
      createdAt: true,
      status: true,
    },
  });
  const totals = new Map<string, number>();
  for (const expense of expenses) {
    const asOf = expense.spentAt ?? expense.createdAt;
    const amountMinor = await convertMoney({
      organizationId: input.user.organizationId,
      amountMinor: expense.amountMinor,
      fromCurrency: expense.currencyCode,
      toCurrency: currencyCode,
      asOf,
    });
    totals.set(dayKey(asOf), (totals.get(dayKey(asOf)) ?? 0) + amountMinor);
  }
  const totalMinor = [...totals.values()].reduce((sum, value) => sum + value, 0);
  const series = moneySeries(totals);
  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary:
      series.length > 0
        ? accessibleSeriesSummary("Expense trend", series, "money")
        : "Expense trend: no expenses in the selected range.",
    metrics: [
      metric("Expense total", totalMinor, "money"),
      metric("Expense count", expenses.length, "number"),
    ],
    series,
    drilldownHref: "/finance/expenses",
  });
}

async function receivableAging(
  input: CompanyReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const today = new Date();
  today.setUTCHours(0, 0, 0, 0);
  const invoices = await prisma.invoice.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      balanceMinor: { gt: 0 },
      status: { in: OPEN_INVOICE_STATUSES },
    },
    select: {
      id: true,
      invoiceNumber: true,
      dueDate: true,
      issueDate: true,
      balanceMinor: true,
      currencyCode: true,
    },
  });
  const buckets = new Map<string, number>([
    ["Current", 0],
    ["1-30 days overdue", 0],
    ["31+ days overdue", 0],
  ]);
  for (const invoice of invoices) {
    const dueDate = invoice.dueDate ?? today;
    const days = Math.floor((today.getTime() - dueDate.getTime()) / 86400000);
    const label = days <= 0 ? "Current" : days <= 30 ? "1-30 days overdue" : "31+ days overdue";
    const amountMinor = await convertMoney({
      organizationId: input.user.organizationId,
      amountMinor: invoice.balanceMinor,
      fromCurrency: invoice.currencyCode,
      toCurrency: currencyCode,
      asOf: invoice.issueDate ?? dueDate,
    });
    buckets.set(label, (buckets.get(label) ?? 0) + amountMinor);
  }
  const totalMinor = [...buckets.values()].reduce((sum, value) => sum + value, 0);
  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: accessibleSeriesSummary("Receivable aging", moneySeries(buckets), "money"),
    metrics: [
      metric("Outstanding receivables", totalMinor, "money"),
      metric("Open invoices", invoices.length, "number"),
    ],
    series: moneySeries(buckets),
    columns: [
      { key: "bucket", label: "Bucket" },
      { key: "amountMinor", label: "Amount", format: "money" },
    ],
    rows: [...buckets.entries()].map(([bucket, amountMinor]) => ({
      id: bucket,
      href: "/finance/invoices",
      values: { bucket, amountMinor },
    })),
    drilldownHref: "/finance/invoices",
  });
}

async function monthlyBusinessSummary(
  input: CompanyReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const [
    invoices,
    payments,
    activeProjects,
    atRiskProjects,
    headcount,
    openReceivables,
    objectives,
  ] = await Promise.all([
    prisma.invoice.findMany({
      where: {
        organizationId: input.user.organizationId,
        deletedAt: null,
        status: { not: "DRAFT" },
        issueDate: { gte: input.range.from, lte: input.range.to },
      },
      select: { totalMinor: true, currencyCode: true, issueDate: true },
    }),
    prisma.payment.findMany({
      where: {
        organizationId: input.user.organizationId,
        deletedAt: null,
        receivedAt: { gte: input.range.from, lte: input.range.to },
      },
      select: { amountMinor: true, currencyCode: true, receivedAt: true },
    }),
    prisma.project.count({
      where: {
        organizationId: input.user.organizationId,
        deletedAt: null,
        status: { in: ACTIVE_PROJECT_STATUSES },
      },
    }),
    prisma.project.count({
      where: { organizationId: input.user.organizationId, deletedAt: null, status: "AT_RISK" },
    }),
    prisma.employee.count({
      where: {
        organizationId: input.user.organizationId,
        deletedAt: null,
        employmentStatus: { in: ["ACTIVE", "PROBATION", "NOTICE"] },
      },
    }),
    prisma.invoice.findMany({
      where: {
        organizationId: input.user.organizationId,
        deletedAt: null,
        balanceMinor: { gt: 0 },
        status: { in: OPEN_INVOICE_STATUSES },
      },
      select: { balanceMinor: true, currencyCode: true, issueDate: true, dueDate: true },
    }),
    prisma.objective.findMany({
      where: { organizationId: input.user.organizationId, deletedAt: null, scope: "COMPANY" },
      select: { progressPct: true },
    }),
  ]);
  let invoicedMinor = 0;
  for (const invoice of invoices) {
    invoicedMinor += await convertMoney({
      organizationId: input.user.organizationId,
      amountMinor: invoice.totalMinor,
      fromCurrency: invoice.currencyCode,
      toCurrency: currencyCode,
      asOf: invoice.issueDate ?? input.range.to,
    });
  }
  let collectedMinor = 0;
  for (const payment of payments) {
    collectedMinor += await convertMoney({
      organizationId: input.user.organizationId,
      amountMinor: payment.amountMinor,
      fromCurrency: payment.currencyCode,
      toCurrency: currencyCode,
      asOf: payment.receivedAt,
    });
  }
  let outstandingMinor = 0;
  for (const invoice of openReceivables) {
    outstandingMinor += await convertMoney({
      organizationId: input.user.organizationId,
      amountMinor: invoice.balanceMinor,
      fromCurrency: invoice.currencyCode,
      toCurrency: currencyCode,
      asOf: invoice.issueDate ?? invoice.dueDate ?? input.range.to,
    });
  }
  const objectiveProgress = average(
    objectives.reduce((sum, objective) => sum + objective.progressPct, 0),
    objectives.length,
  );
  const rows = [
    { id: "invoiced", values: { area: "Invoiced revenue", value: invoicedMinor, format: "money" } },
    { id: "collected", values: { area: "Collected revenue", value: collectedMinor, format: "money" } },
    { id: "outstanding", values: { area: "Outstanding receivables", value: outstandingMinor, format: "money" } },
    { id: "projects", values: { area: "Active projects", value: activeProjects, format: "number" } },
    { id: "risk", values: { area: "At-risk projects", value: atRiskProjects, format: "number" } },
    { id: "headcount", values: { area: "Headcount", value: headcount, format: "number" } },
    { id: "objectives", values: { area: "Company objective progress", value: objectiveProgress, format: "percent" } },
  ];
  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Monthly business summary: ${Math.round(invoicedMinor / 100)} ${currencyCode} invoiced, ${Math.round(collectedMinor / 100)} ${currencyCode} collected, ${activeProjects} active projects, and ${headcount} employees.`,
    metrics: [
      metric("Invoiced revenue", invoicedMinor, "money"),
      metric("Collected revenue", collectedMinor, "money"),
      metric("Outstanding receivables", outstandingMinor, "money"),
      metric("Active projects", activeProjects, "number"),
      metric("Headcount", headcount, "number"),
      metric("Objective progress", objectiveProgress, "percent"),
    ],
    columns: [
      { key: "area", label: "Area" },
      { key: "value", label: "Value", format: "number" },
      { key: "format", label: "Format" },
    ],
    rows,
    drilldownHref: "/dashboard",
  });
}

