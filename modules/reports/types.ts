import type { Permission } from "@/permissions/types";
import type { RevenueDefinition } from "@/modules/reports/revenue";

export type ReportCategory =
  | "company"
  | "crm"
  | "sales"
  | "xyme"
  | "hr"
  | "delivery"
  | "finance";

export type ReportMeasureFormat = "money" | "number" | "percent" | "days";

export type ReportChartType = "bar" | "line" | "table" | "stacked";

export type ReportDateRange = {
  from: Date;
  to: Date;
  label: string;
};

export type ReportSeriesPoint = {
  label: string;
  value: number;
  href?: string;
};

export type ReportTableColumn = {
  key: string;
  label: string;
  format?: ReportMeasureFormat;
  restricted?: boolean;
};

export type ReportTableRow = {
  id: string;
  values: Record<string, string | number | null>;
  href?: string;
};

export type ReportPayload = {
  key: string;
  title: string;
  category: ReportCategory;
  description: string;
  range: ReportDateRange;
  currencyCode: string;
  revenueDefinition?: RevenueDefinition;
  refreshedAt: string;
  summary: string;
  metrics: Array<{
    label: string;
    value: number;
    format: ReportMeasureFormat;
    hint?: string;
  }>;
  series: ReportSeriesPoint[];
  table: {
    columns: ReportTableColumn[];
    rows: ReportTableRow[];
  };
  drilldownHref?: string;
};

export type ReportDefinition = {
  key: string;
  title: string;
  category: ReportCategory;
  description: string;
  permission: Permission;
  /** Extra permission gates (all required) */
  extraPermissions?: Permission[];
  revenueDefinition?: RevenueDefinition;
  chartType: ReportChartType;
  exportable: boolean;
  /** Fields stripped from exports for non-privileged roles */
  restrictedExportFields?: string[];
};

export type SalesPerformanceVisibility = {
  showPeerLeaderboard: boolean;
  showCostVersusRevenue: boolean;
  salesSelfOnly: boolean;
};
