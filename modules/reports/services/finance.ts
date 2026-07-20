import "server-only";

import { prisma } from "@/database";
import type { SessionUser } from "@/permissions";
import type {
  ReportDateRange,
  ReportDefinition,
  ReportPayload,
  ReportSeriesPoint,
  ReportTableColumn,
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

type FinanceReportInput = {
  key: string;
  definition: ReportDefinition;
  user: SessionUser & { organizationId: string };
  range: ReportDateRange;
};

type _MoneyRow = {
  amountMinor: number;
  currencyCode: string;
  asOf: Date | null;
};

const OPEN_INVOICE_STATUSES = ["SENT", "PARTIAL", "OVERDUE", "OPEN"];

function percent(numerator: number, denominator: number): number {
  return denominator > 0 ? Math.round((numerator / denominator) * 1000) / 10 : 0;
}

function average(total: number, count: number): number {
  return count > 0 ? Math.round(total / count) : 0;
}

async function addMoneyToMap(input: {
  organizationId: string;
  currencyCode: string;
  map: Map<string, number>;
  key: string;
  amountMinor: number;
  fromCurrency: string;
  asOf: Date | null;
}): Promise<void> {
  const converted = await convertMinorUnits({
    organizationId: input.organizationId,
    amountMinor: input.amountMinor,
    fromCurrency: input.fromCurrency,
    toCurrency: input.currencyCode,
    asOf: input.asOf ?? new Date(),
  });
  input.map.set(input.key, (input.map.get(input.key) ?? 0) + converted.amountMinor);
}

function moneySeriesFromMap(map: Map<string, number>): ReportSeriesPoint[] {
  return seriesFromMap(map).map((point) => ({
    ...point,
    value: Math.round(point.value / 100),
  }));
}

function invoiceColumns(): ReportTableColumn[] {
  return [
    { key: "invoiceNumber", label: "Invoice" },
    { key: "company", label: "Client" },
    { key: "status", label: "Status" },
    { key: "issueDate", label: "Issued" },
    { key: "dueDate", label: "Due" },
    { key: "totalMinor", label: "Total", format: "money" },
    { key: "balanceMinor", label: "Balance", format: "money" },
  ];
}

export async function runFinanceReport(input: FinanceReportInput): Promise<ReportPayload> {
  const currencyCode = await organizationCurrency(input.user.organizationId);

  switch (input.key) {
    case "finance.invoiced-revenue":
      return invoicedRevenue(input, currencyCode);
    case "finance.collected-revenue":
      return collectedRevenue(input, currencyCode);
    case "finance.outstanding-receivables":
      return outstandingReceivables(input, currencyCode);
    case "finance.aging-buckets":
      return agingBuckets(input, currencyCode);
    case "finance.overdue-invoices":
      return overdueInvoices(input, currencyCode);
    case "finance.payment-trend":
      return paymentTrend(input, currencyCode);
    case "finance.expenses-by-category":
      return expensesByCategory(input, currencyCode);
    case "finance.vendor-spend":
      return vendorSpend(input, currencyCode);
    case "finance.project-margin":
      return projectMargin(input, currencyCode);
    case "finance.client-profitability":
      return clientProfitability(input, currencyCode);
    case "finance.service-profitability":
      return serviceProfitability(input, currencyCode);
    default:
      return buildPayload({
        definition: input.definition,
        range: input.range,
        currencyCode,
        summary: `${input.definition.title}: no implementation for ${input.key}.`,
      });
  }
}

async function invoicedRevenue(
  input: FinanceReportInput,
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
      dueDate: true,
      status: true,
      totalMinor: true,
      balanceMinor: true,
      currencyCode: true,
      company: { select: { name: true } },
    },
    orderBy: { issueDate: "asc" },
  });

  const seriesMap = new Map<string, number>();
  const tableRows: ReportTableRow[] = [];

  for (const invoice of invoices) {
    const asOf = invoice.issueDate ?? input.range.to;
    const convertedTotal = await convertMinorUnits({
      organizationId: input.user.organizationId,
      amountMinor: invoice.totalMinor,
      fromCurrency: invoice.currencyCode,
      toCurrency: currencyCode,
      asOf,
    });
    const convertedBalance = await convertMinorUnits({
      organizationId: input.user.organizationId,
      amountMinor: invoice.balanceMinor,
      fromCurrency: invoice.currencyCode,
      toCurrency: currencyCode,
      asOf,
    });
    if (invoice.issueDate) {
      seriesMap.set(
        dayKey(invoice.issueDate),
        (seriesMap.get(dayKey(invoice.issueDate)) ?? 0) + convertedTotal.amountMinor,
      );
    }
    tableRows.push({
      id: invoice.id,
      href: `/finance/invoices/${invoice.id}`,
      values: {
        invoiceNumber: invoice.invoiceNumber ?? "Draft",
        company: invoice.company?.name ?? "Unassigned",
        status: invoice.status,
        issueDate: invoice.issueDate?.toISOString().slice(0, 10) ?? null,
        dueDate: invoice.dueDate?.toISOString().slice(0, 10) ?? null,
        totalMinor: convertedTotal.amountMinor,
        balanceMinor: convertedBalance.amountMinor,
      },
    });
  }

  const totalMinor = tableRows.reduce(
    (sum, row) => sum + Number(row.values.totalMinor ?? 0),
    0,
  );
  const series = moneySeriesFromMap(seriesMap);

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary:
      series.length > 0
        ? accessibleSeriesSummary("Invoiced revenue by issue date", series, "money")
        : "Invoiced revenue: no non-draft invoices issued in the selected range.",
    metrics: [
      metric("Invoiced revenue", totalMinor, "money"),
      metric("Invoice count", invoices.length, "number"),
      metric("Average invoice", average(totalMinor, invoices.length), "money"),
    ],
    series,
    columns: invoiceColumns(),
    rows: tableRows,
    drilldownHref: "/finance/invoices",
  });
}

