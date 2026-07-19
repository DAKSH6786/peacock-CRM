import type { Metadata } from "next";

import { auth } from "@/auth";
import { PageHeader } from "@/components/shared/page-header";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { requirePermission } from "@/permissions";

export const metadata: Metadata = {
  title: "Dashboard",
};

export default async function DashboardPage() {
  const session = await auth();
  requirePermission(
    session?.user
      ? {
          id: session.user.id,
          email: session.user.email ?? "",
          name: session.user.name,
          organizationId: session.user.organizationId,
          role: session.user.role as never,
          status: session.user.status,
        }
      : null,
    "dashboard:view",
  );

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="Operational overview for Digital Peacock. Module metrics will populate from live services and the seed dataset."
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>CRM & pipeline</CardTitle>
            <CardDescription>
              Leads, contacts, companies, and deal stages.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-[var(--muted)]">
              Connect seed data to begin tracking opportunities.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Delivery & XYME</CardTitle>
            <CardDescription>
              Projects, tasks, and goal cadence across teams.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-[var(--muted)]">
              Workload and goal progress will appear here.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>People & finance</CardTitle>
            <CardDescription>
              HR, attendance, invoices, and approvals.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-[var(--muted)]">
              Sensitive financial figures remain permission-gated.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
