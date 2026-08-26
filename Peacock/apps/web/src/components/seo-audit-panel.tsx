"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api";

type ScoreResult = {
  code: string;
  label: string;
  score: number;
  confidence: number;
  inputs_used: string[];
  major_positive_factors: string[];
  major_negative_factors: string[];
  recommended_actions: string[];
};

type Finding = {
  code: string;
  severity: string;
  title: string;
  description: string;
  category: string;
  page_urls: string[];
};

type Recommendation = {
  code: string;
  title: string;
  priority: string;
  impact: number;
  effort: number;
  confidence: number;
  affected_pages: string[];
  reason: string;
  suggested_fix: string;
  priority_score: number;
};

type PageIssue = {
  url: string;
  issues: string[];
  severities: string[];
};

type SeoAudit = {
  id: string;
  title: string;
  summary: string;
  peacock_seo_score: ScoreResult;
  scores: Record<string, ScoreResult>;
  critical_issues: Finding[];
  warnings: Finding[];
  opportunities: Finding[];
  recommendations: Recommendation[];
  page_issues: PageIssue[];
  interpretation?: string | null;
};

function ScoreCard({ score }: { score: ScoreResult }) {
  return (
    <div className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--background)]/40 p-4">
      <div className="flex items-baseline justify-between gap-3">
        <h3 className="text-sm font-semibold" style={{ fontFamily: "var(--font-display)" }}>
          {score.label}
        </h3>
        <p className="text-2xl font-semibold">{score.score}</p>
      </div>
      <p className="mt-1 text-xs text-[var(--muted)]">
        Confidence {(score.confidence * 100).toFixed(0)}%
      </p>
      {score.major_negative_factors[0] ? (
        <p className="mt-3 text-sm text-[var(--danger)]">{score.major_negative_factors[0]}</p>
      ) : score.major_positive_factors[0] ? (
        <p className="mt-3 text-sm text-[var(--primary)]">{score.major_positive_factors[0]}</p>
      ) : null}
    </div>
  );
}

