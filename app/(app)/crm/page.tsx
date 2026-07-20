import type { Metadata } from "next";
import Link from "next/link";

import { auth } from "@/auth";
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
import { getFollowUpReminders, getSalespersonWorkload } from "@/modules/crm";
import { listDuplicateReviews } from "@/modules/crm/leads";
import { requirePermission } from "@/permissions";
import { hasPermission } from "@/permissions/types";
import type { MembershipRole } from "@prisma/client";
import { prisma } from "@/database";

export const metadata: Metadata = {
  title: "CRM",
};

export default async function CrmHubPage() {
  const session = await auth();
  const user = toSessionUser(session);
  requirePermission(user, "crm:view");
  const organizationId = user!.organizationId!;
  const canManage = hasPermission(
    user!.role as MembershipRole | null,
    "crm:manage",
  );

  const [leadCount, openFollowUps, duplicates, workload, reminders] =
    await Promise.all([
      prisma.lead.count({ where: { organizationId, deletedAt: null } }),
      prisma.followUp.count({
        where: { organizationId, completedAt: null },
      }),
      listDuplicateReviews(organizationId),
      getSalespersonWorkload(organizationId),
      getFollowUpReminders(organizationId),
    ]);

  return (
    <div>
      <PageHeader
        title="CRM"
        description="Lead management, pipeline, follow-ups, conversion, and sales workload."
        actions={
          <>
            <Button asChild variant="secondary">
              <Link href="/crm/pipeline">Pipeline</Link>
            </Button>
            {canManage ? (
              <Button asChild>
                <Link href="/crm/leads/new">New lead</Link>
              </Button>
            ) : null}
          </>
        }
      />

      <div className="mb-6 grid gap-4 md:grid-cols-4">
        <StatCard title="Leads" value={String(leadCount)} href="/crm/leads" />
        <StatCard
          title="Open follow-ups"
          value={String(openFollowUps)}
          href="/crm/follow-ups"
        />
        <StatCard
          title="Overdue"
          value={String(reminders.overdue.length)}
          href="/crm/follow-ups"
        />
        <StatCard
          title="Duplicate reviews"
          value={String(duplicates.length)}
          href="/crm/leads/duplicates"
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Quick links</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {(
              [
                ["/crm/leads", "Lead table"],
                ["/crm/pipeline", "Kanban pipeline"],
                ["/crm/follow-ups", "Follow-up calendar"],
                ["/crm/workload", "Salesperson workload"],
                ["/crm/activity", "Lead activity report"],
                ["/crm/leads/duplicates", "Duplicate review"],
                ["/imports", "Bulk import"],
                ["/reports/crm", "CRM reports"],
              ] as const
            ).map(([href, label]) => (
              <Button key={href} asChild variant="secondary" size="sm">
                <Link href={href}>{label}</Link>
              </Button>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Workload snapshot</CardTitle>
            <CardDescription>Open leads by salesperson</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {workload.slice(0, 6).map((row) => (
              <div key={row.userId} className="flex justify-between gap-2">
                <span>{row.name}</span>
                <span className="text-[var(--muted)]">
                  {row.openLeads} open · {row.overdueFollowUps} overdue
                </span>
              </div>
            ))}
            {workload.length === 0 ? (
              <p className="text-[var(--muted)]">No assigned open leads.</p>
            ) : null}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function StatCard({
  title,
  value,
  href,
}: {
  title: string;
  value: string;
  href: string;
}) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">
          <Link href={href} className="hover:underline">
            {title}
          </Link>
        </CardTitle>
      </CardHeader>
      <CardContent className="text-2xl font-semibold">{value}</CardContent>
    </Card>
  );
}
