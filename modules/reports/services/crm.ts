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

type CrmReportInput = {
  key: string;
  definition: ReportDefinition;
  user: SessionUser & { organizationId: string };
  range: ReportDateRange;
};

function percent(numerator: number, denominator: number): number {
  return denominator > 0 ? Math.round((numerator / denominator) * 1000) / 10 : 0;
}

function average(total: number, count: number): number {
  return count > 0 ? Math.round(total / count) : 0;
}

function daysBetween(from: Date, to: Date): number {
  return Math.max(0, Math.round((to.getTime() - from.getTime()) / 86400000));
}

function jsonLabels(value: unknown): string[] {
  if (!value) return ["Unspecified"];
  if (Array.isArray(value)) {
    const labels = value
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object" && "name" in item) {
          return String((item as { name?: unknown }).name ?? "");
        }
        return "";
      })
      .filter(Boolean);
    return labels.length > 0 ? labels : ["Unspecified"];
  }
  if (typeof value === "string") return [value];
  return ["Unspecified"];
}

async function convertMoney(input: {
  organizationId: string;
  amountMinor: number;
  fromCurrency: string;
  toCurrency: string;
  asOf: Date;
}): Promise<number> {
  const currency = assertSingleCurrency([input.fromCurrency], "CRM report money row");
  const converted = await convertMinorUnits({
    organizationId: input.organizationId,
    amountMinor: input.amountMinor,
    fromCurrency: currency,
    toCurrency: input.toCurrency,
    asOf: input.asOf,
  });
  return converted.amountMinor;
}

export async function runCrmReport(input: CrmReportInput): Promise<ReportPayload> {
  const currencyCode = await organizationCurrency(input.user.organizationId);

  switch (input.key) {
    case "crm.leads-by-source":
      return leadsBySource(input, currencyCode);
    case "crm.leads-by-campaign":
      return leadsByCampaign(input, currencyCode);
    case "crm.leads-by-service":
      return leadsByService(input, currencyCode);
    case "crm.leads-by-country":
      return leadsByCountry(input, currencyCode);
    case "crm.leads-by-salesperson":
      return leadsBySalesperson(input, currencyCode);
    case "crm.funnel-conversion":
      return funnelConversion(input, currencyCode);
    case "crm.stage-aging":
      return stageAging(input, currencyCode);
    case "crm.win-rate":
      return winRate(input, currencyCode);
    case "crm.loss-reasons":
      return lossReasons(input, currencyCode);
    case "crm.average-deal-size":
      return averageDealSize(input, currencyCode);
    case "crm.sales-cycle-length":
      return salesCycleLength(input, currencyCode);
    case "crm.follow-up-compliance":
      return followUpCompliance(input, currencyCode);
    case "crm.forecast-accuracy":
      return forecastAccuracy(input, currencyCode);
    case "crm.pipeline-value":
      return pipelineValue(input, currencyCode);
    case "crm.weighted-forecast":
      return weightedForecast(input, currencyCode);
    case "crm.monthly-lead-trend":
      return monthlyLeadTrend(input, currencyCode);
    default:
      return buildPayload({
        definition: input.definition,
        range: input.range,
        currencyCode,
        summary: `${input.definition.title}: no implementation for ${input.key}.`,
      });
  }
}

async function leadsBySource(
  input: CrmReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const leads = await prisma.lead.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      createdAt: { gte: input.range.from, lte: input.range.to },
    },
    select: {
      id: true,
      source: { select: { id: true, name: true } },
    },
  });
  return leadDimensionPayload(input, currencyCode, {
    title: "Leads by source",
    dimensionKey: "source",
    href: "/crm/leads",
    rows: leads.map((lead) => ({
      id: lead.source?.id ?? "unspecified",
      label: lead.source?.name ?? "Unspecified",
    })),
  });
}

async function leadsByCampaign(
  input: CrmReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const leads = await prisma.lead.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      createdAt: { gte: input.range.from, lte: input.range.to },
    },
    select: {
      id: true,
      campaign: { select: { id: true, name: true } },
    },
  });
  return leadDimensionPayload(input, currencyCode, {
    title: "Leads by campaign",
    dimensionKey: "campaign",
    href: "/crm/leads",
    rows: leads.map((lead) => ({
      id: lead.campaign?.id ?? "unspecified",
      label: lead.campaign?.name ?? "Unspecified",
    })),
  });
}

