import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { auth } from "@/auth";
import { LeadDetailView } from "@/components/crm/lead-detail";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import { toSessionUser } from "@/lib/session-user";
import { getCrmLookups, getLeadDetail } from "@/modules/crm";
import { requirePermission } from "@/permissions";
import { hasPermission } from "@/permissions/types";
import type { MembershipRole } from "@prisma/client";

type Props = {
  params: Promise<{ leadId: string }>;
  searchParams: Promise<{ edit?: string }>;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { leadId } = await params;
  return { title: `Lead ${leadId.slice(0, 8)}` };
}

export default async function LeadDetailPage({ params, searchParams }: Props) {
  const session = await auth();
  const user = toSessionUser(session);
  requirePermission(user, "crm:view");
  const { leadId } = await params;
  const query = await searchParams;

  const [lead, lookups] = await Promise.all([
    getLeadDetail(user!.organizationId!, leadId),
    getCrmLookups(user!.organizationId!),
  ]);
  if (!lead) notFound();

  const canManage = hasPermission(
    user!.role as MembershipRole | null,
    "crm:manage",
  );

  return (
    <div>
      <PageHeader
        title={lead.personName}
        description={`${lead.companyName ?? "No company"} · ${lead.email ?? "No email"}`}
        actions={
          <Button asChild variant="secondary">
            <Link href="/crm/leads">All leads</Link>
          </Button>
        }
      />
      <LeadDetailView
        lead={{
          ...lead,
          lastContactedAt: lead.lastContactedAt?.toISOString() ?? null,
          nextFollowUpAt: lead.nextFollowUpAt?.toISOString() ?? null,
          activities: lead.activities.map((a) => ({
            ...a,
            occurredAt: a.occurredAt.toISOString(),
          })),
          callLogs: lead.callLogs.map((c) => ({
            ...c,
            occurredAt: c.occurredAt.toISOString(),
          })),
          meetings: lead.meetings.map((m) => ({
            ...m,
            startsAt: m.startsAt.toISOString(),
          })),
          notesList: lead.notesList.map((n) => ({
            ...n,
            createdAt: n.createdAt.toISOString(),
          })),
          emailActivities: lead.emailActivities.map((e) => ({
            ...e,
            occurredAt: e.occurredAt.toISOString(),
          })),
          followUps: lead.followUps.map((f) => ({
            ...f,
            dueAt: f.dueAt.toISOString(),
            completedAt: f.completedAt?.toISOString() ?? null,
          })),
          stageHistory: lead.stageHistory.map((s) => ({
            ...s,
            createdAt: s.createdAt.toISOString(),
          })),
          assignmentHistory: lead.assignmentHistory.map((a) => ({
            ...a,
            createdAt: a.createdAt.toISOString(),
          })),
        }}
        lookups={lookups}
        canManage={canManage}
        startInEdit={query.edit === "1"}
      />
    </div>
  );
}
