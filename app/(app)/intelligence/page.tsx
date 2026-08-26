import type { Metadata } from "next";

import { auth } from "@/auth";
import { CockpitView } from "@/components/intelligence/cockpit-view";
import { toSessionUser } from "@/lib/session-user";
import {
  getIntelligenceOverview,
  runDemoPipeline,
} from "@/modules/intelligence/service";
import { requirePermission } from "@/permissions";
import { hasPermission } from "@/permissions/types";
import type { MembershipRole } from "@prisma/client";

export const metadata: Metadata = {
  title: "Visibility Intelligence",
};

type PageProps = {
  searchParams: Promise<{ demo?: string }>;
};

export default async function IntelligenceCockpitPage({
  searchParams,
}: PageProps) {
  const session = await auth();
  const user = toSessionUser(session);
  requirePermission(user, "intelligence:view");
  const organizationId = user!.organizationId!;
  const canRun = hasPermission(
    user!.role as MembershipRole | null,
    "intelligence:run",
  );

  const overview = await getIntelligenceOverview(organizationId);
  const primary = overview.properties[0];
  const params = await searchParams;
  const demoResult = params.demo === "1" ? await runDemoPipeline() : null;

  const mentionSamples = overview.runs.length
    ? undefined
    : demoResult?.measure?.scorecard.mentionRate;

  return (
    <CockpitView
      canRun={canRun}
      propertyId={primary?.id}
      propertyName={primary?.name}
      stats={{
        properties: overview.properties.length,
        runs: overview.runs.length,
        recommendations: overview.recommendations.length,
        mentionRate: mentionSamples,
      }}
      recentRuns={overview.runs.map((run) => ({
        id: run.id,
        status: run.status,
        summary: run.summary,
        confidence: run.confidence,
        createdAt: run.createdAt,
        propertyName: run.property.name,
      }))}
      recommendations={overview.recommendations.map((rec) => ({
        id: rec.id,
        kind: rec.kind,
        title: rec.title,
        impactScore: rec.impactScore,
        confidence: rec.confidence,
        status: rec.status,
      }))}
      demoResult={demoResult}
    />
  );
}
