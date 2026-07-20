import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { auth } from "@/auth";
import { HealthBadge } from "@/components/progress/health-badge";
import { PrintReviewButton } from "@/components/progress/print-review-button";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import { toSessionUser } from "@/lib/session-user";
import { getBusinessReview } from "@/modules/progress";
import { requirePermission } from "@/permissions";

type Params = { params: Promise<{ reviewId: string }> };

export async function generateMetadata({ params }: Params): Promise<Metadata> {
  const { reviewId } = await params;
  return { title: `Review ${reviewId.slice(0, 8)}` };
}

type Snapshot = {
  capturedAt?: string;
  objectives?: Array<{
    id: string;
    title: string;
    progressPct: number;
    health: string;
    status: string;
  }>;
  kpis?: Array<{
    id: string;
    name: string;
    code: string;
    latestValue: number | null;
  }>;
  risks?: Array<{
    id: string;
    title: string;
    likelihood: number | null;
    impact: number | null;
    status: string;
  }>;
};

export default async function BusinessReviewDetailPage({ params }: Params) {
  const session = await auth();
  const user = toSessionUser(session);
  requirePermission(user, "progress:view");
  const organizationId = user!.organizationId!;
  const { reviewId } = await params;
  const review = await getBusinessReview(organizationId, reviewId);
  if (!review) notFound();

  const snapshot = (review.snapshot ?? {}) as Snapshot;
  const wins = review.items.filter((i) => i.itemType === "WIN");
  const misses = review.items.filter((i) => i.itemType === "MISS");
  const risks = review.items.filter((i) => i.itemType === "RISK");
  const decisions = review.items.filter((i) => i.itemType === "DECISION");
  const actions = review.items.filter((i) => i.itemType === "ACTION");

  return (
    <div className="review-print">
      <style>{`
        @media print {
          .print\\:hidden { display: none !important; }
          .review-print {
            color: #111 !important;
            background: #fff !important;
          }
          .review-print section {
            break-inside: avoid;
            page-break-inside: avoid;
          }
        }
      `}</style>

      <PageHeader
        title={review.title}
        description={`${review.reviewType} review · ${review.periodStart.toISOString().slice(0, 10)} – ${review.periodEnd.toISOString().slice(0, 10)}`}
        actions={
          <div className="flex gap-2 print:hidden">
            <Button asChild variant="secondary">
              <Link href="/company-progress/reviews">Back</Link>
            </Button>
            <PrintReviewButton />
          </div>
        }
        className="print:mb-4"
      />

      <div className="mb-6 rounded-lg border border-[var(--border)] bg-[var(--surface)] p-6 print:border-black print:bg-white">
        <p className="text-xs uppercase tracking-wide text-[var(--muted)] print:text-neutral-600">
          Snapshot captured{" "}
          {snapshot.capturedAt
            ? new Date(snapshot.capturedAt).toLocaleString()
            : review.createdAt.toLocaleString()}
          {review.createdBy?.name ? ` · by ${review.createdBy.name}` : ""}
        </p>

        {review.summary ? (
          <section className="mt-4">
            <h2 className="mb-2 text-lg font-semibold">Summary</h2>
            <p className="whitespace-pre-wrap text-sm">{review.summary}</p>
          </section>
        ) : null}

        <div className="mt-6 grid gap-6 md:grid-cols-2">
          <section>
            <h2 className="mb-2 text-lg font-semibold">Major wins</h2>
            <p className="whitespace-pre-wrap text-sm">
              {review.majorWins || "—"}
            </p>
            {wins.length > 0 ? (
              <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
                {wins.map((w) => (
                  <li key={w.id}>{w.title}</li>
                ))}
              </ul>
            ) : null}
          </section>
          <section>
            <h2 className="mb-2 text-lg font-semibold">Missed targets</h2>
            <p className="whitespace-pre-wrap text-sm">
              {review.missedTargets || "—"}
            </p>
            {misses.length > 0 ? (
              <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
                {misses.map((m) => (
                  <li key={m.id}>{m.title}</li>
                ))}
              </ul>
            ) : null}
          </section>
        </div>

        <section className="mt-6">
          <h2 className="mb-3 text-lg font-semibold">Objective progress</h2>
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-[var(--border)] print:border-neutral-400">
                <th className="py-2 pr-2 font-medium">Objective</th>
                <th className="py-2 pr-2 font-medium">Status</th>
                <th className="py-2 pr-2 font-medium">Health</th>
                <th className="py-2 font-medium">Progress</th>
              </tr>
            </thead>
            <tbody>
              {(snapshot.objectives ?? []).map((o) => (
                <tr
                  key={o.id}
                  className="border-b border-[var(--border)]/50 print:border-neutral-200"
                >
                  <td className="py-2 pr-2">{o.title}</td>
                  <td className="py-2 pr-2">{o.status}</td>
                  <td className="py-2 pr-2">
                    <HealthBadge health={o.health} />
                  </td>
                  <td className="py-2 tabular-nums">{o.progressPct}%</td>
                </tr>
              ))}
            </tbody>
          </table>
          {(snapshot.objectives ?? []).length === 0 ? (
            <p className="text-sm text-[var(--muted)]">
              No objectives in snapshot.
            </p>
          ) : null}
        </section>

        <section className="mt-6">
          <h2 className="mb-3 text-lg font-semibold">KPI values</h2>
          <div className="grid gap-2 sm:grid-cols-2 md:grid-cols-3">
            {(snapshot.kpis ?? []).map((k) => (
              <div
                key={k.id}
                className="rounded border border-[var(--border)] p-3 text-sm print:border-neutral-300"
              >
                <p className="font-medium">{k.name}</p>
                <p className="text-lg tabular-nums">{k.latestValue ?? "—"}</p>
              </div>
            ))}
          </div>
          {(snapshot.kpis ?? []).length === 0 ? (
            <p className="text-sm text-[var(--muted)]">No KPIs in snapshot.</p>
          ) : null}
        </section>

        <div className="mt-6 grid gap-6 md:grid-cols-3">
          <ItemColumn title="Risks" items={risks} fallback={snapshot.risks} />
          <ItemColumn title="Decisions" items={decisions} />
          <ItemColumn title="Action items" items={actions} showOwner />
        </div>
      </div>
    </div>
  );
}