async function leadsByService(
  input: CrmReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const leads = await prisma.lead.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      createdAt: { gte: input.range.from, lte: input.range.to },
    },
    select: { id: true, interestedServices: true },
  });

  const rows = leads.flatMap((lead) =>
    jsonLabels(lead.interestedServices).map((label) => ({
      id: label,
      label,
    })),
  );

  return leadDimensionPayload(input, currencyCode, {
    title: "Leads by service",
    dimensionKey: "service",
    href: "/crm/leads",
    rows,
  });
}

async function leadsByCountry(
  input: CrmReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const leads = await prisma.lead.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      createdAt: { gte: input.range.from, lte: input.range.to },
    },
    select: { id: true, country: true },
  });
  return leadDimensionPayload(input, currencyCode, {
    title: "Leads by country",
    dimensionKey: "country",
    href: "/crm/leads",
    rows: leads.map((lead) => ({
      id: lead.country ?? "unspecified",
      label: lead.country ?? "Unspecified",
    })),
  });
}

async function leadsBySalesperson(
  input: CrmReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const leads = await prisma.lead.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      createdAt: { gte: input.range.from, lte: input.range.to },
    },
    select: {
      id: true,
      assignedUserId: true,
      assignedUser: { select: { name: true, email: true } },
    },
  });
  return leadDimensionPayload(input, currencyCode, {
    title: "Leads by salesperson",
    dimensionKey: "salesperson",
    href: "/crm/leads",
    rows: leads.map((lead) => ({
      id: lead.assignedUserId ?? "unassigned",
      label: lead.assignedUser?.name ?? lead.assignedUser?.email ?? "Unassigned",
    })),
  });
}

function leadDimensionPayload(
  input: CrmReportInput,
  currencyCode: string,
  config: {
    title: string;
    dimensionKey: string;
    href: string;
    rows: Array<{ id: string; label: string }>;
  },
): ReportPayload {
  const counts = new Map<string, number>();
  const ids = new Map<string, string>();
  for (const row of config.rows) {
    ids.set(row.label, row.id);
    counts.set(row.label, (counts.get(row.label) ?? 0) + 1);
  }
  const series = seriesFromMap(counts);
  const rows = series
    .sort((a, b) => b.value - a.value)
    .map((point) => ({
      id: ids.get(point.label) ?? point.label,
      href: config.href,
      values: {
        [config.dimensionKey]: point.label,
        leadCount: point.value,
      },
    }));

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary:
      series.length > 0
        ? accessibleSeriesSummary(config.title, series)
        : `${config.title}: no leads in the selected range.`,
    metrics: [metric("Lead count", config.rows.length, "number")],
    series,
    columns: [
      { key: config.dimensionKey, label: config.title.replace("Leads by ", "") },
      { key: "leadCount", label: "Leads", format: "number" },
    ],
    rows,
    drilldownHref: config.href,
  });
}

async function funnelConversion(
  input: CrmReportInput,
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
        select: { id: true },
      },
    },
    orderBy: { sortOrder: "asc" },
  });
  const series = stages.map((stage) => ({
    label: stage.name,
    value: stage.deals.length,
    href: "/crm/deals",
  }));
  const total = series.reduce((sum, point) => sum + point.value, 0);

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary:
      series.length > 0
        ? accessibleSeriesSummary("Open deals by funnel stage", series)
        : "Funnel conversion: no open deals found.",
    metrics: [metric("Open deals", total, "number")],
    series,
    columns: [
      { key: "stage", label: "Stage" },
      { key: "probability", label: "Probability", format: "percent" },
      { key: "dealCount", label: "Open deals", format: "number" },
    ],
    rows: stages.map((stage) => ({
      id: stage.id,
      href: "/crm/deals",
      values: {
        stage: stage.name,
        probability: stage.probability,
        dealCount: stage.deals.length,
      },
    })),
    drilldownHref: "/crm/deals",
  });
}

