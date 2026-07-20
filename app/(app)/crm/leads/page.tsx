import type { Metadata } from "next";
import Link from "next/link";

import { auth } from "@/auth";
import { LeadTable } from "@/components/crm/lead-table";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import { toSessionUser } from "@/lib/session-user";
import { getCrmLookups, listLeads } from "@/modules/crm";
import { requirePermission } from "@/permissions";
import { hasPermission } from "@/permissions/types";
import type { MembershipRole } from "@prisma/client";
import { prisma } from "@/database";

export const metadata: Metadata = {
  title: "Leads",
};

export default async function LeadsPage() {
  const session = await auth();
  const user = toSessionUser(session);
  requirePermission(user, "crm:view");
  const organizationId = user!.organizationId!;
  const role = user!.role as MembershipRole | null;
  const canManage = hasPermission(role, "crm:manage");
  const canExport =
    hasPermission(role, "reports:export") || hasPermission(role, "crm:view");

  const [leads, lookups, savedViews] = await Promise.all([
    listLeads({ organizationId }),
    getCrmLookups(organizationId),
    prisma.savedView.findMany({
      where: {
        organizationId,
        userId: user!.id,
        module: "crm.leads",
      },
      orderBy: { name: "asc" },
    }),
  ]);

  return (
    <div>
      <PageHeader
        title="Leads"
        description="Advanced filters, bulk actions, scoring, and follow-up visibility."
        actions={
          <>
            <Button asChild variant="secondary">
              <Link href="/crm/pipeline">Kanban</Link>
            </Button>
            <Button asChild variant="secondary">
              <Link href="/crm/leads/duplicates">Duplicates</Link>
            </Button>
            <Button asChild variant="secondary">
              <Link href="/imports">Import</Link>
            </Button>
            {canManage ? (
              <Button asChild>
                <Link href="/crm/leads/new">New lead</Link>
              </Button>
            ) : null}
          </>
        }
      />

      {savedViews.length > 0 ? (
        <p className="mb-3 text-xs text-[var(--muted)]">
          Saved views: {savedViews.map((v) => v.name).join(" · ")}
        </p>
      ) : null}

      <LeadTable
        initialLeads={leads.map((lead) => ({
          id: lead.id,
          personName: lead.personName,
          companyName: lead.companyName,
          email: lead.email,
          phone: lead.phone,
          country: lead.country,
          estimatedValueMinor: lead.estimatedValueMinor,
          currencyCode: lead.currencyCode,
          leadScore: lead.leadScore,
          probability: lead.probability,
          lastContactedAt: lead.lastContactedAt?.toISOString() ?? null,
          nextFollowUpAt: lead.nextFollowUpAt?.toISOString() ?? null,
          ageDays: lead.ageDays,
          stale: lead.stale,
          source: lead.source,
          status: lead.status,
          stage: lead.stage,
          assignedUser: lead.assignedUser,
          tags: lead.tags,
          interestedServices: lead.interestedServices,
        }))}
        lookups={lookups}
        canManage={canManage}
        canExport={canExport}
      />
    </div>
  );
}