function FindingList({ title, items }: { title: string; items: Finding[] }) {
  return (
    <div>
      <h3 className="text-lg font-semibold" style={{ fontFamily: "var(--font-display)" }}>
        {title}
      </h3>
      {items.length === 0 ? (
        <p className="mt-2 text-sm text-[var(--muted)]">None</p>
      ) : (
        <ul className="mt-3 space-y-3">
          {items.map((item) => (
            <li key={`${item.code}-${item.title}`} className="border-b border-[var(--border)] pb-3">
              <p className="font-medium">{item.title}</p>
              <p className="mt-1 text-sm text-[var(--muted)]">{item.description}</p>
              {item.page_urls.length ? (
                <p className="mt-1 text-xs text-[var(--muted)]">
                  {item.page_urls.length} page(s) · {item.page_urls[0]}
                </p>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function SeoAuditPanel({ crawlId }: { crawlId: string | null }) {
  const [auditId, setAuditId] = useState<string | null>(null);
  const [tab, setTab] = useState<"overview" | "issues" | "pages" | "recommendations">("overview");
  const [error, setError] = useState<string | null>(null);

  const run = useMutation({
    mutationFn: () =>
      apiFetch<SeoAudit>("/seo/audits", {
        method: "POST",
        body: JSON.stringify({
          crawl_id: crawlId,
          fetch_connectors: true,
          persist: true,
        }),
      }),
    onSuccess: (data) => {
      setError(null);
      setAuditId(data.id);
      setTab("overview");
    },
    onError: (err: Error) => setError(err.message),
  });

  const audit = useQuery({
    queryKey: ["seo-audit", auditId],
    enabled: Boolean(auditId),
    queryFn: () => apiFetch<SeoAudit>(`/seo/audits/${auditId}/overview`),
    initialData: run.data,
  });

  const sectionScores = useMemo(
    () => Object.values(audit.data?.scores ?? {}),
    [audit.data?.scores],
  );

  return (
    <section className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--surface)] p-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.2em] text-[var(--muted)]">Peacock SEO Engine</p>
          <h2 className="mt-1 text-2xl font-semibold" style={{ fontFamily: "var(--font-display)" }}>
            Audit overview
          </h2>
          <p className="mt-2 max-w-2xl text-sm text-[var(--muted)]">
            Deterministic scoring from crawl data. PageSpeed, CWV, Search Console, and Analytics use
            mock adapters locally — they never invent the Peacock SEO Score.
          </p>
        </div>
        <Button
          type="button"
          disabled={!crawlId || run.isPending}
          onClick={() => run.mutate()}
        >
          {run.isPending ? "Auditing…" : "Run SEO audit"}
        </Button>
      </div>

      {!crawlId ? (
        <p className="mt-4 text-sm text-[var(--muted)]">Complete a crawl first, then run the audit.</p>
      ) : (
        <p className="mt-4 text-xs text-[var(--muted)]">Crawl · {crawlId}</p>
      )}
      {error ? <p className="mt-3 text-sm text-[var(--danger)]">{error}</p> : null}

      {audit.data ? (
        <div className="mt-8 space-y-8">
          <div className="rounded-[var(--radius)] border border-[var(--border)] p-5">
            <p className="text-sm text-[var(--muted)]">Peacock SEO Score</p>
            <p className="mt-1 text-5xl font-semibold" style={{ fontFamily: "var(--font-display)" }}>
              {audit.data.peacock_seo_score.score}
            </p>
            <p className="mt-2 text-sm text-[var(--muted)]">{audit.data.summary}</p>
          </div>

          <div className="flex flex-wrap gap-2">
            {(
              [
                ["overview", "Audit Overview"],
                ["issues", "Issues"],
                ["pages", "Page-level Issues"],
                ["recommendations", "Recommendations"],
              ] as const
            ).map(([id, label]) => (
              <Button
                key={id}
                type="button"
                variant={tab === id ? "default" : "secondary"}
                size="sm"
                onClick={() => setTab(id)}
              >
                {label}
              </Button>
            ))}
          </div>

          {tab === "overview" ? (
            <div className="space-y-6">
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {sectionScores.map((score) => (
                  <ScoreCard key={score.code} score={score} />
                ))}
              </div>
              {audit.data.interpretation ? (
                <p className="text-sm text-[var(--muted)]">{audit.data.interpretation}</p>
              ) : null}
            </div>
          ) : null}

          {tab === "issues" ? (
            <div className="grid gap-8 lg:grid-cols-3">
              <FindingList title="Critical Issues" items={audit.data.critical_issues} />
              <FindingList title="Warnings" items={audit.data.warnings} />
              <FindingList title="Opportunities" items={audit.data.opportunities} />
            </div>
          ) : null}

          {tab === "pages" ? (
            <div>
              <h3 className="text-lg font-semibold" style={{ fontFamily: "var(--font-display)" }}>
                Page-level Issues
              </h3>
              <ul className="mt-4 space-y-4">
                {audit.data.page_issues.map((page) => (
                  <li key={page.url} className="border-b border-[var(--border)] pb-3">
                    <p className="font-medium break-all">{page.url}</p>
                    <p className="mt-1 text-sm text-[var(--muted)]">{page.issues.join(" · ")}</p>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {tab === "recommendations" ? (
            <div>
              <h3 className="text-lg font-semibold" style={{ fontFamily: "var(--font-display)" }}>
                Recommendations
              </h3>
              <ul className="mt-4 space-y-5">
                {audit.data.recommendations.map((rec) => (
                  <li key={rec.code} className="rounded-[var(--radius)] border border-[var(--border)] p-4">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <p className="font-semibold">{rec.title}</p>
                      <p className="text-xs uppercase tracking-[0.14em] text-[var(--muted)]">
                        {rec.priority} · impact {rec.impact} · effort {rec.effort} · conf{" "}
                        {rec.confidence}
                      </p>
                    </div>
                    <p className="mt-2 text-sm text-[var(--muted)]">{rec.reason}</p>
                    <p className="mt-2 text-sm">
                      <span className="text-[var(--muted)]">Suggested fix · </span>
                      {rec.suggested_fix}
                    </p>
                    <p className="mt-2 text-xs text-[var(--muted)]">
                      Affected pages · {rec.affected_pages.slice(0, 3).join(", ") || "n/a"}
                      {rec.affected_pages.length > 3 ? ` +${rec.affected_pages.length - 3}` : ""}
                    </p>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
