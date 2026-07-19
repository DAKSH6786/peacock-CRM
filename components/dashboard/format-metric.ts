import { formatMoney, formatPercent } from "@/lib/utils";
import type { MetricValue } from "@/modules/dashboard/metrics.types";

export function formatMetricValue(metric: MetricValue): string {
  switch (metric.format) {
    case "money":
      return formatMoney(
        metric.value,
        metric.currencyCode ?? "INR",
        "en-IN",
      );
    case "percent":
      return formatPercent(metric.value);
    case "number":
    default:
      return new Intl.NumberFormat("en-IN").format(metric.value);
  }
}

export function hasDashboardData(payload: {
  metrics: MetricValue[];
  charts: Array<{ data: unknown[] }>;
  lists: Array<{ items: unknown[] }>;
  activity: unknown[];
}): boolean {
  const metricSignal = payload.metrics.some((metric) => metric.value !== 0);
  const chartSignal = payload.charts.some((chart) => chart.data.length > 0);
  const listSignal = payload.lists.some((list) => list.items.length > 0);
  return metricSignal || chartSignal || listSignal || payload.activity.length > 0;
}
