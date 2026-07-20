import type { Metadata } from "next";
import Link from "next/link";

import { auth } from "@/auth";
import { ScorecardCreateForm } from "@/components/progress/scorecard-create-form";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { prisma } from "@/database";
import { toSessionUser } from "@/lib/session-user";
import {
  DEPARTMENT_KPI_TEMPLATES,
  listScorecards,
} from "@/modules/progress";
import { requirePermission } from "@/permissions";
import { hasPermission } from "@/permissions/types";
import type { MembershipRole } from "@prisma/client";

export const metadata: Metadata = {
  title: "Department scorecards",
};

export default async function ScorecardsPage() {
  const session = await auth();
  const user = toSessionUser(session);
  requirePermission(user, "progress:view");
  const organizationId = user!.organizationId!;
  const canManage = hasPermission(
    user!.role as MembershipRole | null,
    "progress:manage",
  );

  const [scorecards, departments] = await Promise.all([
    listScorecards(organizationId),
    prisma.department.findMany({
      where: { organizationId, deletedAt: null },
      select: { id: true, name: true, code: true },
      orderBy: { name: "asc" },
    }),
  ]);

  return (
    <div>
      <PageHeader
        title="Department scorecards"
        description="Configurable KPIs per department — Sales, Content, Design, Video, SEO, Web, HR, Finance, and custom sets."
        actions={
          <Button asChild variant="secondary">
            <Link href="/company-progress">Dashboard</Link>
          </Button>
        }
      />

      {canManage ? (
        <div className="mb-6">
          <ScorecardCreateForm
            departments={departments}
            templates={DEPARTMENT_KPI_TEMPLATES}
          />
        </div>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2">
        {scorecards.map((sc) => (
          <Card key={sc.id}>
            <CardHeader>
              <CardTitle>{sc.department.name}</CardTitle>
              <CardDescription>{sc.name}</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm">
                {sc.kpis.map((link) => (
                  <li
                    key={link.id}
                    className="flex items-center justify-between gap-2 border-b border-[var(--border)]/50 py-2 last:border-0"
                  >
                    <div>
                      <p className="font-medium">{link.kpi.name}</p>
                      <p className="text-xs text-[var(--muted)]">
                        {link.kpi.code}
                        {link.kpi.category ? ` · ${link.kpi.category}` : ""}
                      </p>
                    </div>
                    <span className="tabular-nums font-medium">
                      {link.kpi.values[0]
                        ? Number(link.kpi.values[0].value)
                        : "—"}
                      {link.kpi.unit ? ` ${link.kpi.unit}` : ""}
                    </span>
                  </li>
                ))}
                {sc.kpis.length === 0 ? (
                  <li className="text-[var(--muted)]">No KPIs linked</li>
                ) : null}
              </ul>
            </CardContent>
          </Card>
        ))}
      </div>

      {scorecards.length === 0 ? (
        <p className="text-sm text-[var(--muted)]">
          No scorecards configured yet.
        </p>
      ) : null}

      <Card className="mt-8">
        <CardHeader>
          <CardTitle>Available KPI templates</CardTitle>
          <CardDescription>
            Starting catalogs only — each department scorecard remains
            independently configurable.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Object.entries(DEPARTMENT_KPI_TEMPLATES).map(([code, kpis]) => (
            <div key={code}>
              <h3 className="mb-2 font-semibold">{code}</h3>
              <ul className="space-y-1 text-sm text-[var(--muted)]">
                {kpis.map((k) => (
                  <li key={k.code}>
                    {k.name}
                    {k.unit ? ` (${k.unit})` : ""}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
