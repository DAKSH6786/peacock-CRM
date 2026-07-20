import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { auth } from "@/auth";
import { HealthBadge, ProgressBar } from "@/components/progress/health-badge";
import {
  KeyResultPanel,
  KeyResultUpdateForm,
} from "@/components/progress/key-result-panel";
import {
  HealthOverrideForm,
  ProgressUpdateForm,
} from "@/components/progress/progress-update-form";
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
import { getObjectiveDetail } from "@/modules/progress";
import { requirePermission } from "@/permissions";
import { hasPermission } from "@/permissions/types";
import type { MembershipRole } from "@prisma/client";

type Params = { params: Promise<{ objectiveId: string }> };

export async function generateMetadata({ params }: Params): Promise<Metadata> {
  const { objectiveId } = await params;
  return { title: `Objective ${objectiveId.slice(0, 8)}` };
}

export default async function ObjectiveDetailPage({ params }: Params) {
  const session = await auth();
  const user = toSessionUser(session);
  requirePermission(user, "progress:view");
  const organizationId = user!.organizationId!;
  const canManage = hasPermission(
    user!.role as MembershipRole | null,
    "progress:manage",
  );
  const { objectiveId } = await params;
  const objective = await getObjectiveDetail(organizationId, objectiveId);
  if (!objective) notFound();

  return (
    <div>
      <PageHeader
        title={objective.title}
        description={objective.description ?? undefined}
        actions={
          <Button asChild variant="secondary">
            <Link href="/company-progress/objectives">Back</Link>
          </Button>
        }
      />

      <div className="mb-6 grid gap-4 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Progress</CardDescription>
            <CardTitle className="text-2xl">{objective.progressPct}%</CardTitle>
          </CardHeader>
          <CardContent>
            <ProgressBar value={objective.progressPct} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Health</CardDescription>
            <CardTitle>
              <HealthBadge health={objective.health} />
            </CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-[var(--muted)]">
            {objective.healthOverridden
              ? `Override: ${objective.healthOverrideReason}`
              : "Calculated from rules"}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Level</CardDescription>
            <CardTitle className="text-lg">{objective.scope}</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-[var(--muted)]">
            Priority {objective.priority}
            {objective.quarter ? ` · ${objective.quarter}` : ""}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Owner</CardDescription>
            <CardTitle className="text-lg">
              {objective.primaryOwner?.name ?? "Unassigned"}
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-[var(--muted)]">
            {objective.department?.name ?? "Company-wide"}
          </CardContent>
        </Card>
      </div>

      <div className="mb-6 grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Alignment</CardTitle>
            <CardDescription>Parent and child objectives</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div>
              <p className="text-[var(--muted)]">Parent</p>
              {objective.parent ? (
                <Link
                  href={`/company-progress/objectives/${objective.parent.id}`}
                  className="font-medium hover:underline"
                >
                  [{objective.parent.scope}] {objective.parent.title}
                </Link>
              ) : (
                <p>None (top-level)</p>
              )}
            </div>
            <div>
              <p className="mb-1 text-[var(--muted)]">Children</p>
              {objective.children.length === 0 ? (
                <p>No linked child objectives</p>
              ) : (
                <ul className="space-y-1">
                  {objective.children.map((c) => (
                    <li key={c.id}>
                      <Link
                        href={`/company-progress/objectives/${c.id}`}
                        className="hover:underline"
                      >
                        [{c.scope}] {c.title}
                      </Link>{" "}
                      <span className="text-[var(--muted)]">
                        {c.progressPct}%
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            {objective.tags.length > 0 ? (
              <p className="text-[var(--muted)]">
                Tags: {objective.tags.join(", ")}
              </p>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Contributors</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {objective.owners.map((o) => (
              <div key={o.id} className="flex justify-between">
                <span>{o.user?.name ?? o.user?.email ?? "—"}</span>
                <span className="text-[var(--muted)]">{o.role}</span>
              </div>
            ))}
            {objective.owners.length === 0 ? (
              <p className="text-[var(--muted)]">No contributors listed</p>
            ) : null}
          </CardContent>
        </Card>
      </div>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Key results</CardTitle>
          <CardDescription>
            Updates append to history — progress is never silently overwritten
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {objective.keyResults.map((kr) => (
            <div
              key={kr.id}
              className="rounded-lg border border-[var(--border)] p-4"
            >
              <div className="mb-2 flex flex-wrap items-start justify-between gap-2">
                <div>
                  <h3 className="font-semibold">{kr.title}</h3>
                  <p className="text-xs text-[var(--muted)]">
                    {kr.metricType}
                    {kr.unit ? ` · ${kr.unit}` : ""} · {kr.updateFrequency} ·
                    Owner {kr.owner?.name ?? "—"}
                    {kr.confidenceScore != null
                      ? ` · Confidence ${kr.confidenceScore}`
                      : ""}
                  </p>
                </div>
                <div className="text-right text-sm">
                  <p className="tabular-nums font-medium">{kr.progressPct}%</p>
                  <p className="text-[var(--muted)]">
                    {kr.currentValue != null ? String(kr.currentValue) : "—"} /{" "}
                    {kr.target != null ? String(kr.target) : "—"}
                  </p>
                </div>
              </div>
              <ProgressBar value={kr.progressPct} className="mb-3" />
              {kr.evidence ? (
                <p className="mb-2 text-xs text-[var(--muted)]">
                  Evidence: {kr.evidence}
                </p>
              ) : null}
              <KeyResultUpdateForm
                keyResultId={kr.id}
                canManage={canManage}
              />
              {kr.updates.length > 0 ? (
                <div className="mt-3 border-t border-[var(--border)] pt-3">
                  <p className="mb-2 text-xs font-medium uppercase tracking-wide text-[var(--muted)]">
                    Update history
                  </p>
                  <ul className="space-y-1 text-xs">
                    {kr.updates.map((u) => (
                      <li key={u.id} className="flex justify-between gap-4">
                        <span>
                          {u.previousValue != null
                            ? String(u.previousValue)
                            : "—"}{" "}
                          → {String(u.newValue)}
                          {u.note ? ` · ${u.note}` : ""}
                        </span>
                        <span className="shrink-0 text-[var(--muted)]">
                          {u.createdAt.toISOString().slice(0, 10)}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}
              {kr.comments.length > 0 ? (
                <div className="mt-2 text-xs text-[var(--muted)]">
                  {kr.comments.length} comment
                  {kr.comments.length === 1 ? "" : "s"}
                </div>
              ) : null}
            </div>
          ))}
          {objective.keyResults.length === 0 ? (
            <p className="text-sm text-[var(--muted)]">No key results yet.</p>
          ) : null}
          <KeyResultPanel objectiveId={objective.id} canManage={canManage} />
        </CardContent>
      </Card>

      <div className="mb-6 grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Milestones & initiatives</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2 text-sm">
            <div>
              <p className="mb-2 font-medium">Milestones</p>
              <ul className="space-y-1">
                {objective.milestones.map((m) => (
                  <li key={m.id}>
                    {m.title}{" "}
                    <span className="text-[var(--muted)]">{m.status}</span>
                  </li>
                ))}
                {objective.milestones.length === 0 ? (
                  <li className="text-[var(--muted)]">None</li>
                ) : null}
              </ul>
            </div>
            <div>
              <p className="mb-2 font-medium">Initiatives</p>
              <ul className="space-y-1">
                {objective.initiatives.map((i) => (
                  <li key={i.id}>
                    {i.title}{" "}
                    <span className="text-[var(--muted)]">{i.status}</span>
                  </li>
                ))}
                {objective.initiatives.length === 0 ? (
                  <li className="text-[var(--muted)]">None</li>
                ) : null}
              </ul>
            </div>
          </CardContent>
        </Card>

        <HealthOverrideForm objectiveId={objective.id} canManage={canManage} />
      </div>

      <div className="mb-6 space-y-4">
        <ProgressUpdateForm
          objectiveId={objective.id}
          canManage={canManage}
        />
        <Card>
          <CardHeader>
            <CardTitle>Progress history</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {objective.progressUpdates.map((u) => (
              <div
                key={u.id}
                className="rounded-md border border-[var(--border)] p-3"
              >
                <div className="mb-1 flex flex-wrap justify-between gap-2">
                  <span className="font-medium">
                    {u.cadence} · {u.reviewStatus}
                  </span>
                  <span className="text-[var(--muted)]">
                    {u.periodStart.toISOString().slice(0, 10)} –{" "}
                    {u.periodEnd.toISOString().slice(0, 10)}
                  </span>
                </div>
                <p>{u.body}</p>
                {u.blocker ? (
                  <p className="mt-1 text-rose-700">Blocker: {u.blocker}</p>
                ) : null}
                {u.riskFlag ? (
                  <p className="mt-1 text-amber-700">Risk flagged</p>
                ) : null}
              </div>
            ))}
            {objective.progressUpdates.length === 0 ? (
              <p className="text-[var(--muted)]">No updates yet.</p>
            ) : null}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
