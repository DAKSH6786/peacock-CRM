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
import { IMPORT_CATALOG } from "@/modules/imports";
import { listImportHistory } from "@/modules/imports/service";
import { requirePermission } from "@/permissions";
import { hasPermission } from "@/permissions/types";
import type { MembershipRole } from "@prisma/client";

import { ImportWorkflowPanel } from "@/components/imports/import-workflow-panel";

export const metadata: Metadata = {
  title: "Imports",
};

export default async function ImportsPage() {
  const session = await auth();
  const user = toSessionUser(session);
  requirePermission(user, "imports:run");

  const role = user!.role as MembershipRole | null;
  const catalog = IMPORT_CATALOG.filter((item) =>
    hasPermission(role, item.permission),
  );
  const history = user?.organizationId
    ? await listImportHistory(user.organizationId)
    : [];

  return (
    <div>
      <PageHeader
        title="CSV imports"
        description="Template download, column mapping, validation, duplicate detection, and background processing with audit history."
        actions={
          <Button asChild variant="secondary">
            <Link href="/exports">Exports</Link>
          </Button>
        }
      />

      <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <ImportWorkflowPanel catalog={catalog} />

        <Card>
          <CardHeader>
            <CardTitle>Import history</CardTitle>
            <CardDescription>
              Recent jobs with imported-by attribution and error files.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {history.length === 0 ? (
              <p className="text-sm text-[var(--muted)]">No imports yet.</p>
            ) : (
              history.map((job) => (
                <div
                  key={job.id}
                  className="border-b border-[var(--border)] pb-3 last:border-0"
                >
                  <div className="flex items-center justify-between gap-2">
                    <p className="font-medium">{job.entityType}</p>
                    <span className="text-xs uppercase tracking-wide text-[var(--muted)]">
                      {job.status}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-[var(--muted)]">
                    {job.successRows}/{job.totalRows} ok · by{" "}
                    {job.createdBy?.name ?? job.createdBy?.email ?? "unknown"} ·{" "}
                    {job.createdAt.toISOString().slice(0, 10)}
                  </p>
                  {job.errorFileKey ? (
                    <form action={`/api/imports/${job.id}`} method="post">
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="mt-1 px-0"
                        asChild
                      >
                        <Link href={`/api/imports/${job.id}`}>View job</Link>
                      </Button>
                    </form>
                  ) : null}
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
