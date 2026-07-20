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
import { listDuplicateReviews } from "@/modules/crm";
import { requirePermission } from "@/permissions";
import { hasPermission } from "@/permissions/types";
import type { MembershipRole } from "@prisma/client";

import { DuplicateReviewPanel } from "@/components/crm/duplicate-review-panel";

export const metadata: Metadata = {
  title: "Duplicate review",
};

export default async function DuplicatesPage() {
  const session = await auth();
  const user = toSessionUser(session);
  requirePermission(user, "crm:view");
  const candidates = await listDuplicateReviews(user!.organizationId!);
  const canManage = hasPermission(
    user!.role as MembershipRole | null,
    "crm:manage",
  );

  return (
    <div>
      <PageHeader
        title="Duplicate review"
        description="Possible matches by normalized email, phone, domain, and company. Never merged automatically."
        actions={
          <Button asChild variant="secondary">
            <Link href="/crm/leads">Back to leads</Link>
          </Button>
        }
      />
      <Card>
        <CardHeader>
          <CardTitle>Pending candidates</CardTitle>
          <CardDescription>
            Dismiss after human review. Merge remains a deliberate future action.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <DuplicateReviewPanel
            candidates={candidates.map((c) => ({
              id: c.id,
              matchType: c.matchType,
              matchValue: c.matchValue,
              lead: c.lead,
              matchLead: c.matchLead,
            }))}
            canManage={canManage}
          />
        </CardContent>
      </Card>
    </div>
  );
}