async function collectedRevenue(
  input: FinanceReportInput,
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
      method: true,
      reference: true,
      receivedAt: true,
    },
    orderBy: { receivedAt: "asc" },
  });

  const seriesMap = new Map<string, number>();
  const rows: ReportTableRow[] = [];
  for (const payment of payments) {
    const converted = await convertMinorUnits({
      organizationId: input.user.organizationId,
      amountMinor: payment.amountMinor,
      fromCurrency: payment.currencyCode,
      toCurrency: currencyCode,
      asOf: payment.receivedAt,
    });
    seriesMap.set(
      dayKey(payment.receivedAt),
      (seriesMap.get(dayKey(payment.receivedAt)) ?? 0) + converted.amountMinor,
    );
    rows.push({
      id: payment.id,
      href: "/finance/payments",
      values: {
        paymentNumber: payment.paymentNumber ?? payment.reference ?? payment.id,
        method: payment.method ?? "Unspecified",
        receivedAt: payment.receivedAt.toISOString().slice(0, 10),
        amountMinor: converted.amountMinor,
      },
    });
  }

  const totalMinor = rows.reduce(
    (sum, row) => sum + Number(row.values.amountMinor ?? 0),
    0,
  );
  const series = moneySeriesFromMap(seriesMap);

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary:
      series.length > 0
        ? accessibleSeriesSummary("Collected revenue by received date", series, "money")
        : "Collected revenue: no payments received in the selected range.",
    metrics: [
      metric("Collected revenue", totalMinor, "money"),
      metric("Payment count", payments.length, "number"),
      metric("Average payment", average(totalMinor, payments.length), "money"),
    ],
    series,
    columns: [
      { key: "paymentNumber", label: "Payment" },
      { key: "method", label: "Method" },
      { key: "receivedAt", label: "Received" },
      { key: "amountMinor", label: "Amount", format: "money" },
    ],
    rows,
    drilldownHref: "/finance/payments",
  });
}

