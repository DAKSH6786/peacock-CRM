import type { Metadata } from "next";
import Link from "next/link";

import { auth } from "@/auth";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { toSessionUser } from "@/lib/session-user";
import { getSalespersonWorkload } from "@/modules/crm";
import { requirePermission } from "@/permissions";

export const metadata: Metadata = {
  title: "Sales workload",
};

export default async function WorkloadPage() {
  const session = await auth();
  const user = toSessionUser(session);
  requirePermission(user, "crm:view");
  const workload = await getSalespersonWorkload(user!.organizationId!);

  return (
    <div>
      <PageHeader
        title="Salesperson workload"
        description="Open leads, overdue follow-ups, and pipeline value by owner."
        actions={
          <Button asChild variant="secondary">
            <Link href="/crm">CRM hub</Link>
          </Button>
        }
      />
      <Card>
        <CardHeader>
          <CardTitle>Owners</CardTitle>
        </CardHeader>
        <CardContent>
          <table className="min-w-full text-left text-sm">
            <thead className="text-xs uppercase text-[var(--muted)]">
              <tr>
                <th className="py-2">Salesperson</th>
                <th className="py-2">Open leads</th>
                <th className="py-2">Overdue follow-ups</th>
                <th className="py-2">Pipeline value</th>
              </tr>
            </thead>
            <tbody>
              {workload.map((row) => (
                <tr key={row.userId} className="border-t border-[var(--border)]">
                  <td className="py-2">
                    <div>{row.name}</div>
                    <div className="text-xs text-[var(--muted)]">{row.email}</div>
                  </td>
                  <td className="py-2">{row.openLeads}</td>
                  <td className="py-2">{row.overdueFollowUps}</td>
                  <td className="py-2">
                    {(row.pipelineValueMinor / 100).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {workload.length === 0 ? (
            <p className="text-sm text-[var(--muted)]">No workload data.</p>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}
