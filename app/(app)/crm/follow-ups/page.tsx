import type { Metadata } from "next";
import Link from "next/link";

import { auth } from "@/auth";
import { PageHeader } from "@/components/shared/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { toSessionUser } from "@/lib/session-user";
import { getFollowUpReminders, listFollowUps } from "@/modules/crm";
import { requirePermission } from "@/permissions";

export const metadata: Metadata = {
  title: "Follow-ups",
};

export default async function FollowUpsPage() {
  const session = await auth();
  const user = toSessionUser(session);
  requirePermission(user, "crm:view");
  const organizationId = user!.organizationId!;

  const start = new Date();
  start.setHours(0, 0, 0, 0);
  const end = new Date(start);
  end.setDate(end.getDate() + 14);

  const [followUps, reminders] = await Promise.all([
    listFollowUps({ organizationId, from: start, to: end }),
    getFollowUpReminders(organizationId),
  ]);

  return (
    <div>
      <PageHeader
        title="Follow-up calendar"
        description="Upcoming and overdue follow-ups with reminders."
        actions={
          <Button asChild variant="secondary">
            <Link href="/crm/leads">Leads</Link>
          </Button>
        }
      />

      <div className="mb-6 grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Overdue reminders</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {reminders.overdue.length === 0 ? (
              <p className="text-[var(--muted)]">None overdue.</p>
            ) : (
              reminders.overdue.map((f) => (
                <div key={f.id} className="flex justify-between gap-2">
                  <Link
                    href={`/crm/leads/${f.lead.id}`}
                    className="hover:underline"
                  >
                    {f.lead.personName}
                  </Link>
                  <Badge tone="default">{f.dueAt.toISOString().slice(0, 10)}</Badge>
                </div>
              ))
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Due in 48 hours</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {reminders.upcoming.length === 0 ? (
              <p className="text-[var(--muted)]">Nothing upcoming.</p>
            ) : (
              reminders.upcoming.map((f) => (
                <div key={f.id} className="flex justify-between gap-2">
                  <Link
                    href={`/crm/leads/${f.lead.id}`}
                    className="hover:underline"
                  >
                    {f.lead.personName}
                  </Link>
                  <span className="text-[var(--muted)]">
                    {f.dueAt.toISOString().slice(0, 16).replace("T", " ")}
                  </span>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Next 14 days</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          {followUps.map((f) => (
            <div
              key={f.id}
              className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--border)] pb-2"
            >
              <div>
                <Link
                  href={`/crm/leads/${f.lead.id}`}
                  className="font-medium hover:underline"
                >
                  {f.lead.personName}
                </Link>
                <p className="text-xs text-[var(--muted)]">
                  {f.lead.companyName} · {f.notes}
                </p>
              </div>
              <div className="flex items-center gap-2">
                {f.completedAt ? <Badge tone="default">Done</Badge> : null}
                <span>{f.dueAt.toISOString().slice(0, 16).replace("T", " ")}</span>
              </div>
            </div>
          ))}
          {followUps.length === 0 ? (
            <p className="text-[var(--muted)]">No follow-ups in range.</p>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
