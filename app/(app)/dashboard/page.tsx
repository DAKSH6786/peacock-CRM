import type { Metadata } from "next";
import Link from "next/link";

import { auth } from "@/auth";
import { ChartCard } from "@/components/shared/chart-card";
import { MetricCard } from "@/components/shared/metric-card";
import { PageHeader } from "@/components/shared/page-header";
import { ActivityTimeline } from "@/components/shared/activity-timeline";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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

const activityShape = [
  { label: "Mon", value: 0 },
  { label: "Tue", value: 0 },
  { label: "Wed", value: 0 },
  { label: "Thu", value: 0 },
  { label: "Fri", value: 0 },
  { label: "Sat", value: 0 },
  { label: "Sun", value: 0 },
];

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
        title="Command center"
        description="A live operating view across growth, delivery, people, and finance for Digital Peacock."
        actions={
          <>
            <Button asChild variant="secondary">
              <Link href="/approvals">Review approvals</Link>
            </Button>
            <Button asChild>
              <Link href="/crm/leads">Open CRM</Link>
            </Button>
          </>
        }
      />

      <div className="mb-6 flex flex-wrap items-center gap-2">
        <Badge tone="teal">Permission-aware shell</Badge>
        <Badge tone="violet">Dark mode default</Badge>
        <Badge tone="info">Metrics hydrate from services</Badge>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Open pipeline"
          value="—"
          hint="Awaiting CRM metrics"
        />
        <MetricCard
          label="Active projects"
          value="—"
          hint="Awaiting delivery metrics"
        />
        <MetricCard
          label="Pending approvals"
          value="—"
          hint="Awaiting workflow queue"
        />
        <MetricCard
          label="XYME on track"
          value="—"
          hint="Awaiting goal cadence"
        />
      </div>

      <div className="mt-6 grid gap-4 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <ChartCard
            title="Lead activity"
            description="Weekly volume appears here once CRM analytics are connected."
            data={activityShape}
            valueLabel="Leads"
          />
        </div>
        <Card>
          <CardHeader>
            <CardTitle>Focus today</CardTitle>
            <CardDescription>
              Prioritized work for your operating rhythm.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ActivityTimeline
              items={[
                {
                  id: "1",
                  title: "Review approval inbox",
                  description: "Home · Approvals",
                  at: "Today",
                },
                {
                  id: "2",
                  title: "Check delivery blockers",
                  description: "Delivery · Projects",
                  at: "Today",
                },
                {
                  id: "3",
                  title: "Update XYME progress",
                  description: "Performance · XYME",
                  at: "This week",
                },
              ]}
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