async function stageAging(
  input: CrmReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const deals = await prisma.deal.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      closedAt: null,
    },
    select: {
      id: true,
      createdAt: true,
      stage: { select: { id: true, name: true } },
      stageHistory: {
        orderBy: { createdAt: "desc" },
        take: 1,
        select: { createdAt: true },
      },
    },
  });

  const now = new Date();
  const buckets = new Map<string, { id: string; days: number; count: number }>();
  for (const deal of deals) {
    const label = deal.stage?.name ?? "Unstaged";
    const current = buckets.get(label) ?? {
      id: deal.stage?.id ?? "unstaged",
      days: 0,
      count: 0,
    };
    current.days += daysBetween(deal.stageHistory[0]?.createdAt ?? deal.createdAt, now);
    current.count += 1;
    buckets.set(label, current);
  }

  const rows: ReportTableRow[] = [...buckets.entries()].map(([stage, value]) => ({
    id: value.id,
    href: "/crm/deals",
    values: {
      stage,
      dealCount: value.count,
      averageDays: average(value.days, value.count),
    },
  }));
  const series = rows.map((row) => ({
    label: String(row.values.stage),
    value: Number(row.values.averageDays),
    href: row.href,
  }));

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary:
      series.length > 0
        ? accessibleSeriesSummary("Average stage aging in days", series, "days")
        : "Stage aging: no open deals found.",
    metrics: [metric("Open deals", deals.length, "number")],
    series,
    columns: [
      { key: "stage", label: "Stage" },
      { key: "dealCount", label: "Open deals", format: "number" },
      { key: "averageDays", label: "Average days", format: "days" },
    ],
    rows,
    drilldownHref: "/crm/deals",
  });
}

async function winRate(
  input: CrmReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const deals = await prisma.deal.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      closedAt: { gte: input.range.from, lte: input.range.to },
    },
    select: {
      id: true,
      stage: { select: { isClosedWon: true, isClosedLost: true } },
    },
  });
  const won = deals.filter((deal) => deal.stage?.isClosedWon).length;
  const lost = deals.filter((deal) => deal.stage?.isClosedLost).length;
  const closed = deals.length;
  const rate = percent(won, closed);

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Win rate: ${rate}% from ${won} won and ${lost} lost deals in the selected range.`,
    metrics: [
      metric("Win rate", rate, "percent"),
      metric("Won deals", won, "number"),
      metric("Closed deals", closed, "number"),
    ],
    series: [
      { label: "Won", value: won, href: "/crm/deals" },
      { label: "Lost", value: lost, href: "/crm/deals" },
    ],
    columns: [
      { key: "status", label: "Outcome" },
      { key: "dealCount", label: "Deals", format: "number" },
      { key: "sharePct", label: "Share", format: "percent" },
    ],
    rows: [
      {
        id: "won",
        href: "/crm/deals",
        values: { status: "Won", dealCount: won, sharePct: percent(won, closed) },
      },
      {
        id: "lost",
        href: "/crm/deals",
        values: { status: "Lost", dealCount: lost, sharePct: percent(lost, closed) },
      },
    ],
    drilldownHref: "/crm/deals",
  });
}

async function lossReasons(
  input: CrmReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const deals = await prisma.deal.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      lostReasonId: { not: null },
      closedAt: { gte: input.range.from, lte: input.range.to },
    },
    select: {
      id: true,
      lostReason: { select: { id: true, name: true } },
    },
  });
  const counts = new Map<string, number>();
  const ids = new Map<string, string>();
  for (const deal of deals) {
    const label = deal.lostReason?.name ?? "Unspecified";
    ids.set(label, deal.lostReason?.id ?? "unspecified");
    counts.set(label, (counts.get(label) ?? 0) + 1);
  }
  const series = seriesFromMap(counts);

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary:
      series.length > 0
        ? accessibleSeriesSummary("Loss reasons", series)
        : "Loss reasons: no closed-lost deals with reasons in the selected range.",
    metrics: [metric("Loss reason records", deals.length, "number")],
    series,
    columns: [
      { key: "reason", label: "Reason" },
      { key: "dealCount", label: "Deals", format: "number" },
    ],
    rows: series.map((point) => ({
      id: ids.get(point.label) ?? point.label,
      href: "/crm/deals",
      values: { reason: point.label, dealCount: point.value },
    })),
    drilldownHref: "/crm/deals",
  });
}

async function averageDealSize(
  input: CrmReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const deals = await prisma.deal.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      closedAt: { gte: input.range.from, lte: input.range.to },
      stage: { isClosedWon: true },
    },
    select: {
      id: true,
      name: true,
      valueMinor: true,
      currencyCode: true,
      closedAt: true,
      company: { select: { name: true } },
    },
    orderBy: { closedAt: "desc" },
  });
  const rows: ReportTableRow[] = [];
  for (const deal of deals) {
    const amountMinor = await convertMoney({
      organizationId: input.user.organizationId,
      amountMinor: deal.valueMinor,
      fromCurrency: deal.currencyCode,
      toCurrency: currencyCode,
      asOf: deal.closedAt ?? input.range.to,
    });
    rows.push({
      id: deal.id,
      href: `/crm/deals/${deal.id}`,
      values: {
        deal: deal.name,
        company: deal.company?.name ?? "Unassigned",
        closedAt: deal.closedAt?.toISOString().slice(0, 10) ?? null,
        valueMinor: amountMinor,
      },
    });
  }
  const total = rows.reduce((sum, row) => sum + Number(row.values.valueMinor ?? 0), 0);
  const avg = average(total, rows.length);

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Average deal size: ${Math.round(avg / 100)} ${currencyCode} across ${rows.length} won deals.`,
    metrics: [
      metric("Average deal size", avg, "money"),
      metric("Won revenue", total, "money"),
      metric("Won deals", rows.length, "number"),
    ],
    columns: [
      { key: "deal", label: "Deal" },
      { key: "company", label: "Client" },
      { key: "closedAt", label: "Closed" },
      { key: "valueMinor", label: "Value", format: "money" },
    ],
    rows,
    drilldownHref: "/crm/deals",
  });
}

