import type { Metadata } from "next";
import Link from "next/link";

import { auth } from "@/auth";
import { ProgressBar } from "@/components/progress/health-badge";
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
import { getCompanyProgressDashboard } from "@/modules/progress";
import { requirePermission } from "@/permissions";

export const metadata: Metadata = {
  title: "Department progress",
};

export default async function DepartmentsProgressPage() {
  const session = await auth();
  const user = toSessionUser(session);
  requirePermission(user, "progress:view");
  const dashboard = await getCompanyProgressDashboard(user!.organizationId!);

  return (
    <div>
      <PageHeader
        title="Department progress"
        description="Department scorecards and objective roll-ups."
        actions={
          <>
            <Button asChild variant="secondary">
              <Link href="/company-progress">Company dashboard</Link>
            </Button>
            <Button asChild variant="secondary">
              <Link href="/company-progress/scorecards">Scorecards</Link>
            </Button>
          </>
        }
      />

      <div className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {dashboard.byDepartment.map((dept) => (
          <Card key={dept.departmentId}>
            <CardHeader>
              <CardTitle>{dept.name}</CardTitle>
              <CardDescription>
                {dept.objectiveCount} objectives · {dept.onTrack} on track ·{" "}
                {dept.atRisk} at risk · {dept.offTrack} off track
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="mb-2 flex justify-between text-sm">
                <span>Progress</span>
                <span className="font-medium tabular-nums">
                  {dept.progressPct}%
                </span>
              </div>
              <ProgressBar value={dept.progressPct} />
              <Button asChild variant="secondary" size="sm" className="mt-4">
                <Link
                  href={`/company-progress/objectives?scope=DEPARTMENT`}
                >
                  View objectives
                </Link>
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Scorecards</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          {dashboard.scorecards.map((sc) => (
            <div
              key={sc.id}
              className="rounded-lg border border-[var(--border)] p-4"
            >
              <h3 className="mb-2 font-semibold">{sc.department.name}</h3>
              <ul className="space-y-1 text-sm">
                {sc.kpis.map((kpi) => (
                  <li key={kpi.id} className="flex justify-between gap-2">
                    <span>{kpi.name}</span>
                    <span className="tabular-nums">
                      {kpi.latestValue ?? "—"}
                      {kpi.unit ? ` ${kpi.unit}` : ""}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
          {dashboard.scorecards.length === 0 ? (
            <p className="text-sm text-[var(--muted)]">
              No scorecards configured.{" "}
              <Link href="/company-progress/scorecards" className="underline">
                Configure now
              </Link>
            </p>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
