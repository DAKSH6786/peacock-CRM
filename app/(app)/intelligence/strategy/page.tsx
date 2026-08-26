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
import { prisma } from "@/database";
import { toSessionUser } from "@/lib/session-user";
import { requirePermission } from "@/permissions";

export const metadata: Metadata = {
  title: "90-day strategy",
};

export default async function StrategyPage() {
  const session = await auth();
  const user = toSessionUser(session);
  requirePermission(user, "intelligence:view");

  const plans = await prisma.strategyPlan.findMany({
    where: {
      organizationId: user!.organizationId!,
      deletedAt: null,
    },
    orderBy: { createdAt: "desc" },
    take: 10,
    include: {
      property: { select: { name: true, primaryDomain: true } },
    },
  });

  return (
    <div>
      <PageHeader
        title="90-day strategy"
        description="EXECUTE emits sequenced plans from verified priorities — technical, entity, answer content, authority, then learn."
      />

      <div className="grid gap-4">
        {plans.length === 0 ? (
          <Card>
            <CardHeader>
              <CardTitle>No strategy packs yet</CardTitle>
              <CardDescription>
                Complete a cognitive run through EXECUTE to generate a 90-day
                plan.
              </CardDescription>
            </CardHeader>
          </Card>
        ) : (
          plans.map((plan) => {
            const weeks =
              (plan.weeks as Array<{
                week: number;
                theme: string;
                outcomes: string[];
                workItems: string[];
              }> | null) ?? [];
            return (
              <Card key={plan.id}>
                <CardHeader>
                  <CardTitle>{plan.title}</CardTitle>
                  <CardDescription>
                    {plan.property.name} · {plan.horizonDays} days ·{" "}
                    {plan.status}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="mb-4 text-sm text-[var(--muted)]">
                    {plan.summary}
                  </p>
                  <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                    {weeks.slice(0, 6).map((week) => (
                      <div
                        key={week.week}
                        className="rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] p-3"
                      >
                        <p className="text-xs text-[var(--muted)] uppercase">
                          Week {week.week}
                        </p>
                        <p className="font-medium">{week.theme}</p>
                        <p className="mt-1 text-xs text-[var(--muted)]">
                          {week.outcomes[0]}
                        </p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            );
          })
        )}
      </div>
    </div>
  );
}