async function salesCycleLength(
  input: CrmReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const deals = await prisma.deal.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      closedAt: { gte: input.range.from, lte: input.range.to },
      stage: { isClosedWon: true },
    },
    select: { id: true, name: true, createdAt: true, closedAt: true },
    orderBy: { closedAt: "desc" },
  });
  const rows = deals.map((deal) => ({
    id: deal.id,
    href: `/crm/deals/${deal.id}`,
    values: {
      deal: deal.name,
      createdAt: deal.createdAt.toISOString().slice(0, 10),
      closedAt: deal.closedAt?.toISOString().slice(0, 10) ?? null,
      cycleDays: deal.closedAt ? daysBetween(deal.createdAt, deal.closedAt) : 0,
    },
  }));
  const totalDays = rows.reduce((sum, row) => sum + Number(row.values.cycleDays), 0);
  const avgDays = average(totalDays, rows.length);

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Sales-cycle length: ${avgDays} average days across ${rows.length} won deals.`,
    metrics: [
      metric("Average sales-cycle length", avgDays, "days"),
      metric("Won deals", rows.length, "number"),
    ],
    columns: [
      { key: "deal", label: "Deal" },
      { key: "createdAt", label: "Created" },
      { key: "closedAt", label: "Closed" },
      { key: "cycleDays", label: "Cycle days", format: "days" },
    ],
    rows,
    drilldownHref: "/crm/deals",
  });
}

async function followUpCompliance(
  input: CrmReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const followUps = await prisma.followUp.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      dueAt: { gte: input.range.from, lte: input.range.to },
    },
    select: { id: true, dueAt: true, completedAt: true, leadId: true },
  });
  const completed = followUps.filter((item) => item.completedAt).length;
  const overdue = followUps.filter(
    (item) => !item.completedAt && item.dueAt.getTime() < Date.now(),
  ).length;
  const pending = followUps.length - completed - overdue;

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Follow-up compliance: ${percent(completed, followUps.length)}% completed, ${overdue} overdue, ${pending} pending.`,
    metrics: [
      metric("Completion rate", percent(completed, followUps.length), "percent"),
      metric("Completed follow-ups", completed, "number"),
      metric("Overdue follow-ups", overdue, "number"),
    ],
    series: [
      { label: "Completed", value: completed, href: "/crm/leads" },
      { label: "Overdue", value: overdue, href: "/crm/leads" },
      { label: "Pending", value: pending, href: "/crm/leads" },
    ],
    columns: [
      { key: "status", label: "Status" },
      { key: "followUpCount", label: "Follow-ups", format: "number" },
    ],
    rows: [
      { id: "completed", href: "/crm/leads", values: { status: "Completed", followUpCount: completed } },
      { id: "overdue", href: "/crm/leads", values: { status: "Overdue", followUpCount: overdue } },
      { id: "pending", href: "/crm/leads", values: { status: "Pending", followUpCount: pending } },
    ],
    drilldownHref: "/crm/leads",
  });
}

