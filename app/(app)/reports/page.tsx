import type { Metadata } from "next";
import Link from "next/link";

import { auth } from "@/auth";
import { ReportCategoryNav } from "@/components/reports/report-controls";
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
import {
  categoryLabel,
  visibleCatalog,
  type ReportCategory,
} from "@/modules/reports/catalog";
import { requirePermission } from "@/permissions";
import { hasPermission } from "@/permissions/types";
import type { MembershipRole } from "@prisma/client";

export const metadata: Metadata = {
  title: "Reports",
};

const CATEGORIES: ReportCategory[] = [
  "company",
  "crm",
  "sales",
  "xyme",
  "hr",
  "delivery",
  "finance",
];

export default async function ReportsPage() {
  const session = await auth();
  const user = toSessionUser(session);
  requirePermission(user, "reports:view");

  const role = user!.role as MembershipRole | null;
  const catalog = visibleCatalog((permission) => hasPermission(role, permission));

  const byCategory = CATEGORIES.map((category) => ({
    id: category,
    label: categoryLabel(category),
    count: catalog.filter((item) => item.category === category).length,
    items: catalog.filter((item) => item.category === category),
  })).filter((group) => group.count > 0);

  return (
    <div>
      <PageHeader
        title="Reports & analytics"
        description="Permission-aware operating reports with explicit revenue definitions, date ranges, and export controls."
        actions={
          <>
            <Button asChild variant="secondary">
              <Link href="/reports/saved">Saved reports</Link>
            </Button>
            <Button asChild>
              <Link href="/reports/builder">Report builder</Link>
            </Button>
          </>
        }
      />

      <div className="mb-6">
        <ReportCategoryNav
          categories={byCategory.map(({ id, label, count }) => ({
            id,
            label,
            count,
          }))}
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        {byCategory.map((group) => (
          <Card key={group.id}>
            <CardHeader>
              <CardTitle>{group.label}</CardTitle>
              <CardDescription>
                {group.count} report{group.count === 1 ? "" : "s"} available for your role.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {group.items.map((item) => (
                  <li key={item.key}>
                    <Link
                      href={`/reports/${group.id}/${item.key.split(".").slice(1).join(".")}`}
                      className="text-sm font-semibold text-[var(--accent-teal)] hover:underline"
                    >
                      {item.title}
                    </Link>
                    <p className="text-xs text-[var(--muted)]">{item.description}</p>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
