import type { Metadata } from "next";
import Link from "next/link";

import { auth } from "@/auth";
import {
  formatMinor,
  ProgressBar,
} from "@/components/progress/health-badge";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { toSessionUser } from "@/lib/session-user";
import {
  getCompanyProgressDashboard,
  getUpdateReminders,
} from "@/modules/progress";
import { requirePermission } from "@/permissions";
import { hasPermission } from "@/permissions/types";
import type { MembershipRole } from "@prisma/client";

export const metadata: Metadata = {
  title: "Company progress",
};

export default async function CompanyProgressPage() {
  const session = await auth();
  const user = toSessionUser(session);
  requirePermission(user, "progress:view");
  const organizationId = user!.organizationId!;
  const canManage = hasPermission(
    user!.role as MembershipRole | null,
    "progress:manage",
  );

  const [dashboard, reminders] = await Promise.all([
    getCompanyProgressDashboard(organizationId),
    getUpdateReminders(organizationId),
  ]);

  return (
    <div>
      <PageHeader
        title="Company progress"
        description="Objectives, department scorecards, commercial health, and business reviews."
        actions={
          <>
            <Button asChild variant="secondary">
              <Link href="/company-progress/objectives">Objectives</Link>
            </Button>
            <Button asChild variant="secondary">
              <Link href="/company-progress/scorecards">Scorecards</Link>
            </Button>
            <Button asChild variant="secondary">
              <Link href="/company-progress/reviews">Reviews</Link>
            </Button>
            {canManage ? (
              <Button asChild>
                <Link href="/company-progress/objectives">Manage</Link>
              </Button>
            ) : null}
          </>
        }
      />

      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Overall progress"
          value={`${dashboard.overallProgressPct}%`}
        />
        <MetricCard
          title="On track"
          value={String(dashboard.objectiveCounts.onTrack)}
        />
        <MetricCard
          title="At risk"
          value={String(dashboard.objectiveCounts.atRisk)}
        />
        <MetricCard
          title="Delayed"
          value={String(dashboard.objectiveCounts.delayed)}
        />
      </div>

      <div className="mb-6 grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Progress by department</CardTitle>
            <CardDescription>Average objective completion</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {dashboard.byDepartment.map((dept) => (
              <div key={dept.departmentId}>
                <div className="mb-1 flex items-center justify-between text-sm">
                  <span className="font-medium">{dept.name}</span>
                  <span className="text-[var(--muted)]">
                    {dept.progressPct}% · {dept.objectiveCount} objectives
                  </span>
                </div>
                <ProgressBar value={dept.progressPct} />
              </div>
            ))}
            {dashboard.byDepartment.length === 0 ? (
              <p className="text-sm text-[var(--muted)]">No departments yet.</p>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>By quarter</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {dashboard.byQuarter.map((q) => (
              <div
                key={q.quarter}
                className="flex items-center justify-between text-sm"
              >
                <span>{q.quarter}</span>
                <span className="font-medium">{q.progressPct}%</span>
              </div>
            ))}
            {dashboard.byQuarter.length === 0 ? (
              <p className="text-sm text-[var(--muted)]">No quarter data.</p>
            ) : null}
          </CardContent>
        </Card>
      </div>

      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Revenue vs target"
          value={formatMinor(dashboard.commercial.closedRevenueMinor)}
          hint={
            dashboard.commercial.revenueTargetMinor != null
              ? `Target ${formatMinor(dashboard.commercial.revenueTargetMinor)}`
              : "No target set"
          }
        />
        <MetricCard
          title="Pipeline vs target"
          value={formatMinor(dashboard.commercial.pipelineWeightedMinor)}
          hint={
            dashboard.commercial.pipelineTargetMinor != null
              ? `Target ${formatMinor(dashboard.commercial.pipelineTargetMinor)}`
              : "Weighted open pipeline"
          }
        />
        <MetricCard
          title="Active clients"
          value={String(dashboard.commercial.activeClients)}
          hint={`Retention ${dashboard.commercial.clientRetentionPct}%`}
        />
        <MetricCard
          title="Invoice collection"
          value={`${dashboard.commercial.invoiceCollectionRate}%`}
          hint={`${dashboard.commercial.overdueInvoiceCount} overdue`}
        />
        <MetricCard
          title="Project delivery"
          value={String(dashboard.deliveryHealth.active)}
          hint={`${dashboard.deliveryHealth.completed} completed`}
        />
        <MetricCard
          title="Billable utilization"
          value={`${dashboard.peopleOps.billableUtilization}%`}
        />
        <MetricCard
          title="Hiring progress"
          value={String(dashboard.peopleOps.openPositions)}
          hint="Open positions"
        />
        <MetricCard
          title="XYME completion"
          value={`${dashboard.peopleOps.xymeCompletionPct}%`}
          hint={`${dashboard.peopleOps.xymeApprovedPlans}/${dashboard.peopleOps.xymeTotalPlans} approved`}
        />
      </div>

      <div className="mb-6 grid gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Top risks</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {dashboard.topRisks.map((risk) => (
              <div key={risk.id} className="text-sm">
                <p className="font-medium">{risk.title}</p>
                <p className="text-[var(--muted)]">
                  Impact {risk.impact ?? "—"} · Likelihood {risk.likelihood ?? "—"}
                </p>
              </div>
            ))}
            {dashboard.topRisks.length === 0 ? (
              <p className="text-sm text-[var(--muted)]">No open risks.</p>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent decisions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {dashboard.recentDecisions.map((d) => (
              <div key={d.id} className="text-sm">
                <p className="font-medium">{d.title}</p>
                <p className="line-clamp-2 text-[var(--muted)]">{d.decision}</p>
              </div>
            ))}
            {dashboard.recentDecisions.length === 0 ? (
              <p className="text-sm text-[var(--muted)]">No decisions logged.</p>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Update reminders</CardTitle>
            <CardDescription>Objectives without a weekly check-in</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {reminders.slice(0, 8).map((r) => (
              <Link
                key={r.objectiveId}
                href={`/company-progress/objectives/${r.objectiveId}`}
                className="block text-sm hover:underline"
              >
                <p className="font-medium">{r.title}</p>
                <p className="text-[var(--muted)]">
                  {r.owner?.name ?? "Unassigned"}
                </p>
              </Link>
            ))}
            {reminders.length === 0 ? (
              <p className="text-sm text-[var(--muted)]">All updates current.</p>
            ) : null}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Department scorecards</CardTitle>
          <CardDescription>
            Configurable KPIs — each department can use different metrics
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {dashboard.scorecards.map((sc) => (
              <div
                key={sc.id}
                className="rounded-lg border border-[var(--border)] p-4"
              >
                <div className="mb-3 flex items-center justify-between">
                  <h3 className="font-semibold">{sc.department.name}</h3>
                  <span className="text-xs text-[var(--muted)]">{sc.name}</span>
                </div>
                <ul className="space-y-2 text-sm">
                  {sc.kpis.map((kpi) => (
                    <li
                      key={kpi.id}
                      className="flex items-center justify-between gap-2"
                    >
                      <span>{kpi.name}</span>
                      <span className="font-medium tabular-nums">
                        {kpi.latestValue ?? "—"}
                        {kpi.unit ? ` ${kpi.unit}` : ""}
                      </span>
                    </li>
                  ))}
                  {sc.kpis.length === 0 ? (
                    <li className="text-[var(--muted)]">No KPIs configured</li>
                  ) : null}
                </ul>
              </div>
            ))}
          </div>
          {dashboard.scorecards.length === 0 ? (
            <p className="text-sm text-[var(--muted)]">
              No scorecards yet.{" "}
              <Link
                href="/company-progress/scorecards"
                className="underline underline-offset-2"
              >
                Configure scorecards
              </Link>
            </p>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}

function MetricCard({
  title,
  value,
  hint,
}: {
  title: string;
  value: string;
  hint?: string;
}) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardDescription>{title}</CardDescription>
        <CardTitle className="text-2xl tabular-nums">{value}</CardTitle>
      </CardHeader>
      {hint ? (
        <CardContent>
          <p className="text-xs text-[var(--muted)]">{hint}</p>
        </CardContent>
      ) : null}
    </Card>
  );
}