async function forecastAccuracy(
  input: CrmReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const [openDeals, wonDeals] = await Promise.all([
    prisma.deal.findMany({
      where: {
        organizationId: input.user.organizationId,
        deletedAt: null,
        closedAt: null,
      },
      select: {
        id: true,
        valueMinor: true,
        currencyCode: true,
        probability: true,
        expectedCloseDate: true,
        createdAt: true,
      },
    }),
    prisma.deal.findMany({
      where: {
        organizationId: input.user.organizationId,
        deletedAt: null,
        closedAt: { gte: input.range.from, lte: input.range.to },
        stage: { isClosedWon: true },
      },
      select: {
        id: true,
        valueMinor: true,
        currencyCode: true,
        closedAt: true,
      },
    }),
  ]);

  let forecastMinor = 0;
  for (const deal of openDeals) {
    const weighted = Math.round((deal.valueMinor * (deal.probability ?? 0)) / 100);
    forecastMinor += await convertMoney({
      organizationId: input.user.organizationId,
      amountMinor: weighted,
      fromCurrency: deal.currencyCode,
      toCurrency: currencyCode,
      asOf: deal.expectedCloseDate ?? deal.createdAt,
    });
  }

  let closedWonMinor = 0;
  for (const deal of wonDeals) {
    closedWonMinor += await convertMoney({
      organizationId: input.user.organizationId,
      amountMinor: deal.valueMinor,
      fromCurrency: deal.currencyCode,
      toCurrency: currencyCode,
      asOf: deal.closedAt ?? input.range.to,
    });
  }

  const accuracy =
    forecastMinor > 0
      ? Math.max(0, 100 - percent(Math.abs(forecastMinor - closedWonMinor), forecastMinor))
      : 0;

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Forecast accuracy: ${accuracy}% with ${Math.round(forecastMinor / 100)} ${currencyCode} weighted forecast and ${Math.round(closedWonMinor / 100)} ${currencyCode} closed won.`,
    metrics: [
      metric("Weighted forecast", forecastMinor, "money"),
      metric("Closed won", closedWonMinor, "money"),
      metric("Forecast accuracy", accuracy, "percent"),
    ],
    series: [
      { label: "Weighted forecast", value: Math.round(forecastMinor / 100), href: "/crm/deals" },
      { label: "Closed won", value: Math.round(closedWonMinor / 100), href: "/crm/deals" },
    ],
    columns: [
      { key: "measure", label: "Measure" },
      { key: "amountMinor", label: "Amount", format: "money" },
    ],
    rows: [
      {
        id: "forecast",
        href: "/crm/deals",
        values: { measure: "Weighted forecast", amountMinor: forecastMinor },
      },
      {
        id: "closed-won",
        href: "/crm/deals",
        values: { measure: "Closed won", amountMinor: closedWonMinor },
      },
    ],
    drilldownHref: "/crm/deals",
  });
}


async function pipelineValue(
  input: CrmReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const leads = await prisma.lead.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      stage: { isClosedWon: false, isClosedLost: false },
    },
    select: {
      id: true,
      estimatedValueMinor: true,
      currencyCode: true,
      stage: { select: { id: true, name: true, sortOrder: true } },
      createdAt: true,
    },
  });

  const byStage = new Map<
    string,
    { label: string; value: number; sort: number; ids: string[] }
  >();
  for (const lead of leads) {
    const key = lead.stage?.id ?? "none";
    const label = lead.stage?.name ?? "Unstaged";
    const amount = await convertMoney({
      organizationId: input.user.organizationId,
      amountMinor: lead.estimatedValueMinor ?? 0,
      fromCurrency: lead.currencyCode,
      toCurrency: currencyCode,
      asOf: lead.createdAt,
    });
    const row = byStage.get(key) ?? {
      label,
      value: 0,
      sort: lead.stage?.sortOrder ?? 999,
      ids: [],
    };
    row.value += amount;
    row.ids.push(lead.id);
    byStage.set(key, row);
  }

  const ordered = [...byStage.values()].sort((a, b) => a.sort - b.sort);
  const total = ordered.reduce((sum, row) => sum + row.value, 0);

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Open pipeline value ${Math.round(total / 100)} ${currencyCode} across ${ordered.length} stages.`,
    metrics: [
      metric("Pipeline value", total, "money"),
      metric("Open leads", leads.length, "number"),
    ],
    series: ordered.map((row) => ({
      label: row.label,
      value: Math.round(row.value / 100),
      href: "/crm/pipeline",
    })),
    columns: [
      { key: "stage", label: "Stage" },
      { key: "valueMinor", label: "Value", format: "money" },
      { key: "leads", label: "Leads", format: "number" },
    ],
    rows: ordered.map((row) => ({
      id: row.label,
      href: "/crm/pipeline",
      values: {
        stage: row.label,
        valueMinor: row.value,
        leads: row.ids.length,
      },
    })),
    drilldownHref: "/crm/pipeline",
  });
}

