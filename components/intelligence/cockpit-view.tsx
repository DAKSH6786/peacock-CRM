import Link from "next/link";

import { PipelineRail } from "@/components/intelligence/pipeline-rail";
import { RunDemoButton } from "@/components/intelligence/run-demo-button";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { PipelineRunResult } from "@/modules/intelligence";
import { DEFAULT_ROLE_PROVIDER } from "@/modules/connectors";

type CockpitViewProps = {
  canRun: boolean;
  propertyId?: string;
  propertyName?: string;
  stats: {
    properties: number;
    runs: number;
    recommendations: number;
    mentionRate?: number;
  };
  recentRuns: Array<{
    id: string;
    status: string;
    summary: string | null;
    confidence: number | null;
    createdAt: Date;
    propertyName: string;
  }>;
  recommendations: Array<{
    id: string;
    kind: string;
    title: string;
    impactScore: number;
    confidence: number;
    status: string;
  }>;
  demoResult?: PipelineRunResult | null;
};

export function CockpitView({
  canRun,
  propertyId,
  propertyName,
  stats,
  recentRuns,
  recommendations,
  demoResult,
}: CockpitViewProps) {
  const completedStages = demoResult
    ? Object.entries(demoResult.stages)
        .filter(([, s]) => s?.status === "SUCCEEDED")
        .map(([name]) => name)
    : [];

  return (
    <div>
      <PageHeader
        title="Generative Visibility Cockpit"
        description="Peacock One runs OBSERVE → THINK → VERIFY → DECIDE → EXECUTE → MEASURE → LEARN — not identical prompts across LLMs."
        actions={
          <>
            <Button asChild variant="secondary">
              <Link href="/intelligence/properties">Properties</Link>
            </Button>
            <Button asChild variant="secondary">
              <Link href="/intelligence/strategy">90-day strategy</Link>
            </Button>
            {canRun ? <RunDemoButton propertyId={propertyId} /> : null}
          </>
        }
      />

      <div className="mb-6">
        <PipelineRail
          active={
            demoResult?.status === "BLOCKED_ON_VERIFY" ? "VERIFY" : "LEARN"
          }
          completed={completedStages}
          blocked={demoResult?.status === "BLOCKED_ON_VERIFY"}
        />
      </div>

      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Metric title="Properties" value={String(stats.properties)} />
        <Metric title="Intelligence runs" value={String(stats.runs)} />
        <Metric title="Recommendations" value={String(stats.recommendations)} />
        <Metric
          title="AI mention rate"
          value={
            stats.mentionRate !== undefined
              ? `${Math.round(stats.mentionRate * 100)}%`
              : "—"
          }
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Multi-layer connector roles</CardTitle>
            <CardDescription>
              Each provider has specialist jobs. Stages request roles, not “ask
              everyone the same thing”.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm">
              {Object.entries(DEFAULT_ROLE_PROVIDER).map(([role, provider]) => (
                <li
                  key={role}
                  className="flex items-center justify-between gap-3 border-b border-[var(--border)] py-2 last:border-0"
                >
                  <span className="font-medium text-[var(--foreground)]">
                    {role}
                  </span>
                  <span className="text-[var(--muted)]">{provider}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent cognitive runs</CardTitle>
            <CardDescription>
              {propertyName
                ? `Primary property: ${propertyName}`
                : "Seed or create a visibility property to persist runs."}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {recentRuns.length === 0 ? (
              <p className="text-sm text-[var(--muted)]">
                No persisted runs yet. Start the cognitive loop to capture stage
                artifacts and connector traces.
              </p>
            ) : (
              <ul className="space-y-3">
                {recentRuns.map((run) => (
                  <li key={run.id}>
                    <Link
                      href={`/intelligence/runs/${run.id}`}
                      className="block rounded-lg border border-[var(--border)] bg-[var(--surface-muted)] p-3 transition hover:border-[var(--primary)]/40"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-medium">{run.propertyName}</span>
                        <span className="text-xs text-[var(--muted)] uppercase">
                          {run.status}
                        </span>
                      </div>
                      <p className="mt-1 line-clamp-2 text-sm text-[var(--muted)]">
                        {run.summary ?? "In progress"}
                      </p>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Top recommendations</CardTitle>
            <CardDescription>
              Decision stage output — ranked by impact × confidence × effort.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {recommendations.length === 0 ? (
              <p className="text-sm text-[var(--muted)]">
                Recommendations appear after a successful DECIDE stage.
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="text-[var(--muted)]">
                    <tr>
                      <th className="pb-2 font-medium">Kind</th>
                      <th className="pb-2 font-medium">Title</th>
                      <th className="pb-2 font-medium">Impact</th>
                      <th className="pb-2 font-medium">Confidence</th>
                      <th className="pb-2 font-medium">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recommendations.map((rec) => (
                      <tr
                        key={rec.id}
                        className="border-t border-[var(--border)]"
                      >
                        <td className="py-2 pr-3 text-[var(--muted)]">
                          {rec.kind}
                        </td>
                        <td className="py-2 pr-3">{rec.title}</td>
                        <td className="py-2 pr-3">
                          {rec.impactScore.toFixed(2)}
                        </td>
                        <td className="py-2 pr-3">
                          {rec.confidence.toFixed(2)}
                        </td>
                        <td className="py-2">{rec.status}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        {demoResult ? (
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Latest loop summary</CardTitle>
              <CardDescription>{demoResult.summary}</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-3">
              <div>
                <p className="text-xs text-[var(--muted)] uppercase">
                  AEO score
                </p>
                <p className="text-2xl font-semibold">
                  {demoResult.observe
                    ? Math.round(demoResult.observe.aeo.score * 100)
                    : "—"}
                </p>
              </div>
              <div>
                <p className="text-xs text-[var(--muted)] uppercase">
                  GEO score
                </p>
                <p className="text-2xl font-semibold">
                  {demoResult.observe
                    ? Math.round(demoResult.observe.geo.score * 100)
                    : "—"}
                </p>
              </div>
              <div>
                <p className="text-xs text-[var(--muted)] uppercase">
                  Visibility mentions
                </p>
                <p className="text-2xl font-semibold">
                  {demoResult.measure
                    ? `${Math.round(demoResult.measure.scorecard.mentionRate * 100)}%`
                    : "—"}
                </p>
              </div>
            </CardContent>
          </Card>
        ) : null}
      </div>
    </div>
  );
}

function Metric({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4 shadow-[var(--shadow-soft)]">
      <p className="text-xs tracking-wide text-[var(--muted)] uppercase">
        {title}
      </p>
      <p className="mt-2 font-[family-name:var(--font-display)] text-3xl font-bold">
        {value}
      </p>
    </div>
  );
}
