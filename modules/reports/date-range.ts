import { parseDashboardRange, toDateInputValue } from "@/modules/dashboard/date-range";
import type { ReportDateRange } from "@/modules/reports/types";

export { toDateInputValue };

export function parseReportRange(
  fromParam?: string | null,
  toParam?: string | null,
): ReportDateRange {
  const range = parseDashboardRange(fromParam, toParam);
  return {
    from: range.from,
    to: range.to,
    label: range.label,
  };
}
