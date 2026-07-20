import type { MembershipRole } from "@prisma/client";

import type { Permission } from "@/permissions/types";
import { hasPermission } from "@/permissions/types";
import type { SessionUser } from "@/permissions/types";

export type ExportType =
  | "tables"
  | "reports"
  | "employees"
  | "crm"
  | "projects"
  | "invoices"
  | "finance"
  | "xyme";

export type ExportDefinition = {
  key: ExportType;
  label: string;
  description: string;
  permission: Permission;
  /** Extra permission required for sensitive fields */
  sensitivePermission?: Permission;
  /** Requires an approval step before generation */
  requiresApproval?: boolean;
  defaultColumns: { key: string; label: string; sensitive?: boolean }[];
  defaultExpiryHours: number;
};

export const EXPORT_CATALOG: ExportDefinition[] = [
  {
    key: "tables",
    label: "Tables",
    description: "Generic tabular dataset export.",
    permission: "reports:export",
    defaultColumns: [
      { key: "id", label: "ID" },
      { key: "name", label: "Name" },
      { key: "createdAt", label: "Created at" },
    ],
    defaultExpiryHours: 24,
  },
  {
    key: "reports",
    label: "Reports",
    description: "Saved or catalog report exports.",
    permission: "reports:export",
    defaultColumns: [
      { key: "reportKey", label: "Report" },
      { key: "metric", label: "Metric" },
      { key: "value", label: "Value" },
    ],
    defaultExpiryHours: 24,
  },
  {
    key: "employees",
    label: "Employee data",
    description: "Employee directory export.",
    permission: "employees:view",
    sensitivePermission: "employees:view_compensation",
    requiresApproval: true,
    defaultColumns: [
      { key: "employeeCode", label: "Employee code" },
      { key: "name", label: "Name" },
      { key: "email", label: "Email" },
      { key: "department", label: "Department" },
      { key: "compensation", label: "Compensation", sensitive: true },
    ],
    defaultExpiryHours: 12,
  },
  {
    key: "crm",
    label: "CRM data",
    description: "Leads, contacts, clients, and deals.",
    permission: "crm:view",
    defaultColumns: [
      { key: "type", label: "Type" },
      { key: "name", label: "Name" },
      { key: "email", label: "Email" },
      { key: "owner", label: "Owner" },
      { key: "status", label: "Status" },
    ],
    defaultExpiryHours: 24,
  },
  {
    key: "projects",
    label: "Project data",
    description: "Projects, tasks, and delivery status.",
    permission: "projects:view",
    defaultColumns: [
      { key: "code", label: "Code" },
      { key: "name", label: "Name" },
      { key: "client", label: "Client" },
      { key: "status", label: "Status" },
      { key: "owner", label: "Owner" },
    ],
    defaultExpiryHours: 24,
  },
  {
    key: "invoices",
    label: "Invoice data",
    description: "Invoice register export.",
    permission: "finance:view",
    defaultColumns: [
      { key: "invoiceNumber", label: "Invoice #" },
      { key: "client", label: "Client" },
      { key: "amount", label: "Amount" },
      { key: "status", label: "Status" },
      { key: "issueDate", label: "Issue date" },
    ],
    defaultExpiryHours: 24,
  },
  {
    key: "finance",
    label: "Finance reports",
    description: "Finance and profitability exports.",
    permission: "finance:view",
    sensitivePermission: "finance:view_profitability",
    requiresApproval: true,
    defaultColumns: [
      { key: "period", label: "Period" },
      { key: "revenue", label: "Revenue" },
      { key: "expenses", label: "Expenses" },
      { key: "margin", label: "Margin", sensitive: true },
    ],
    defaultExpiryHours: 12,
  },
  {
    key: "xyme",
    label: "XYME reports",
    description: "XYME goals and progress exports.",
    permission: "xyme:view",
    defaultColumns: [
      { key: "cycle", label: "Cycle" },
      { key: "goal", label: "Goal" },
      { key: "owner", label: "Owner" },
      { key: "progress", label: "Progress" },
    ],
    defaultExpiryHours: 24,
  },
];

export function getExportDefinition(key: string): ExportDefinition | undefined {
  return EXPORT_CATALOG.find((item) => item.key === key);
}

export function canRequestExport(
  user: SessionUser,
  exportType: string,
): boolean {
  const definition = getExportDefinition(exportType);
  if (!definition) return false;
  const role = user.role as MembershipRole | null;

  if (definition.key === "tables" || definition.key === "reports") {
    return hasPermission(role, "reports:export");
  }

  return hasPermission(role, definition.permission);
}

export function filterExportColumns(
  user: SessionUser,
  exportType: string,
  requestedColumns: string[],
): string[] {
  const definition = getExportDefinition(exportType);
  if (!definition) return [];

  const role = user.role as MembershipRole | null;
  const canSeeSensitive =
    !definition.sensitivePermission ||
    hasPermission(role, definition.sensitivePermission);

  const allowed = new Set(
    definition.defaultColumns
      .filter((col) => canSeeSensitive || !col.sensitive)
      .map((col) => col.key),
  );

  const selected =
    requestedColumns.length > 0
      ? requestedColumns.filter((key) => allowed.has(key))
      : [...allowed];

  return selected;
}

export function exportRequiresApproval(
  user: SessionUser,
  exportType: string,
): boolean {
  const definition = getExportDefinition(exportType);
  if (!definition?.requiresApproval) return false;
  const role = user.role as MembershipRole | null;
  // Admins can self-approve by skipping the gate
  if (role === "SUPER_ADMIN" || role === "ADMIN") return false;
  return true;
}

export function isExportDownloadExpired(expiresAt: Date | null | undefined, now = new Date()): boolean {
  if (!expiresAt) return false;
  return expiresAt.getTime() < now.getTime();
}

export function buildExportCsv(
  columns: string[],
  rows: Record<string, unknown>[],
): string {
  const header = columns.join(",");
  const lines = rows.map((row) =>
    columns
      .map((col) => {
        const value = row[col];
        const text = value == null ? "" : String(value);
        return text.includes(",") || text.includes('"') || text.includes("\n")
          ? `"${text.replace(/"/g, '""')}"`
          : text;
      })
      .join(","),
  );
  return `${[header, ...lines].join("\n")}\n`;
}

export function canAccessExports(user: SessionUser): boolean {
  return EXPORT_CATALOG.some((item) => canRequestExport(user, item.key));
}

export function computeExpiryDate(
  exportType: string,
  from = new Date(),
): Date {
  const definition = getExportDefinition(exportType);
  const hours = definition?.defaultExpiryHours ?? 24;
  return new Date(from.getTime() + hours * 60 * 60 * 1000);
}