async function outstandingReceivables(
  input: FinanceReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
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
      issueDate: true,
      dueDate: true,
      status: true,
      totalMinor: true,
      balanceMinor: true,
      currencyCode: true,
      company: { select: { name: true } },
    },
    orderBy: { dueDate: "asc" },
  });

  const rows: ReportTableRow[] = [];
  for (const invoice of invoices) {
    const asOf = invoice.issueDate ?? input.range.to;
    const balance = await convertMinorUnits({
      organizationId: input.user.organizationId,
      amountMinor: invoice.balanceMinor,
      fromCurrency: invoice.currencyCode,
      toCurrency: currencyCode,
      asOf,
    });
    const total = await convertMinorUnits({
      organizationId: input.user.organizationId,
      amountMinor: invoice.totalMinor,
      fromCurrency: invoice.currencyCode,
      toCurrency: currencyCode,
      asOf,
    });
    rows.push({
      id: invoice.id,
      href: `/finance/invoices/${invoice.id}`,
      values: {
        invoiceNumber: invoice.invoiceNumber ?? invoice.id,
        company: invoice.company?.name ?? "Unassigned",
        status: invoice.status,
        issueDate: invoice.issueDate?.toISOString().slice(0, 10) ?? null,
        dueDate: invoice.dueDate?.toISOString().slice(0, 10) ?? null,
        totalMinor: total.amountMinor,
        balanceMinor: balance.amountMinor,
      },
    });
  }

  const totalBalance = rows.reduce(
    (sum, row) => sum + Number(row.values.balanceMinor ?? 0),
    0,
  );

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Outstanding receivables: ${Math.round(totalBalance / 100)} ${currencyCode} remains across ${rows.length} open invoices.`,
    metrics: [
      metric("Outstanding receivables", totalBalance, "money"),
      metric("Open invoices", rows.length, "number"),
    ],
    columns: invoiceColumns(),
    rows,
    drilldownHref: "/finance/invoices",
  });
}

async function agingBuckets(
  input: FinanceReportInput,
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
    const ageDays = Math.floor((today.getTime() - dueDate.getTime()) / 86400000);
    const label =
      ageDays <= 0 ? "Current" : ageDays <= 30 ? "1-30 days overdue" : "31+ days overdue";
    await addMoneyToMap({
      organizationId: input.user.organizationId,
      currencyCode,
      map: buckets,
      key: label,
      amountMinor: invoice.balanceMinor,
      fromCurrency: invoice.currencyCode,
      asOf: invoice.issueDate ?? dueDate,
    });
  }

  const rows = [...buckets.entries()].map(([label, amountMinor]) => ({
    id: label,
    values: {
      bucket: label,
      amountMinor,
      invoiceCount: invoices.filter((invoice) => {
        const dueDate = invoice.dueDate ?? today;
        const ageDays = Math.floor((today.getTime() - dueDate.getTime()) / 86400000);
        return (
          (label === "Current" && ageDays <= 0) ||
          (label === "1-30 days overdue" && ageDays > 0 && ageDays <= 30) ||
          (label === "31+ days overdue" && ageDays > 30)
        );
      }).length,
    },
    href: "/finance/invoices",
  }));
  const totalMinor = rows.reduce(
    (sum, row) => sum + Number(row.values.amountMinor ?? 0),
    0,
  );

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: accessibleSeriesSummary(
      "Receivable aging",
      moneySeriesFromMap(buckets),
      "money",
    ),
    metrics: [
      metric("Total receivables", totalMinor, "money"),
      metric("Open invoice count", invoices.length, "number"),
    ],
    series: moneySeriesFromMap(buckets),
    columns: [
      { key: "bucket", label: "Bucket" },
      { key: "invoiceCount", label: "Invoices", format: "number" },
      { key: "amountMinor", label: "Amount", format: "money" },
    ],
    rows,
    drilldownHref: "/finance/invoices",
  });
}

async function overdueInvoices(
  input: FinanceReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const today = new Date();
  today.setUTCHours(0, 0, 0, 0);
  const invoices = await prisma.invoice.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      balanceMinor: { gt: 0 },
      dueDate: { lt: today },
      status: { in: OPEN_INVOICE_STATUSES },
    },
    select: {
      id: true,
      invoiceNumber: true,
      issueDate: true,
      dueDate: true,
      status: true,
      totalMinor: true,
      balanceMinor: true,
      currencyCode: true,
      company: { select: { name: true } },
    },
    orderBy: { dueDate: "asc" },
  });

  const rows: ReportTableRow[] = [];
  for (const invoice of invoices) {
    const asOf = invoice.issueDate ?? invoice.dueDate ?? today;
    const balance = await convertMinorUnits({
      organizationId: input.user.organizationId,
      amountMinor: invoice.balanceMinor,
      fromCurrency: invoice.currencyCode,
      toCurrency: currencyCode,
      asOf,
    });
    const total = await convertMinorUnits({
      organizationId: input.user.organizationId,
      amountMinor: invoice.totalMinor,
      fromCurrency: invoice.currencyCode,
      toCurrency: currencyCode,
      asOf,
    });
    rows.push({
      id: invoice.id,
      href: `/finance/invoices/${invoice.id}`,
      values: {
        invoiceNumber: invoice.invoiceNumber ?? invoice.id,
        company: invoice.company?.name ?? "Unassigned",
        status: invoice.status,
        issueDate: invoice.issueDate?.toISOString().slice(0, 10) ?? null,
        dueDate: invoice.dueDate?.toISOString().slice(0, 10) ?? null,
        totalMinor: total.amountMinor,
        balanceMinor: balance.amountMinor,
      },
    });
  }

  const totalBalance = rows.reduce(
    (sum, row) => sum + Number(row.values.balanceMinor ?? 0),
    0,
  );

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Overdue invoices: ${rows.length} invoices total ${Math.round(totalBalance / 100)} ${currencyCode} overdue.`,
    metrics: [
      metric("Overdue balance", totalBalance, "money"),
      metric("Overdue invoice count", rows.length, "number"),
    ],
    columns: invoiceColumns(),
    rows,
    drilldownHref: "/finance/invoices",
  });
}

