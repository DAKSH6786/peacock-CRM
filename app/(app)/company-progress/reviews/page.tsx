import type { Metadata } from "next";
import Link from "next/link";

import { auth } from "@/auth";
import { BusinessReviewCreateForm } from "@/components/progress/business-review-form";
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
import { listBusinessReviews } from "@/modules/progress";
import { requirePermission } from "@/permissions";
import { hasPermission } from "@/permissions/types";
import type { MembershipRole } from "@prisma/client";

export const metadata: Metadata = {
  title: "Business reviews",
};

export default async function BusinessReviewsPage() {
  const session = await auth();
  const user = toSessionUser(session);
  requirePermission(user, "progress:view");
  const organizationId = user!.organizationId!;
  const canManage = hasPermission(
    user!.role as MembershipRole | null,
    "progress:manage",
  );

  const reviews = await listBusinessReviews(organizationId);

  return (
    <div>
      <PageHeader
        title="Business reviews"
        description="Monthly and quarterly reviews with frozen KPI and objective snapshots. Print-friendly and PDF-ready."
        actions={
          <Button asChild variant="secondary">
            <Link href="/company-progress">Dashboard</Link>
          </Button>
        }
      />

      <div className="mb-6">
        <BusinessReviewCreateForm canManage={canManage} />
      </div>

      <div className="space-y-3">
        {reviews.map((review) => (
          <Card key={review.id}>
            <CardHeader className="flex flex-row items-start justify-between gap-4 space-y-0">
              <div>
                <CardTitle>
                  <Link
                    href={`/company-progress/reviews/${review.id}`}
                    className="hover:underline"
                  >
                    {review.title}
                  </Link>
                </CardTitle>
                <CardDescription>
                  {review.reviewType} ·{" "}
                  {review.periodStart.toISOString().slice(0, 10)} –{" "}
                  {review.periodEnd.toISOString().slice(0, 10)} ·{" "}
                  {review._count.items} items
                </CardDescription>
              </div>
              <Button asChild size="sm" variant="secondary">
                <Link href={`/company-progress/reviews/${review.id}`}>
                  Open
                </Link>
              </Button>
            </CardHeader>
            {review.summary ? (
              <CardContent>
                <p className="line-clamp-2 text-sm text-[var(--muted)]">
                  {review.summary}
                </p>
              </CardContent>
            ) : null}
          </Card>
        ))}
        {reviews.length === 0 ? (
          <p className="text-sm text-[var(--muted)]">No reviews yet.</p>
        ) : null}
      </div>
    </div>
  );
}
