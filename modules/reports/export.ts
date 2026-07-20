import type { SessionUser } from "@/permissions/types";
import type { ReportDefinition, ReportPayload } from "@/modules/reports/types";
import {
  canExportReport,
  stripRestrictedExportFields,
} from "@/modules/reports/export-policy";
import { formatMoney, formatPercent } from "@/lib/utils";

export type ExportFormat = "csv" | "spreadsheet" | "pdf";

class ExportForbiddenError extends Error {
  constructor(message = "Forbidden") {
    super(message);
    this.name = "ExportForbiddenError";
  }
}

function formatCell(
  value: string | number | null,
  format: "money" | "number" | "percent" | "days" | undefined,
  currencyCode: string,
): string {
  if (value === null || value === undefined) return "";
  if (typeof value === "string") return value;
  switch (format) {
    case "money":
      return formatMoney(value, currencyCode, "en-IN");
    case "percent":
      return formatPercent(value);
    case "days":
      return `${value}`;
    default:
      return String(value);
  }
}

export function buildExportRows(
  payload: ReportPayload,
  definition: ReportDefinition,
  user: SessionUser,
): { headers: string[]; rows: string[][] } {
  if (!canExportReport(user, definition)) {
    throw new ExportForbiddenError("Missing permission: reports:export");
  }

  const columns = payload.table.columns.filter((column) => {
    if (!column.restricted) return true;
    const sample = { [column.key]: 1 };
    const stripped = stripRestrictedExportFields(sample, definition, user);
    return column.key in stripped;
  });

  const headers = columns.map((column) => column.label);
  const rows = payload.table.rows.map((row) => {
    const safeValues = stripRestrictedExportFields(
      { ...row.values },
      definition,
      user,
    );
    return columns.map((column) =>
      formatCell(
        (safeValues[column.key] as string | number | null) ?? null,
        column.format,
        payload.currencyCode,
      ),
    );
  });

  // Always include metadata preamble as comment-style first conceptual block
  // via headers; callers can prepend summary lines.
  return { headers, rows };
}

export function toCsv(headers: string[], rows: string[][]): string {
  const escape = (value: string) => {
    if (/[",\n]/.test(value)) {
      return `"${value.replaceAll('"', '""')}"`;
    }
    return value;
  };
  return [headers, ...rows].map((line) => line.map(escape).join(",")).join("\n");
}

/** Spreadsheet-ready TSV (opens cleanly in Excel / Sheets). */
export function toSpreadsheetTsv(headers: string[], rows: string[][]): string {
  const escape = (value: string) => value.replaceAll("\t", " ").replaceAll("\n", " ");
  return [headers, ...rows].map((line) => line.map(escape).join("\t")).join("\n");
}

export function toPrintableHtml(payload: ReportPayload): string {
  const metrics = payload.metrics
    .map(
      (item) =>
        `<li><strong>${item.label}:</strong> ${item.value}${item.format === "percent" ? "%" : ""}</li>`,
    )
    .join("");
  const series = payload.series
    .map((point) => `<li>${point.label}: ${point.value}</li>`)
    .join("");
  const head = payload.table.columns.map((c) => `<th>${c.label}</th>`).join("");
  const body = payload.table.rows
    .map(
      (row) =>
        `<tr>${payload.table.columns
          .map((c) => `<td>${row.values[c.key] ?? ""}</td>`)
          .join("")}</tr>`,
    )
    .join("");

  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>${payload.title}</title>
  <style>
    body { font-family: Georgia, serif; color: #111; margin: 2rem; }
    h1 { font-size: 1.6rem; margin-bottom: 0.25rem; }
    .meta { color: #444; margin-bottom: 1.5rem; }
    table { border-collapse: collapse; width: 100%; margin-top: 1rem; }
    th, td { border: 1px solid #ccc; padding: 0.4rem 0.6rem; text-align: left; }
    th { background: #f4f4f4; }
    @media print { button { display: none; } }
  </style>
</head>
<body>
  <button onclick="window.print()">Print / Save as PDF</button>
  <h1>${payload.title}</h1>
  <p class="meta">
    Range: ${payload.range.label}<br/>
    Currency: ${payload.currencyCode}<br/>
    Revenue definition: ${payload.revenueDefinition ?? "n/a"}<br/>
    Last refresh: ${payload.refreshedAt}
  </p>
  <p>${payload.summary}</p>
  <h2>Metrics</h2>
  <ul>${metrics || "<li>None</li>"}</ul>
  <h2>Series</h2>
  <ul>${series || "<li>None</li>"}</ul>
  <h2>Detail</h2>
  <table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>
</body>
</html>`;
}
