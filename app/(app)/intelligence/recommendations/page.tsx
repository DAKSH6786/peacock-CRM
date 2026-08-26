import type { Metadata } from "next";

import { auth } from "@/auth";
import { PageHeader } from "@/components/shared/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { prisma } from "@/database";
import { toSessionUser } from "@/lib/session-user";
import { requirePermission } from "@/permissions";

export const metadata: Metadata = {
  title: "Recommendations",
};

export default async function RecommendationsPage() {
  const session = await auth();
  const user = toSessionUser(session);
  requirePermission(user, "intelligence:view");

  const recommendations = await prisma.recommendation.findMany({
    where: { organizationId: user!.organizationId!, deletedAt: null },
    orderBy: [{ impactScore: "desc" }, { createdAt: "desc" }],
    take: 50,
    include: {
      property: { select: { name: true } },
    },
  });

  return (
    <div>
      <PageHeader
        title="Recommendations"
        description="DECIDE output grounded in OBSERVE evidence and VERIFY consensus — ready for EXECUTE work products."
      />

      <Card>
        <CardHeader>
          <CardTitle>Ranked actions</CardTitle>
        </CardHeader>
        <CardContent>
          {recommendations.length === 0 ? (
            <p className="text-sm text-[var(--muted)]">
              No recommendations yet.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-[var(--muted)]">
                  <tr>
                    <th className="pb-2">Property</th>
                    <th className="pb-2">Kind</th>
                    <th className="pb-2">Title</th>
                    <th className="pb-2">Impact</th>
                    <th className="pb-2">Effort</th>
                    <th className="pb-2">Confidence</th>
                    <th className="pb-2">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {recommendations.map((rec) => (
                    <tr
                      key={rec.id}
                      className="border-t border-[var(--border)]"
                    >
                      <td className="py-2 pr-3">{rec.property.name}</td>
                      <td className="py-2 pr-3">{rec.kind}</td>
                      <td className="py-2 pr-3">
                        <div className="font-medium">{rec.title}</div>
                        <div className="text-[var(--muted)]">{rec.summary}</div>
                      </td>
                      <td className="py-2 pr-3">
                        {rec.impactScore.toFixed(2)}
                      </td>
                      <td className="py-2 pr-3">
                        {rec.effortScore.toFixed(2)}
                      </td>
                      <td className="py-2 pr-3">{rec.confidence.toFixed(2)}</td>
                      <td className="py-2">{rec.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
