import Link from "next/link";

import { ReportDateFilter } from "@/components/reports/report-controls";
import { ChartCard } from "@/components/shared/chart-card";
import { EmptyState } from "@/components/shared/empty-state";
import { MetricCard } from "@/components/shared/metric-card";
import { PageHeader } from "@/components/shared/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { formatMoney, formatPercent } from "@/lib/utils";
import { toDateInputValue } from "@/modules/reports/date-range";
import { revenueDefinitionLabel } from "@/modules/reports/revenue";
import type { ReportPayload } from "@/modules/reports/types";
import { ReportExportActions } from "@/components/reports/report-export-actions";

function formatMetric(
  value: number,
  format: "money" | "number" | "percent" | "days",
  currencyCode: string,
) {
  switch (format) {
    case "money":
      return formatMoney(value, currencyCode, "en-IN");
    case "percent":
      return formatPercent(value);
    case "days":
      return `${value}d`;
    default:
      return new Intl.NumberFormat("en-IN").format(value);
  }
}

export function ReportViewer({
  payload,
  canExport,
}: {
  payload: ReportPayload;
  canExport: boolean;
}) {
  const revenueLabel = revenueDefinitionLabel(payload.revenueDefinition);
  const hasData =
    payload.metrics.some((metric) => metric.value !== 0) ||
    payload.series.length > 0 ||
    payload.table.rows.length > 0;

  return (
    <div>
      <PageHeader
        title={payload.title}
        description={payload.description}
        actions={
          <>
            {payload.drilldownHref ? (
              <Button asChild variant="secondary">
                <Link href={payload.drilldownHref}>Open records</Link>
              </Button>
            ) : null}
            <ReportExportActions reportKey={payload.key} canExport={canExport} />
          </>
        }
      />

      <div className="mb-4 flex flex-wrap gap-2">
        <Badge tone="teal">{payload.range.label}</Badge>
        <Badge tone="info">{payload.currencyCode}</Badge>
        {revenueLabel ? <Badge tone="violet">{revenueLabel}</Badge> : null}
        <Badge tone="default">
          Refreshed{" "}
          {new Intl.DateTimeFormat("en-IN", {
            dateStyle: "medium",
            timeStyle: "short",
          }).format(new Date(payload.refreshedAt))}
        </Badge>
      </div>

      <div className="mb-6">
        <ReportDateFilter
          from={toDateInputValue(payload.range.from)}
          to={toDateInputValue(payload.range.to)}
        />
      </div>

      <p className="mb-6 text-sm text-[var(--muted)]" role="note">
        {payload.summary}
      </p>

      {!hasData ? (
        <EmptyState
          title="No data for this range"
          description="Widen the date filter or ensure related records exist in the database."
        />
      ) : (
        <>
          {payload.metrics.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              {payload.metrics.map((item) => (
                <MetricCard
                  key={item.label}
                  label={item.label}
                  value={formatMetric(item.value, item.format, payload.currencyCode)}
                  hint={item.hint}
                />
              ))}
            </div>
          ) : null}

          {payload.series.length > 0 ? (
            <div className="mt-6">
              <ChartCard
                title={payload.title}
                description={payload.summary}
                data={payload.series.map((point) => ({
                  label: point.label,
                  value: point.value,
                }))}
              />
            </div>
          ) : null}

          {payload.table.rows.length > 0 ? (
            <Card className="mt-6">
              <CardHeader>
                <CardTitle>Supporting records</CardTitle>
                <CardDescription>
                  Drill into rows for the underlying operational screens.
                </CardDescription>
              </CardHeader>
              <CardContent className="overflow-x-auto">
                <table className="w-full min-w-[40rem] text-left text-sm">
                  <thead>
                    <tr className="border-b border-[var(--border)] text-[var(--muted)]">
                      {payload.table.columns.map((column) => (
                        <th key={column.key} className="px-2 py-2 font-medium">
                          {column.label}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {payload.table.rows.map((row) => (
                      <tr
                        key={row.id}
                        className="border-b border-[var(--border)] last:border-0"
                      >
                        {payload.table.columns.map((column, index) => {
                          const raw = row.values[column.key];
                          const display =
                            typeof raw === "number"
                              ? formatMetric(
                                  raw,
                                  column.format ?? "number",
                                  payload.currencyCode,
                                )
                              : (raw ?? "—");
                          return (
                            <td key={column.key} className="px-2 py-2">
                              {index === 0 && row.href ? (
                                <Link
                                  href={row.href}
                                  className="font-semibold text-[var(--accent-teal)] hover:underline"
                                >
                                  {display}
                                </Link>
                              ) : (
                                display
                              )}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          ) : null}
        </>
      )}
    </div>
  );
}
