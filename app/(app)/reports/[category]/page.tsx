import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { auth } from "@/auth";
import { PageHeader } from "@/components/shared/page-header";
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
  reportsForCategory,
  type ReportCategory,
} from "@/modules/reports/catalog";
import { requirePermission } from "@/permissions";
import { hasPermission } from "@/permissions/types";
import type { MembershipRole } from "@prisma/client";

type Props = { params: Promise<{ category: string }> };

const VALID: ReportCategory[] = [
  "company",
  "crm",
  "sales",
  "xyme",
  "hr",
  "delivery",
  "finance",
];

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { category } = await params;
  if (!VALID.includes(category as ReportCategory)) return { title: "Reports" };
  return { title: `${categoryLabel(category as ReportCategory)} reports` };
}

export default async function ReportCategoryPage({ params }: Props) {
  const { category: raw } = await params;
  if (!VALID.includes(raw as ReportCategory)) notFound();
  const category = raw as ReportCategory;

  const session = await auth();
  const user = toSessionUser(session);
  requirePermission(user, "reports:view");

  const role = user!.role as MembershipRole | null;
  const items = reportsForCategory(category).filter((item) => {
    if (!hasPermission(role, item.permission)) return false;
    return (item.extraPermissions ?? []).every((permission) =>
      hasPermission(role, permission),
    );
  });

  return (
    <div>
      <PageHeader
        title={`${categoryLabel(category)} reports`}
        description="Select a report to view live database metrics for a date range."
      />
      <div className="grid gap-4 md:grid-cols-2">
        {items.map((item) => (
          <Card key={item.key}>
            <CardHeader>
              <CardTitle>
                <Link
                  href={`/reports/${category}/${item.key.split(".").slice(1).join(".")}`}
                  className="hover:text-[var(--accent-teal)]"
                >
                  {item.title}
                </Link>
              </CardTitle>
              <CardDescription>{item.description}</CardDescription>
            </CardHeader>
            <CardContent className="text-xs text-[var(--muted)]">
              {item.revenueDefinition
                ? `Revenue definition: ${item.revenueDefinition}`
                : "Operational metrics"}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
