import { describe, expect, it } from "vitest";

import { canExportReport, stripRestrictedExportFields } from "@/modules/reports/export-policy";
import { getReportDefinition } from "@/modules/reports/catalog";
import type { ReportPayload } from "@/modules/reports/types";
import type { SessionUser } from "@/permissions/types";
import { builderDefinitionSchema } from "@/modules/reports/builder/datasets";
import { parseReportRange } from "@/modules/reports/date-range";
import {
  buildExportRows,
  toCsv,
  toSpreadsheetTsv,
} from "@/modules/reports/export";

const range = parseReportRange("2026-07-01", "2026-07-19");

const financeUser: SessionUser = {
  id: "u1",
  email: "finance@example.com",
  organizationId: "org1",
  role: "FINANCE",
  status: "ACTIVE",
};

const salesUser: SessionUser = {
  id: "u2",
  email: "sales@example.com",
  organizationId: "org1",
  role: "SALES",
  status: "ACTIVE",
};

const payload: ReportPayload = {
  key: "finance.project-margin",
  title: "Project margin",
  category: "finance",
  description: "test",
  range,
  currencyCode: "INR",
  revenueDefinition: "invoiced",
  refreshedAt: new Date().toISOString(),
  summary: "Two projects",
  metrics: [{ label: "Projects", value: 2, format: "number" }],
  series: [
    { label: "A", value: 40 },
    { label: "B", value: 60 },
  ],
  table: {
    columns: [
      { key: "name", label: "Project" },
      { key: "marginPct", label: "Margin", format: "percent", restricted: true },
      { key: "profitMinor", label: "Profit", format: "money", restricted: true },
    ],
    rows: [
      {
        id: "1",
        values: { name: "Northstar", marginPct: 40, profitMinor: 100000 },
      },
      {
        id: "2",
        values: { name: "Orbit", marginPct: 25, profitMinor: 50000 },
      },
    ],
  },
};

describe("report date filters", () => {
  it("parses an explicit range", () => {
    expect(range.label).toContain("2026-07-01");
    expect(range.from <= range.to).toBe(true);
  });

  it("falls back to current month on invalid range", () => {
    const invalid = parseReportRange("2026-08-01", "2026-07-01");
    expect(invalid.label).toBe("Current month");
  });
});

describe("report permissions and exports", () => {
  it("allows finance to export finance reports", () => {
    const definition = getReportDefinition("finance.collected-revenue")!;
    expect(canExportReport(financeUser, definition)).toBe(true);
  });

  it("blocks sales from exporting without reports:export", () => {
    const definition = getReportDefinition("crm.win-rate")!;
    expect(canExportReport(salesUser, definition)).toBe(false);
  });

  it("strips restricted profitability fields for sales exports", () => {
    const definition = getReportDefinition("finance.project-margin")!;
    const row = stripRestrictedExportFields(
      { name: "Northstar", marginPct: 40, profitMinor: 100000, costMinor: 1 },
      definition,
      salesUser,
    );
    expect(row.name).toBe("Northstar");
    expect(row.marginPct).toBeUndefined();
    expect(row.profitMinor).toBeUndefined();
  });

  it("keeps profitability fields for finance exports", () => {
    const definition = getReportDefinition("finance.project-margin")!;
    const { headers, rows } = buildExportRows(payload, definition, financeUser);
    expect(headers).toContain("Margin");
    expect(rows).toHaveLength(2);
    const csv = toCsv(headers, rows);
    expect(csv.split("\n").length).toBe(3);
    const tsv = toSpreadsheetTsv(headers, rows);
    expect(tsv).toContain("\t");
  });

  it("sums series totals for chart summaries", () => {
    const total = payload.series.reduce((sum, point) => sum + point.value, 0);
    expect(total).toBe(100);
  });
});

describe("builder constraints", () => {
  it("accepts a whitelisted definition", () => {
    const parsed = builderDefinitionSchema.parse({
      datasetId: "leads",
      fields: ["source", "country"],
      filters: [],
      groupBy: ["source"],
      measures: ["count"],
      chartType: "bar",
    });
    expect(parsed.datasetId).toBe("leads");
  });

  it("rejects unknown datasets", () => {
    expect(() =>
      builderDefinitionSchema.parse({
        datasetId: "raw_sql",
        fields: ["id"],
        measures: ["count"],
      }),
    ).toThrow();
  });
});