async function paymentTrend(
  input: FinanceReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  return collectedRevenue(input, currencyCode);
}

async function expensesByCategory(
  input: FinanceReportInput,
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
      category: { select: { id: true, name: true } },
    },
  });

  const categoryTotals = new Map<string, number>();
  const categoryIds = new Map<string, string>();
  for (const expense of expenses) {
    const label = expense.category?.name ?? "Uncategorized";
    categoryIds.set(label, expense.category?.id ?? "uncategorized");
    await addMoneyToMap({
      organizationId: input.user.organizationId,
      currencyCode,
      map: categoryTotals,
      key: label,
      amountMinor: expense.amountMinor,
      fromCurrency: expense.currencyCode,
      asOf: expense.spentAt ?? expense.createdAt,
    });
  }

  const rows = [...categoryTotals.entries()]
    .sort(([, a], [, b]) => b - a)
    .map(([label, amountMinor]) => ({
      id: categoryIds.get(label) ?? label,
      href: "/finance/expenses",
      values: {
        category: label,
        amountMinor,
        expenseCount: expenses.filter(
          (expense) => (expense.category?.name ?? "Uncategorized") === label,
        ).length,
      },
    }));

  const totalMinor = rows.reduce(
    (sum, row) => sum + Number(row.values.amountMinor ?? 0),
    0,
  );

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Expenses by category: ${Math.round(totalMinor / 100)} ${currencyCode} across ${rows.length} categories.`,
    metrics: [
      metric("Expense total", totalMinor, "money"),
      metric("Expense count", expenses.length, "number"),
    ],
    series: moneySeriesFromMap(categoryTotals),
    columns: [
      { key: "category", label: "Category" },
      { key: "expenseCount", label: "Expenses", format: "number" },
      { key: "amountMinor", label: "Amount", format: "money" },
    ],
    rows,
    drilldownHref: "/finance/expenses",
  });
}

async function vendorSpend(
  input: FinanceReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const bills = await prisma.vendorBill.findMany({
    where: {
      organizationId: input.user.organizationId,
      deletedAt: null,
      createdAt: { gte: input.range.from, lte: input.range.to },
    },
    select: {
      id: true,
      amountMinor: true,
      currencyCode: true,
      createdAt: true,
      vendor: { select: { id: true, name: true } },
    },
  });

  const vendorTotals = new Map<string, number>();
  const vendorIds = new Map<string, string>();
  for (const bill of bills) {
    vendorIds.set(bill.vendor.name, bill.vendor.id);
    await addMoneyToMap({
      organizationId: input.user.organizationId,
      currencyCode,
      map: vendorTotals,
      key: bill.vendor.name,
      amountMinor: bill.amountMinor,
      fromCurrency: bill.currencyCode,
      asOf: bill.createdAt,
    });
  }

  const rows = [...vendorTotals.entries()]
    .sort(([, a], [, b]) => b - a)
    .map(([vendor, amountMinor]) => ({
      id: vendorIds.get(vendor) ?? vendor,
      href: "/finance/vendors",
      values: {
        vendor,
        billCount: bills.filter((bill) => bill.vendor.name === vendor).length,
        amountMinor,
      },
    }));
  const totalMinor = rows.reduce(
    (sum, row) => sum + Number(row.values.amountMinor ?? 0),
    0,
  );

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Vendor spend: ${Math.round(totalMinor / 100)} ${currencyCode} across ${rows.length} vendors.`,
    metrics: [
      metric("Vendor spend", totalMinor, "money"),
      metric("Vendor bill count", bills.length, "number"),
    ],
    series: moneySeriesFromMap(vendorTotals),
    columns: [
      { key: "vendor", label: "Vendor" },
      { key: "billCount", label: "Bills", format: "number" },
      { key: "amountMinor", label: "Amount", format: "money" },
    ],
    rows,
    drilldownHref: "/finance/vendors",
  });
}

