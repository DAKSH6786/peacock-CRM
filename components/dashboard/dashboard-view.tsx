import Link from "next/link";

import { DashboardDateFilter } from "@/components/dashboard/dashboard-date-filter";
import {
  formatMetricValue,
  hasDashboardData,
} from "@/components/dashboard/format-metric";
import { ActivityTimeline } from "@/components/shared/activity-timeline";
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
import { toDateInputValue } from "@/modules/dashboard/date-range";
import type { DashboardPayload } from "@/modules/dashboard/metrics.types";
import { personaLabel } from "@/modules/dashboard/persona";

function formatActivityAt(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

export function DashboardView({ payload }: { payload: DashboardPayload }) {
  const hasData = hasDashboardData(payload);

  return (
    <div>
      <PageHeader
        title={personaLabel(payload.persona)}
        description={`Live operating metrics for ${payload.range.label}. All figures are calculated from organization records.`}
        actions={
          <>
            <Button asChild variant="secondary">
              <Link href="/my-work">Open My Work</Link>
            </Button>
            <Button asChild>
              <Link href="/approvals">Approvals</Link>
            </Button>
          </>
        }
      />

      <div className="mb-4 flex flex-wrap items-center gap-2">
        <Badge tone="teal">{personaLabel(payload.persona)}</Badge>
        <Badge tone="info">{payload.currencyCode}</Badge>
        <Badge tone="violet">{payload.range.label}</Badge>
      </div>

      <div className="mb-6">
        <DashboardDateFilter
          from={toDateInputValue(payload.range.from)}
          to={toDateInputValue(payload.range.to)}
        />
      </div>

      {!hasData ? (
        <EmptyState
          title="No metrics for this range"
          description="Add CRM, finance, delivery, or people records — or widen the date filter — to populate this dashboard."
          action={
            <Button asChild variant="secondary">
              <Link href="/crm/leads">Go to CRM</Link>
            </Button>
          }
        />
      ) : (
        <>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {payload.metrics.map((metric) => (
              <MetricCard
                key={metric.label}
                label={metric.label}
                value={formatMetricValue(metric)}
                hint={metric.hint}
              />
            ))}
          </div>

          {payload.charts.length > 0 ? (
            <div className="mt-6 grid gap-4 xl:grid-cols-2">
              {payload.charts.map((chart) => (
                <ChartCard
                  key={chart.id}
                  title={chart.title}
                  description={chart.description}
                  data={chart.data.map((point) => ({
                    label: point.name,
                    value: point.value,
                  }))}
                />
              ))}
            </div>
          ) : null}

          <div className="mt-6 grid gap-4 xl:grid-cols-3">
            <div className="space-y-4 xl:col-span-2">
              {payload.lists.length === 0 ? (
                <EmptyState
                  title="No detail lists"
                  description="Lists such as pipelines, approvals, and team queues appear here when related records exist."
                />
              ) : (
                payload.lists.map((list) => (
                  <Card key={list.id}>
                    <CardHeader>
                      <CardTitle>{list.title}</CardTitle>
                      <CardDescription>
                        {list.items.length === 0
                          ? "Nothing in this queue right now."
                          : `${list.items.length} item${list.items.length === 1 ? "" : "s"}`}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      {list.items.length === 0 ? (
                        <p className="text-sm text-[var(--muted)]">No rows.</p>
                      ) : (
                        <ul className="divide-y divide-[var(--border)]">
                          {list.items.map((item) => (
                            <li
                              key={item.id}
                              className="flex items-start justify-between gap-3 py-3 first:pt-0 last:pb-0"
                            >
                              <div className="min-w-0">
                                {item.href ? (
                                  <Link
                                    href={item.href}
                                    className="text-sm font-semibold text-[var(--accent-teal)] hover:underline"
                                  >
                                    {item.title}
                                  </Link>
                                ) : (
                                  <p className="text-sm font-semibold">
                                    {item.title}
                                  </p>
                                )}
                                {item.meta ? (
                                  <p className="mt-0.5 text-xs text-[var(--muted)]">
                                    {item.meta}
                                  </p>
                                ) : null}
                              </div>
                            </li>
                          ))}
                        </ul>
                      )}
                    </CardContent>
                  </Card>
                ))
              )}
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Recent business activity</CardTitle>
                <CardDescription>
                  Latest organization events from the activity feed.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ActivityTimeline
                  items={payload.activity.map((item) => ({
                    ...item,
                    at: formatActivityAt(item.at),
                  }))}
                />
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
