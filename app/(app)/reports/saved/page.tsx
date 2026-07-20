import type { Metadata } from "next";
import Link from "next/link";

import { auth } from "@/auth";
import { EmptyState } from "@/components/shared/empty-state";
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
import { listSavedReports } from "@/modules/reports/builder/save";
import { requirePermission } from "@/permissions";

export const metadata: Metadata = {
  title: "Saved reports",
};

export default async function SavedReportsPage() {
  const session = await auth();
  const user = toSessionUser(session);
  requirePermission(user, "reports:view");

  const saved = await listSavedReports(user);

  return (
    <div>
      <PageHeader
        title="Saved reports"
        description="Reports you own or that were shared with your role."
        actions={
          <Button asChild>
            <Link href="/reports/builder">New builder report</Link>
          </Button>
        }
      />

      {saved.length === 0 ? (
        <EmptyState
          title="No saved reports yet"
          description="Use the constrained builder to save a definition and optionally share it with roles."
          action={
            <Button asChild variant="secondary">
              <Link href="/reports/builder">Open builder</Link>
            </Button>
          }
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {saved.map((report) => (
            <Card key={report.id}>
              <CardHeader>
                <CardTitle>{report.name}</CardTitle>
                <CardDescription>
                  {report.description ?? "Saved builder definition"}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2 text-sm text-[var(--muted)]">
                <p>Source: {report.source}</p>
                <p>
                  Shared with:{" "}
                  {report.shares.length
                    ? report.shares.map((share) => share.roleCode).join(", ")
                    : "Only you"}
                </p>
                <p>
                  Schedules:{" "}
                  {report.schedules.length
                    ? report.schedules
                        .map((item) => `${item.cadence}/${item.format}`)
                        .join(", ")
                    : "None"}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