async function latestProjectSnapshots(
  organizationId: string,
  range: ReportDateRange,
) {
  const snapshots = await prisma.projectProfitabilitySnapshot.findMany({
    where: {
      organizationId,
      asOfDate: { lte: range.to },
    },
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
          clientAccount: {
            select: {
              company: { select: { id: true, name: true } },
            },
          },
          services: { select: { name: true } },
        },
      },
    },
    orderBy: [{ projectId: "asc" }, { asOfDate: "desc" }],
  });

  const latest = new Map<string, (typeof snapshots)[number]>();
  for (const snapshot of snapshots) {
    if (!latest.has(snapshot.projectId)) {
      latest.set(snapshot.projectId, snapshot);
    }
  }
  return [...latest.values()];
}

async function projectMargin(
  input: FinanceReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const snapshots = await latestProjectSnapshots(input.user.organizationId, input.range);
  const rows: ReportTableRow[] = [];
  for (const snapshot of snapshots) {
    const revenue = await convertMinorUnits({
      organizationId: input.user.organizationId,
      amountMinor: snapshot.revenueMinor,
      fromCurrency: snapshot.currencyCode,
      toCurrency: currencyCode,
      asOf: snapshot.asOfDate,
    });
    const cost = await convertMinorUnits({
      organizationId: input.user.organizationId,
      amountMinor: snapshot.costMinor,
      fromCurrency: snapshot.currencyCode,
      toCurrency: currencyCode,
      asOf: snapshot.asOfDate,
    });
    const profit = revenue.amountMinor - cost.amountMinor;
    rows.push({
      id: snapshot.id,
      href: `/projects/${snapshot.projectId}`,
      values: {
        project: snapshot.project.name,
        asOfDate: snapshot.asOfDate.toISOString().slice(0, 10),
        revenueMinor: revenue.amountMinor,
        costMinor: cost.amountMinor,
        profitMinor: profit,
        marginPct: percent(profit, revenue.amountMinor),
      },
    });
  }

  const revenueMinor = rows.reduce(
    (sum, row) => sum + Number(row.values.revenueMinor ?? 0),
    0,
  );
  const profitMinor = rows.reduce(
    (sum, row) => sum + Number(row.values.profitMinor ?? 0),
    0,
  );

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Project margin: ${percent(profitMinor, revenueMinor)}% margin on ${Math.round(revenueMinor / 100)} ${currencyCode} revenue.`,
    metrics: [
      metric("Revenue", revenueMinor, "money"),
      metric("Profit", profitMinor, "money"),
      metric("Margin", percent(profitMinor, revenueMinor), "percent"),
    ],
    columns: [
      { key: "project", label: "Project" },
      { key: "asOfDate", label: "As of" },
      { key: "revenueMinor", label: "Revenue", format: "money" },
      { key: "costMinor", label: "Cost", format: "money", restricted: true },
      { key: "profitMinor", label: "Profit", format: "money", restricted: true },
      { key: "marginPct", label: "Margin", format: "percent", restricted: true },
    ],
    rows,
    drilldownHref: "/projects",
  });
}

async function clientProfitability(
  input: FinanceReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const snapshots = await latestProjectSnapshots(input.user.organizationId, input.range);
  const totals = new Map<
    string,
    { id: string; revenueMinor: number; costMinor: number; profitMinor: number; projects: number }
  >();

  for (const snapshot of snapshots) {
    const company = snapshot.project.clientAccount?.company;
    const label = company?.name ?? "Unassigned";
    const current = totals.get(label) ?? {
      id: company?.id ?? "unassigned",
      revenueMinor: 0,
      costMinor: 0,
      profitMinor: 0,
      projects: 0,
    };
    const revenue = await convertMinorUnits({
      organizationId: input.user.organizationId,
      amountMinor: snapshot.revenueMinor,
      fromCurrency: snapshot.currencyCode,
      toCurrency: currencyCode,
      asOf: snapshot.asOfDate,
    });
    const cost = await convertMinorUnits({
      organizationId: input.user.organizationId,
      amountMinor: snapshot.costMinor,
      fromCurrency: snapshot.currencyCode,
      toCurrency: currencyCode,
      asOf: snapshot.asOfDate,
    });
    current.revenueMinor += revenue.amountMinor;
    current.costMinor += cost.amountMinor;
    current.profitMinor += revenue.amountMinor - cost.amountMinor;
    current.projects += 1;
    totals.set(label, current);
  }

  const rows = [...totals.entries()]
    .sort(([, a], [, b]) => b.profitMinor - a.profitMinor)
    .map(([client, values]) => ({
      id: values.id,
      href: "/crm/clients",
      values: {
        client,
        projectCount: values.projects,
        revenueMinor: values.revenueMinor,
        costMinor: values.costMinor,
        profitMinor: values.profitMinor,
        marginPct: percent(values.profitMinor, values.revenueMinor),
      },
    }));
  const revenueMinor = rows.reduce(
    (sum, row) => sum + Number(row.values.revenueMinor ?? 0),
    0,
  );
  const profitMinor = rows.reduce(
    (sum, row) => sum + Number(row.values.profitMinor ?? 0),
    0,
  );

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Client profitability: ${percent(profitMinor, revenueMinor)}% margin across ${rows.length} clients.`,
    metrics: [
      metric("Client revenue", revenueMinor, "money"),
      metric("Client profit", profitMinor, "money"),
      metric("Client margin", percent(profitMinor, revenueMinor), "percent"),
    ],
    columns: [
      { key: "client", label: "Client" },
      { key: "projectCount", label: "Projects", format: "number" },
      { key: "revenueMinor", label: "Revenue", format: "money" },
      { key: "costMinor", label: "Cost", format: "money", restricted: true },
      { key: "profitMinor", label: "Profit", format: "money", restricted: true },
      { key: "marginPct", label: "Margin", format: "percent", restricted: true },
    ],
    rows,
    drilldownHref: "/crm/clients",
  });
}

