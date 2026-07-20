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
import { getLeadActivityReport } from "@/modules/crm";
import { requirePermission } from "@/permissions";

export const metadata: Metadata = {
  title: "Lead activity",
};

export default async function LeadActivityPage() {
  const session = await auth();
  const user = toSessionUser(session);
  requirePermission(user, "crm:view");
  const report = await getLeadActivityReport(user!.organizationId!);

  return (
    <div>
      <PageHeader
        title="Lead activity report"
        description="Calls, meetings, notes, and follow-up completions over the last 30 days."
        actions={
          <>
            <Button asChild variant="secondary">
              <Link href="/reports/crm">Full CRM reports</Link>
            </Button>
            <Button asChild variant="secondary">
              <Link href="/crm">CRM hub</Link>
            </Button>
          </>
        }
      />
      <div className="grid gap-4 md:grid-cols-4">
        <Metric title="Calls" value={report.calls} />
        <Metric title="Meetings" value={report.meetings} />
        <Metric title="Follow-ups done" value={report.followUpsCompleted} />
        <Metric
          title="Activity types"
          value={report.byType.reduce((s, r) => s + r.count, 0)}
        />
      </div>
      <Card className="mt-6">
        <CardHeader>
          <CardTitle>By type</CardTitle>
          <CardDescription>Since {report.since.slice(0, 10)}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          {report.byType.map((row) => (
            <div key={row.type} className="flex justify-between">
              <span>{row.type}</span>
              <span>{row.count}</span>
            </div>
          ))}
          {report.byType.length === 0 ? (
            <p className="text-[var(--muted)]">No activities logged yet.</p>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}

function Metric({ title, value }: { title: string; value: number }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent className="text-2xl font-semibold">{value}</CardContent>
    </Card>
  );
}
