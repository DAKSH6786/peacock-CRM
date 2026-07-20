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
import { canAccessExports, canRequestExport, EXPORT_CATALOG } from "@/modules/exports";
import { listExportHistory } from "@/modules/exports/service";
import { ForbiddenError } from "@/permissions";

import { ExportRequestPanel } from "@/components/exports/export-request-panel";

export const metadata: Metadata = {
  title: "Exports",
};

export default async function ExportsPage() {
  const session = await auth();
  const user = toSessionUser(session);
  if (!user || !canAccessExports(user)) {
    throw new ForbiddenError("Missing export access");
  }

  const catalog = EXPORT_CATALOG.filter((item) => canRequestExport(user!, item.key));
  const history = user?.organizationId
    ? await listExportHistory(user.organizationId)
    : [];

  return (
    <div>
      <PageHeader
        title="Exports"
        description="Permission-filtered exports with date ranges, column selection, expiring downloads, and optional approval for sensitive data."
        actions={
          <Button asChild variant="secondary">
            <Link href="/imports">Imports</Link>
          </Button>
        }
      />

      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <ExportRequestPanel catalog={catalog} />

        <Card>
          <CardHeader>
            <CardTitle>Export history</CardTitle>
            <CardDescription>
              Background jobs, approval state, and audit-ready downloads.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {history.length === 0 ? (
              <p className="text-sm text-[var(--muted)]">No exports yet.</p>
            ) : (
              history.map((job) => (
                <div
                  key={job.id}
                  className="border-b border-[var(--border)] pb-3 last:border-0"
                >
                  <div className="flex items-center justify-between gap-2">
                    <p className="font-medium">{job.exportType}</p>
                    <span className="text-xs uppercase text-[var(--muted)]">
                      {job.status}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-[var(--muted)]">
                    by {job.createdBy?.name ?? job.createdBy?.email ?? "unknown"}
                    {job.requiresApproval
                      ? ` · approval ${job.approvedAt ? "granted" : "pending"}`
                      : ""}
                    {job.expiresAt
                      ? ` · expires ${job.expiresAt.toISOString().slice(0, 10)}`
                      : ""}
                  </p>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
