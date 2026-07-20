import "server-only";

import type { MembershipRole } from "@prisma/client";

import { prisma } from "@/database";
import {
  builderDefinitionSchema,
  getBuilderDataset,
  type BuilderDefinition,
} from "@/modules/reports/builder/datasets";
import { organizationCurrency } from "@/modules/reports/currency";
import { parseReportRange } from "@/modules/reports/date-range";
import {
  accessibleSeriesSummary,
  buildPayload,
  metric,
  seriesFromMap,
} from "@/modules/reports/helpers";
import type { ReportPayload } from "@/modules/reports/types";
import type { SessionUser } from "@/permissions";
import { ForbiddenError, requireOrganization } from "@/permissions";
import { hasPermission } from "@/permissions/types";

function ensureDatasetAccess(user: SessionUser, datasetId: string) {
  const dataset = getBuilderDataset(datasetId);
  if (!dataset) throw new ForbiddenError("Unknown dataset");
  if (!hasPermission(user.role as MembershipRole | null, dataset.permission)) {
    throw new ForbiddenError(`Missing permission: ${dataset.permission}`);
  }
  return dataset;
}

function validateFieldRefs(definition: BuilderDefinition) {
  const dataset = getBuilderDataset(definition.datasetId);
  if (!dataset) throw new ForbiddenError("Unknown dataset");
  const fieldIds = new Set(dataset.fields.map((field) => field.id));
  const measureIds = new Set(dataset.measures.map((measure) => measure.id));

  for (const field of definition.fields) {
    if (!fieldIds.has(field as never)) {
      throw new ForbiddenError(`Field not allowed: ${field}`);
    }
  }
  for (const field of definition.groupBy) {
    if (!fieldIds.has(field as never)) {
      throw new ForbiddenError(`Group field not allowed: ${field}`);
    }
  }
  for (const filter of definition.filters) {
    if (!fieldIds.has(filter.field as never)) {
      throw new ForbiddenError(`Filter field not allowed: ${filter.field}`);
    }
  }
  for (const measure of definition.measures) {
    if (!measureIds.has(measure as never)) {
      throw new ForbiddenError(`Measure not allowed: ${measure}`);
    }
  }
}