function ItemColumn({
  title,
  items,
  fallback,
  showOwner,
}: {
  title: string;
  items: Array<{
    id: string;
    title: string;
    body: string | null;
    dueDate: Date | null;
    owner?: { name: string | null } | null;
  }>;
  fallback?: Array<{ id: string; title: string }>;
  showOwner?: boolean;
}) {
  const rows =
    items.length > 0
      ? items
      : (fallback ?? []).map((f) => ({
          id: f.id,
          title: f.title,
          body: null,
          dueDate: null,
          owner: null,
        }));

  return (
    <section>
      <h2 className="mb-2 text-lg font-semibold">{title}</h2>
      <ul className="space-y-2 text-sm">
        {rows.map((item) => (
          <li key={item.id}>
            <p className="font-medium">{item.title}</p>
            {item.body ? (
              <p className="text-[var(--muted)] print:text-neutral-600">
                {item.body}
              </p>
            ) : null}
            {showOwner && item.owner?.name ? (
              <p className="text-xs text-[var(--muted)]">
                Owner: {item.owner.name}
                {item.dueDate
                  ? ` · Due ${item.dueDate.toISOString().slice(0, 10)}`
                  : ""}
              </p>
            ) : item.dueDate ? (
              <p className="text-xs text-[var(--muted)]">
                Due {item.dueDate.toISOString().slice(0, 10)}
              </p>
            ) : null}
          </li>
        ))}
        {rows.length === 0 ? (
          <li className="text-[var(--muted)]">None</li>
        ) : null}
      </ul>
    </section>
  );
}
