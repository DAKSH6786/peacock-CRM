import type { Metadata } from "next";
import Link from "next/link";

import { auth } from "@/auth";
import { HealthBadge, ProgressBar } from "@/components/progress/health-badge";
import { ObjectiveCreateForm } from "@/components/progress/objective-create-form";
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
import { listObjectives } from "@/modules/progress";
import { requirePermission } from "@/permissions";
import { hasPermission } from "@/permissions/types";
import type { MembershipRole } from "@prisma/client";

export const metadata: Metadata = {
  title: "Objectives",
};

export default async function ObjectivesPage({
  searchParams,
}: {
  searchParams: Promise<{ scope?: string; health?: string; quarter?: string }>;
}) {
  const session = await auth();
  const user = toSessionUser(session);
  requirePermission(user, "progress:view");
  const organizationId = user!.organizationId!;
  const canManage = hasPermission(
    user!.role as MembershipRole | null,
    "progress:manage",
  );
  const params = await searchParams;

  const [objectives, departments] = await Promise.all([
    listObjectives({
      organizationId,
      scope: params.scope,
      health: params.health,
      quarter: params.quarter,
    }),
    prisma.department.findMany({
      where: { organizationId, deletedAt: null },
      select: { id: true, name: true },
      orderBy: { name: "asc" },
    }),
  ]);

  const parents = objectives.map((o) => ({
    id: o.id,
    title: o.title,
    scope: o.scope,
  }));

  return (
    <div>
      <PageHeader
        title="Objectives"
        description="Company, department, team, and individual objectives with parent alignment."
        actions={
          <>
            <Button asChild variant="secondary">
              <Link href="/company-progress">Dashboard</Link>
            </Button>
            {canManage ? (
              <ObjectiveCreateForm parents={parents} departments={departments} />
            ) : null}
          </>
        }
      />

      <div className="mb-4 flex flex-wrap gap-2 text-sm">
        {[
          { href: "/company-progress/objectives", label: "All" },
          {
            href: "/company-progress/objectives?scope=COMPANY",
            label: "Company",
          },
          {
            href: "/company-progress/objectives?scope=DEPARTMENT",
            label: "Department",
          },
          { href: "/company-progress/objectives?scope=TEAM", label: "Team" },
          {
            href: "/company-progress/objectives?scope=INDIVIDUAL",
            label: "Individual",
          },
          {
            href: "/company-progress/objectives?health=AMBER",
            label: "At risk",
          },
          {
            href: "/company-progress/objectives?health=RED",
            label: "Off track",
          },
        ].map((f) => (
          <Link
            key={f.href}
            href={f.href}
            className="rounded-md border border-[var(--border)] px-3 py-1 hover:bg-[var(--surface)]"
          >
            {f.label}
          </Link>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{objectives.length} objectives</CardTitle>
          <CardDescription>
            Linked objectives show parent alignment toward company strategy
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead>
                <tr className="border-b border-[var(--border)] text-[var(--muted)]">
                  <th className="py-2 pr-3 font-medium">Title</th>
                  <th className="py-2 pr-3 font-medium">Level</th>
                  <th className="py-2 pr-3 font-medium">Parent</th>
                  <th className="py-2 pr-3 font-medium">Owner</th>
                  <th className="py-2 pr-3 font-medium">Quarter</th>
                  <th className="py-2 pr-3 font-medium">Health</th>
                  <th className="py-2 font-medium">Progress</th>
                </tr>
              </thead>
              <tbody>
                {objectives.map((o) => (
                  <tr
                    key={o.id}
                    className="border-b border-[var(--border)]/60 last:border-0"
                  >
                    <td className="py-3 pr-3">
                      <Link
                        href={`/company-progress/objectives/${o.id}`}
                        className="font-medium hover:underline"
                      >
                        {o.title}
                      </Link>
                      {o.department ? (
                        <p className="text-xs text-[var(--muted)]">
                          {o.department.name}
                        </p>
                      ) : null}
                    </td>
                    <td className="py-3 pr-3">{o.scope}</td>
                    <td className="py-3 pr-3 text-[var(--muted)]">
                      {o.parent?.title ?? "—"}
                    </td>
                    <td className="py-3 pr-3">
                      {o.primaryOwner?.name ?? "—"}
                    </td>
                    <td className="py-3 pr-3">{o.quarter ?? "—"}</td>
                    <td className="py-3 pr-3">
                      <HealthBadge health={o.health} />
                    </td>
                    <td className="py-3">
                      <div className="flex min-w-[120px] items-center gap-2">
                        <ProgressBar value={o.progressPct} />
                        <span className="tabular-nums">{o.progressPct}%</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {objectives.length === 0 ? (
              <p className="py-8 text-center text-sm text-[var(--muted)]">
                No objectives yet.
              </p>
            ) : null}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
