import type { Metadata } from "next";
import Link from "next/link";

import { auth } from "@/auth";
import { LeadForm } from "@/components/crm/lead-form";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import { toSessionUser } from "@/lib/session-user";
import { getCrmLookups } from "@/modules/crm";
import { requirePermission } from "@/permissions";

export const metadata: Metadata = {
  title: "New lead",
};

export default async function NewLeadPage() {
  const session = await auth();
  const user = toSessionUser(session);
  requirePermission(user, "crm:manage");
  const lookups = await getCrmLookups(user!.organizationId!);

  return (
    <div>
      <PageHeader
        title="Create lead"
        description="Capture contact, qualification, and pipeline placement."
        actions={
          <Button asChild variant="secondary">
            <Link href="/crm/leads">Back to leads</Link>
          </Button>
        }
      />
      <LeadForm mode="create" lookups={lookups} />
    </div>
  );
}
