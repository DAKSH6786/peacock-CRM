import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { auth } from "@/auth";
import { PipelineRail } from "@/components/intelligence/pipeline-rail";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
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
  title: "Intelligence run",
};

type PageProps = {
  params: Promise<{ id: string }>;
};

export default async function IntelligenceRunPage({ params }: PageProps) {
  const session = await auth();
  const user = toSessionUser(session);
  requirePermission(user, "intelligence:view");
  const { id } = await params;

  const run = await prisma.intelligenceRun.findFirst({
    where: { id, organizationId: user!.organizationId! },
    include: {
      property: true,
      stages: { orderBy: { createdAt: "asc" } },
      providerTraces: { orderBy: { createdAt: "asc" } },
      recommendations: true,
      strategyPlans: true,
    },
  });

  if (!run) notFound();

  const completed = run.stages
    .filter((s) => s.status === "SUCCEEDED")
    .map((s) => s.stage);

  return (
    <div>
      <PageHeader
        title={run.property.name}
        description={run.summary ?? `Status: ${run.status}`}
        actions={
          <Button asChild variant="secondary">
            <Link href="/intelligence">Cockpit</Link>
          </Button>
        }
      />

      <div className="mb-6">
        <PipelineRail
          active={run.currentStage}
          completed={completed}
          blocked={run.status === "BLOCKED_ON_VERIFY"}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Stage results</CardTitle>
            <CardDescription>
              Confidence {run.confidence?.toFixed(2) ?? "—"}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {run.stages.map((stage) => (
              <div
                key={stage.id}
                className="rounded-lg border border-[var(--border)] p-3"
              >
                <div className="flex justify-between gap-2 text-sm">
                  <span className="font-semibold">{stage.stage}</span>
                  <span className="text-[var(--muted)]">{stage.status}</span>
                </div>
                <p className="mt-1 text-xs text-[var(--muted)]">
                  confidence {stage.confidence?.toFixed(2) ?? "—"}
                </p>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Connector traces</CardTitle>
            <CardDescription>
              Role-bound calls with prompt hashes (not secret payloads)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm">
              {run.providerTraces.map((trace) => (
                <li
                  key={trace.id}
                  className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--border)] py-2"
                >
                  <span>
                    {trace.stage} · {trace.role}
                  </span>
                  <span className="text-[var(--muted)]">
                    {trace.provider} · {trace.promptHash}
                  </span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Decided recommendations</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm">
              {run.recommendations.map((rec) => (
                <li
                  key={rec.id}
                  className="border-b border-[var(--border)] py-2"
                >
                  <span className="font-medium">
                    [{rec.kind}] {rec.title}
                  </span>
                  <p className="text-[var(--muted)]">{rec.summary}</p>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
