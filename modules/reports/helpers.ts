import type {
  ReportDateRange,
  ReportDefinition,
  ReportMeasureFormat,
  ReportPayload,
  ReportSeriesPoint,
  ReportTableColumn,
  ReportTableRow,
} from "@/modules/reports/types";

export function emptyPayload(
  definition: ReportDefinition,
  range: ReportDateRange,
  currencyCode: string,
  summary: string,
): ReportPayload {
  return {
    key: definition.key,
    title: definition.title,
    category: definition.category,
    description: definition.description,
    range,
    currencyCode,
    revenueDefinition: definition.revenueDefinition,
    refreshedAt: new Date().toISOString(),
    summary,
    metrics: [],
    series: [],
    table: { columns: [], rows: [] },
  };
}

export function buildPayload(input: {
  definition: ReportDefinition;
  range: ReportDateRange;
  currencyCode: string;
  summary: string;
  metrics?: ReportPayload["metrics"];
  series?: ReportSeriesPoint[];
  columns?: ReportTableColumn[];
  rows?: ReportTableRow[];
  drilldownHref?: string;
}): ReportPayload {
  return {
    key: input.definition.key,
    title: input.definition.title,
    category: input.definition.category,
    description: input.definition.description,
    range: input.range,
    currencyCode: input.currencyCode,
    revenueDefinition: input.definition.revenueDefinition,
    refreshedAt: new Date().toISOString(),
    summary: input.summary,
    metrics: input.metrics ?? [],
    series: input.series ?? [],
    table: {
      columns: input.columns ?? [],
      rows: input.rows ?? [],
    },
    drilldownHref: input.drilldownHref,
  };
}

export function metric(
  label: string,
  value: number,
  format: ReportMeasureFormat,
  hint?: string,
) {
  return { label, value, format, hint };
}

export function seriesFromMap(map: Map<string, number>): ReportSeriesPoint[] {
  return [...map.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([label, value]) => ({ label, value }));
}

export function dayKey(date: Date): string {
  return date.toISOString().slice(0, 10);
}

export function accessibleSeriesSummary(
  title: string,
  series: ReportSeriesPoint[],
  format: ReportMeasureFormat = "number",
): string {
  if (series.length === 0) {
    return `${title}: no data points in the selected range.`;
  }
  const parts = series.map((point) => {
    const formatted =
      format === "percent"
        ? `${point.value}%`
        : format === "money"
          ? String(point.value)
          : String(point.value);
    return `${point.label} ${formatted}`;
  });
  return `${title}: ${parts.join("; ")}.`;
}

export function rangeMs(range: ReportDateRange): number {
  return Math.max(1, range.to.getTime() - range.from.getTime());
}