export async function executeBuilderReport(input: {
  user: SessionUser | null | undefined;
  definition: unknown;
  from?: string | null;
  to?: string | null;
}): Promise<ReportPayload> {
  const authed = requireOrganization(input.user);
  if (!hasPermission(authed.role as MembershipRole | null, "reports:view")) {
    throw new ForbiddenError("Missing permission: reports:view");
  }

  const parsed = builderDefinitionSchema.parse(input.definition);
  ensureDatasetAccess(authed, parsed.datasetId);
  validateFieldRefs(parsed);

  const range = parseReportRange(input.from, input.to);
  const currencyCode = await organizationCurrency(authed.organizationId);
  const organizationId = authed.organizationId;

  const definitionStub = {
    key: `builder.${parsed.datasetId}`,
    title: `Custom · ${getBuilderDataset(parsed.datasetId)?.label}`,
    category: "company" as const,
    description: "Constrained report builder result (no arbitrary SQL).",
    permission: "reports:view" as const,
    chartType: parsed.chartType,
    exportable: true,
  };

  switch (parsed.datasetId) {
    case "leads": {
      const leads = await prisma.lead.findMany({
        where: {
          organizationId,
          deletedAt: null,
          createdAt: { gte: range.from, lte: range.to },
        },
        select: {
          id: true,
          country: true,
          estimatedValueMinor: true,
          currencyCode: true,
          source: { select: { name: true } },
          campaign: { select: { name: true } },
          assignedUser: { select: { name: true } },
        },
        take: 5000,
      });
      const groupField = parsed.groupBy[0] ?? "source";
      const map = new Map<string, { count: number; value: number }>();
      for (const lead of leads) {
        const label =
          groupField === "country"
            ? lead.country ?? "Unknown"
            : groupField === "campaign"
              ? lead.campaign?.name ?? "None"
              : groupField === "salesperson"
                ? lead.assignedUser?.name ?? "Unassigned"
                : lead.source?.name ?? "Unknown";
        const current = map.get(label) ?? { count: 0, value: 0 };
        current.count += 1;
        current.value += lead.estimatedValueMinor ?? 0;
        map.set(label, current);
      }
      const series = seriesFromMap(
        new Map(
          [...map.entries()].map(([label, stats]) => [
            label,
            parsed.measures.includes("estimatedValue") ? stats.value : stats.count,
          ]),
        ),
      );
      return buildPayload({
        definition: definitionStub,
        range,
        currencyCode,
        summary: accessibleSeriesSummary(definitionStub.title, series),
        metrics: [
          metric("Leads", leads.length, "number"),
          metric(
            "Estimated value",
            leads.reduce((sum, lead) => sum + (lead.estimatedValueMinor ?? 0), 0),
            "money",
          ),
        ],
        series,
        columns: [
          { key: "group", label: groupField },
          { key: "count", label: "Count", format: "number" },
          { key: "value", label: "Estimated value", format: "money" },
        ],
        rows: [...map.entries()].map(([label, stats]) => ({
          id: label,
          values: { group: label, count: stats.count, value: stats.value },
          href: "/crm/leads",
        })),
        drilldownHref: "/crm/leads",
      });
    }
    case "deals": {
      const deals = await prisma.deal.findMany({
        where: {
          organizationId,
          deletedAt: null,
          OR: [
            { closedAt: { gte: range.from, lte: range.to } },
            { closedAt: null, createdAt: { gte: range.from, lte: range.to } },
          ],
        },
        select: {
          id: true,
          name: true,
          valueMinor: true,
          currencyCode: true,
          stage: { select: { name: true } },
          ownerUserId: true,
        },
        take: 5000,
      });
      const owners = await prisma.user.findMany({
        where: {
          id: { in: deals.map((deal) => deal.ownerUserId).filter(Boolean) as string[] },
        },
        select: { id: true, name: true },
      });
      const ownerMap = new Map(owners.map((owner) => [owner.id, owner.name ?? owner.id]));
      const groupField = parsed.groupBy[0] ?? "stage";
      const map = new Map<string, { count: number; value: number }>();
      for (const deal of deals) {
        const label =
          groupField === "owner"
            ? (deal.ownerUserId ? ownerMap.get(deal.ownerUserId) : null) ?? "Unassigned"
            : deal.stage?.name ?? "No stage";
        const current = map.get(label) ?? { count: 0, value: 0 };
        current.count += 1;
        current.value += deal.valueMinor;
        map.set(label, current);
      }
      const series = seriesFromMap(
        new Map(
          [...map.entries()].map(([label, stats]) => [
            label,
            parsed.measures.includes("value") ? stats.value : stats.count,
          ]),
        ),
      );
      return buildPayload({
        definition: definitionStub,
        range,
        currencyCode,
        summary: accessibleSeriesSummary(definitionStub.title, series),
        metrics: [
          metric("Deals", deals.length, "number"),
          metric(
            "Deal value",
            deals.reduce((sum, deal) => sum + deal.valueMinor, 0),
            "money",
          ),
        ],
        series,
        columns: [
          { key: "group", label: groupField },
          { key: "count", label: "Count", format: "number" },
          { key: "value", label: "Value", format: "money" },
        ],
        rows: [...map.entries()].map(([label, stats]) => ({
          id: label,
          values: { group: label, count: stats.count, value: stats.value },
          href: "/crm/deals",
        })),
        drilldownHref: "/crm/deals",
      });
    }
    case "invoices": {
      const invoices = await prisma.invoice.findMany({
        where: {
          organizationId,
          deletedAt: null,
          issueDate: { gte: range.from, lte: range.to },
          status: { not: "DRAFT" },
        },
        select: {
          id: true,
          status: true,
          totalMinor: true,
          balanceMinor: true,
          currencyCode: true,
          company: { select: { name: true } },
        },
        take: 5000,
      });
      const groupField = parsed.groupBy[0] ?? "status";
      const map = new Map<string, { count: number; total: number; balance: number }>();
      for (const invoice of invoices) {
        const label =
          groupField === "client"
            ? invoice.company?.name ?? "Unknown"
            : invoice.status;
        const current = map.get(label) ?? { count: 0, total: 0, balance: 0 };
        current.count += 1;
        current.total += invoice.totalMinor;
        current.balance += invoice.balanceMinor;
        map.set(label, current);
      }
      const series = seriesFromMap(
        new Map(
          [...map.entries()].map(([label, stats]) => [
            label,
            parsed.measures.includes("balance")
              ? stats.balance
              : parsed.measures.includes("total")
                ? stats.total
                : stats.count,
          ]),
        ),
      );
      return buildPayload({
        definition: definitionStub,
        range,
        currencyCode,
        summary: accessibleSeriesSummary(definitionStub.title, series),
        metrics: [
          metric("Invoices", invoices.length, "number"),
          metric(
            "Invoiced total",
            invoices.reduce((sum, row) => sum + row.totalMinor, 0),
            "money",
          ),
          metric(
            "Outstanding",
            invoices.reduce((sum, row) => sum + row.balanceMinor, 0),
            "money",
          ),
        ],
        series,
        columns: [
          { key: "group", label: groupField },
          { key: "count", label: "Count", format: "number" },
          { key: "total", label: "Total", format: "money" },
          { key: "balance", label: "Balance", format: "money" },
        ],
        rows: [...map.entries()].map(([label, stats]) => ({
          id: label,
          values: {
            group: label,
            count: stats.count,
            total: stats.total,
            balance: stats.balance,
          },
          href: "/finance/invoices",
        })),
        drilldownHref: "/finance/invoices",
      });
    }
    case "payments": {
      const payments = await prisma.payment.findMany({
        where: {
          organizationId,
          deletedAt: null,
          receivedAt: { gte: range.from, lte: range.to },
        },
        select: { id: true, method: true, amountMinor: true, currencyCode: true },
        take: 5000,
      });
      const map = new Map<string, { count: number; amount: number }>();
      for (const payment of payments) {
        const label = payment.method ?? "Unknown";
        const current = map.get(label) ?? { count: 0, amount: 0 };
        current.count += 1;
        current.amount += payment.amountMinor;
        map.set(label, current);
      }
      const series = seriesFromMap(
        new Map(
          [...map.entries()].map(([label, stats]) => [
            label,
            parsed.measures.includes("amount") ? stats.amount : stats.count,
          ]),
        ),
      );
      return buildPayload({
        definition: definitionStub,
        range,
        currencyCode,
        summary: accessibleSeriesSummary(definitionStub.title, series),
        metrics: [
          metric("Payments", payments.length, "number"),
          metric(
            "Collected",
            payments.reduce((sum, row) => sum + row.amountMinor, 0),
            "money",
          ),
        ],
        series,
        columns: [
          { key: "group", label: "Method" },
          { key: "count", label: "Count", format: "number" },
          { key: "amount", label: "Amount", format: "money" },
        ],
        rows: [...map.entries()].map(([label, stats]) => ({
          id: label,
          values: { group: label, count: stats.count, amount: stats.amount },
          href: "/finance/payments",
        })),
        drilldownHref: "/finance/payments",
      });
    }
    case "projects": {
      const projects = await prisma.project.findMany({
        where: { organizationId, deletedAt: null },
        select: {
          id: true,
          name: true,
          status: true,
          budgetMinor: true,
          currencyCode: true,
        },
        take: 5000,
      });
      const groupField = parsed.groupBy[0] ?? "status";
      const map = new Map<string, { count: number; budget: number }>();
      for (const project of projects) {
        const label = groupField === "name" ? project.name : project.status;
        const current = map.get(label) ?? { count: 0, budget: 0 };
        current.count += 1;
        current.budget += project.budgetMinor ?? 0;
        map.set(label, current);
      }
      const series = seriesFromMap(
        new Map(
          [...map.entries()].map(([label, stats]) => [
            label,
            parsed.measures.includes("budget") ? stats.budget : stats.count,
          ]),
        ),
      );
      return buildPayload({
        definition: definitionStub,
        range,
        currencyCode,
        summary: accessibleSeriesSummary(definitionStub.title, series),
        metrics: [metric("Projects", projects.length, "number")],
        series,
        columns: [
          { key: "group", label: groupField },
          { key: "count", label: "Count", format: "number" },
          { key: "budget", label: "Budget", format: "money" },
        ],
        rows: [...map.entries()].map(([label, stats]) => ({
          id: label,
          values: { group: label, count: stats.count, budget: stats.budget },
          href: "/projects",
        })),
        drilldownHref: "/projects",
      });
    }
    case "attendance": {
      const rows = await prisma.attendanceRecord.findMany({
        where: {
          organizationId,
          date: { gte: range.from, lte: range.to },
        },
        select: { id: true, status: true },
        take: 10000,
      });
      const map = new Map<string, number>();
      for (const row of rows) {
        map.set(row.status, (map.get(row.status) ?? 0) + 1);
      }
      const series = seriesFromMap(map);
      return buildPayload({
        definition: definitionStub,
        range,
        currencyCode,
        summary: accessibleSeriesSummary(definitionStub.title, series),
        metrics: [metric("Records", rows.length, "number")],
        series,
        columns: [
          { key: "status", label: "Status" },
          { key: "count", label: "Count", format: "number" },
        ],
        rows: [...map.entries()].map(([status, count]) => ({
          id: status,
          values: { status, count },
          href: "/hr/attendance",
        })),
        drilldownHref: "/hr/attendance",
      });
    }
    case "xyme_goals": {
      const goals = await prisma.xYMEGoal.findMany({
        where: {
          organizationId,
          deletedAt: null,
          createdAt: { gte: range.from, lte: range.to },
        },
        select: {
          id: true,
          category: true,
          progressPct: true,
          plan: {
            select: {
              employee: {
                select: { department: { select: { name: true } } },
              },
            },
          },
        },
        take: 5000,
      });
      const groupField = parsed.groupBy[0] ?? "category";
      const map = new Map<string, { count: number; progress: number }>();
      for (const goal of goals) {
        const label =
          groupField === "department"
            ? goal.plan.employee.department?.name ?? "Unassigned"
            : goal.category;
        const current = map.get(label) ?? { count: 0, progress: 0 };
        current.count += 1;
        current.progress += goal.progressPct;
        map.set(label, current);
      }
      const series = seriesFromMap(
        new Map(
          [...map.entries()].map(([label, stats]) => [
            label,
            parsed.measures.includes("avgProgress")
              ? stats.count
                ? Math.round(stats.progress / stats.count)
                : 0
              : stats.count,
          ]),
        ),
      );
      return buildPayload({
        definition: definitionStub,
        range,
        currencyCode,
        summary: accessibleSeriesSummary(definitionStub.title, series),
        metrics: [metric("Goals", goals.length, "number")],
        series,
        columns: [
          { key: "group", label: groupField },
          { key: "count", label: "Count", format: "number" },
          { key: "avgProgress", label: "Avg progress", format: "percent" },
        ],
        rows: [...map.entries()].map(([label, stats]) => ({
          id: label,
          values: {
            group: label,
            count: stats.count,
            avgProgress: stats.count
              ? Math.round(stats.progress / stats.count)
              : 0,
          },
          href: "/xyme",
        })),
        drilldownHref: "/xyme",
      });
    }
    default:
      throw new ForbiddenError("Unsupported dataset");
  }
}
