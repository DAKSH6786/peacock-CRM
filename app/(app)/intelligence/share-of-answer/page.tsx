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
import { toSessionUser } from "@/lib/session-user";
import {
  aggregateBrandScores,
  shareOfAnswerCatalog,
  type EntityIndicatorReading,
} from "@/modules/share-of-answer";
import { requirePermission } from "@/permissions";

export const metadata: Metadata = {
  title: "Share of Answer",
};

const ENTERPRISE_CRM_OBS: EntityIndicatorReading[][] = [
  [
    {
      entityName: "Brand A",
      mention: true,
      position: 1,
      recommendationStrength: 0.9,
      answerSpace: 0.35,
      citationOwnership: 0.7,
      semanticProminence: 0.8,
      positiveClaims: 5,
      negativeClaims: 0,
      neutralClaims: 1,
      comparisonOutcome: "win",
      tokenSpanRatio: 0.25,
    },
    {
      entityName: "Brand B",
      mention: true,
      position: 2,
      recommendationStrength: 0.75,
      answerSpace: 0.3,
      citationOwnership: 0.55,
      semanticProminence: 0.65,
      positiveClaims: 3,
      negativeClaims: 1,
      neutralClaims: 1,
      comparisonOutcome: "tie",
      tokenSpanRatio: 0.4,
    },
    {
      entityName: "Client",
      isClient: true,
      mention: true,
      position: 4,
      recommendationStrength: 0.35,
      answerSpace: 0.12,
      citationOwnership: 0.2,
      semanticProminence: 0.3,
      positiveClaims: 1,
      negativeClaims: 1,
      neutralClaims: 2,
      comparisonOutcome: "lose",
      tokenSpanRatio: 0.35,
    },
  ],
];

export default async function ShareOfAnswerPage() {
  const session = await auth();
  const user = toSessionUser(session);
  requirePermission(user, "intelligence:view");

  const catalog = shareOfAnswerCatalog();
  const brands = aggregateBrandScores(ENTERPRISE_CRM_OBS);

  return (
    <div>
      <PageHeader
        title="Share of Answer"
        description="How much of a generative answer is controlled by or favourable to each brand — multi-indicator influence, never token count alone."
      />

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Query cluster: Enterprise CRM</CardTitle>
          <CardDescription>
            Methodology: {catalog.methodologyNote}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {brands.map((b) => (
              <div key={b.entityName}>
                <div className="mb-1 flex items-baseline justify-between gap-4">
                  <span className="font-medium">
                    {b.entityName}
                    {b.isClient ? " (Client)" : ""}
                  </span>
                  <span className="text-2xl font-bold tabular-nums">
                    {b.shareOfAnswer.toFixed(0)}%
                  </span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-[var(--muted)]/20">
                  <div
                    className="h-full rounded-full bg-[var(--accent)]"
                    style={{ width: `${Math.min(100, b.shareOfAnswer)}%` }}
                  />
                </div>
                <p className="mt-1 text-xs text-[var(--muted)]">
                  Token-only share {b.tokenOnlyShare.toFixed(0)}% · gap{" "}
                  {b.tokenVsInfluenceGap.toFixed(1)} pp · mention{" "}
                  {(b.mentionRate * 100).toFixed(0)}% · rec strength{" "}
                  {(b.avgRecommendationStrength * 100).toFixed(0)}%
                </p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Indicators</CardTitle>
          <CardDescription>
            Token span is diagnostic only and cannot be the sole methodology.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2 text-sm">
          {catalog.indicators.map((i) => (
            <span
              key={i}
              className="rounded-md border border-[var(--border)] px-2 py-1"
            >
              {i.replace(/_/g, " ")}
            </span>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