async function weightedForecast(
  input: CrmReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const leads = await prisma.lead.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      stage: { isClosedWon: false, isClosedLost: false },
    },
    select: {
      id: true,
      estimatedValueMinor: true,
      currencyCode: true,
      probability: true,
      stage: { select: { name: true, probability: true } },
      createdAt: true,
    },
  });

  let weighted = 0;
  const rows: ReportTableRow[] = [];
  for (const lead of leads) {
    const probability = lead.probability ?? lead.stage?.probability ?? 0;
    const amount = await convertMoney({
      organizationId: input.user.organizationId,
      amountMinor: lead.estimatedValueMinor ?? 0,
      fromCurrency: lead.currencyCode,
      toCurrency: currencyCode,
      asOf: lead.createdAt,
    });
    const w = Math.round((amount * probability) / 100);
    weighted += w;
    rows.push({
      id: lead.id,
      href: `/crm/leads/${lead.id}`,
      values: {
        stage: lead.stage?.name ?? "—",
        probability,
        valueMinor: amount,
        weightedMinor: w,
      },
    });
  }

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Weighted forecast ${Math.round(weighted / 100)} ${currencyCode} from ${leads.length} open leads.`,
    metrics: [
      metric("Weighted forecast", weighted, "money"),
      metric("Open leads", leads.length, "number"),
    ],
    series: [
      {
        label: "Weighted forecast",
        value: Math.round(weighted / 100),
        href: "/crm/pipeline",
      },
    ],
    columns: [
      { key: "stage", label: "Stage" },
      { key: "probability", label: "Probability", format: "percent" },
      { key: "valueMinor", label: "Value", format: "money" },
      { key: "weightedMinor", label: "Weighted", format: "money" },
    ],
    rows,
    drilldownHref: "/crm/pipeline",
  });
}

async function monthlyLeadTrend(
  input: CrmReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const leads = await prisma.lead.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      createdAt: { gte: input.range.from, lte: input.range.to },
    },
    select: { id: true, createdAt: true },
  });

  const byMonth = new Map<string, number>();
  for (const lead of leads) {
    const key = lead.createdAt.toISOString().slice(0, 7);
    byMonth.set(key, (byMonth.get(key) ?? 0) + 1);
  }
  const months = [...byMonth.entries()].sort(([a], [b]) => a.localeCompare(b));

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `${leads.length} leads created across ${months.length} months.`,
    metrics: [metric("Leads created", leads.length, "number")],
    series: months.map(([label, value]) => ({
      label,
      value,
      href: "/crm/leads",
    })),
    columns: [
      { key: "month", label: "Month" },
      { key: "leads", label: "Leads", format: "number" },
    ],
    rows: months.map(([month, count]) => ({
      id: month,
      href: "/crm/leads",
      values: { month, leads: count },
    })),
    drilldownHref: "/crm/leads",
  });
}