async function serviceProfitability(
  input: FinanceReportInput,
  currencyCode: string,
): Promise<ReportPayload> {
  const snapshots = await latestProjectSnapshots(input.user.organizationId, input.range);
  const totals = new Map<
    string,
    { revenueMinor: number; costMinor: number; profitMinor: number; projects: number }
  >();

  for (const snapshot of snapshots) {
    const serviceNames =
      snapshot.project.services.length > 0
        ? snapshot.project.services.map((service) => service.name)
        : ["Unassigned"];
    const currency = assertSingleCurrency([snapshot.currencyCode], "Service profitability");
    const revenue = await convertMinorUnits({
      organizationId: input.user.organizationId,
      amountMinor: snapshot.revenueMinor,
      fromCurrency: currency,
      toCurrency: currencyCode,
      asOf: snapshot.asOfDate,
    });
    const cost = await convertMinorUnits({
      organizationId: input.user.organizationId,
      amountMinor: snapshot.costMinor,
      fromCurrency: currency,
      toCurrency: currencyCode,
      asOf: snapshot.asOfDate,
    });
    const serviceCount = serviceNames.length;
    for (const service of serviceNames) {
      const current = totals.get(service) ?? {
        revenueMinor: 0,
        costMinor: 0,
        profitMinor: 0,
        projects: 0,
      };
      current.revenueMinor += Math.round(revenue.amountMinor / serviceCount);
      current.costMinor += Math.round(cost.amountMinor / serviceCount);
      current.profitMinor += Math.round((revenue.amountMinor - cost.amountMinor) / serviceCount);
      current.projects += 1;
      totals.set(service, current);
    }
  }

  const rows = [...totals.entries()]
    .sort(([, a], [, b]) => b.profitMinor - a.profitMinor)
    .map(([service, values]) => ({
      id: service,
      href: "/projects",
      values: {
        service,
        projectCount: values.projects,
        revenueMinor: values.revenueMinor,
        costMinor: values.costMinor,
        profitMinor: values.profitMinor,
        marginPct: percent(values.profitMinor, values.revenueMinor),
      },
    }));
  const revenueMinor = rows.reduce(
    (sum, row) => sum + Number(row.values.revenueMinor ?? 0),
    0,
  );
  const profitMinor = rows.reduce(
    (sum, row) => sum + Number(row.values.profitMinor ?? 0),
    0,
  );

  return buildPayload({
    definition: input.definition,
    range: input.range,
    currencyCode,
    summary: `Service profitability: ${percent(profitMinor, revenueMinor)}% margin across ${rows.length} service groups.`,
    metrics: [
      metric("Service revenue", revenueMinor, "money"),
      metric("Service profit", profitMinor, "money"),
      metric("Service margin", percent(profitMinor, revenueMinor), "percent"),
    ],
    columns: [
      { key: "service", label: "Service" },
      { key: "projectCount", label: "Projects", format: "number" },
      { key: "revenueMinor", label: "Revenue", format: "money" },
      { key: "costMinor", label: "Cost", format: "money", restricted: true },
      { key: "profitMinor", label: "Profit", format: "money", restricted: true },
      { key: "marginPct", label: "Margin", format: "percent", restricted: true },
    ],
    rows,
    drilldownHref: "/projects",
  });
}

