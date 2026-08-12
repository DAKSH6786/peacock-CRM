"use client";

import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api";
import { useAuthStore } from "@/stores/auth";

type LayerResult = {
  layer: number;
  name: string;
  status: string;
  summary: string;
};

type StrategicRun = {
  id: string;
  status: string;
  classification: {
    user_intent: string;
    requested_output: string;
    importance: string;
    business_risk: string;
    freshness_requirement: string;
    required_data: string[];
    thinking_depth: string;
  };
  layers: LayerResult[];
  recommendations: Array<{
    title: string;
    priority: string;
    impact: number;
    effort: number;
    confidence: number;
    priority_score: number;
    rationale: string;
    depends_on_inference: boolean;
  }>;
  tasks: Array<{ title: string; owner_role: string; priority: string }>;
  evidence_summary: Record<string, number>;
  context_summary: {
    selected_kinds: string[];
    rejected_kinds: string[];
    tokens_used: number;
    token_budget: number;
  };
  interpretation?: string | null;
};

export function StrategicIntelligencePanel() {
  const { accessToken, workspaceId } = useAuthStore();
  const [requestText, setRequestText] = useState(
    "Urgent SEO audit review: fix critical crawl issues and raise visibility.",
  );
  const [error, setError] = useState<string | null>(null);
  const [run, setRun] = useState<StrategicRun | null>(null);

  const mutate = useMutation({
    mutationFn: () =>
      apiFetch<StrategicRun>("/intelligence/runs", {
        method: "POST",
        token: accessToken ?? undefined,
        body: JSON.stringify({
          request_text: requestText,
          workspace_id: workspaceId,
          metadata: {
            crawl: { pages_crawled: 42, pages_failed: 3, issues_found: 11 },
            seo_audit: {
              peacock_seo_score: 61,
              critical_issues: 4,
              warnings: 9,
              opportunities: 6,
              section_scores: { technical_seo: 58, content_quality: 64 },
            },
            visibility: { brand_mentions: 2, citation_counts: 1 },
          },
        }),
      }),
    onSuccess: (data) => {
      setError(null);
      setRun(data);
    },
    onError: (err: Error) => setError(err.message),
  });

  if (!accessToken) {
    return (
      <section className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--surface)] p-6">
        <h2 className="text-xl font-semibold" style={{ fontFamily: "var(--font-display)" }}>
          Strategic Intelligence
        </h2>
        <p className="mt-2 text-sm text-[var(--muted)]">
          Sign in to run Layers 0–10 on a strategic request.
        </p>
      </section>
    );
  }

  return (
    <section className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--surface)] p-6">
      <p className="text-sm uppercase tracking-[0.2em] text-[var(--muted)]">Layers 0–10</p>
      <h2 className="mt-1 text-2xl font-semibold" style={{ fontFamily: "var(--font-display)" }}>
        Strategic request decomposition
      </h2>
      <p className="mt-2 max-w-3xl text-sm text-[var(--muted)]">
        Intelligent context selection only — never a full database dump. Deterministic evidence stays
        separated from LLM inference.
      </p>

      <label className="mt-6 block text-sm">
        <span className="text-[var(--muted)]">Strategic request</span>
        <textarea
          className="mt-1 min-h-24 w-full rounded-[var(--radius)] border border-[var(--border)] bg-transparent px-3 py-2"
          value={requestText}
          onChange={(e) => setRequestText(e.target.value)}
        />
      </label>
      <div className="mt-3">
        <Button type="button" disabled={mutate.isPending} onClick={() => mutate.mutate()}>
          {mutate.isPending ? "Running pipeline…" : "Run Layers 0–10"}
        </Button>
      </div>
      {error ? <p className="mt-3 text-sm text-[var(--danger)]">{error}</p> : null}

      {run ? (
        <div className="mt-8 space-y-8">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <div>
              <p className="text-xs uppercase tracking-[0.14em] text-[var(--muted)]">Intent</p>
              <p className="mt-1 font-semibold">{run.classification.user_intent}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.14em] text-[var(--muted)]">Depth</p>
              <p className="mt-1 font-semibold">{run.classification.thinking_depth}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.14em] text-[var(--muted)]">Evidence</p>
              <p className="mt-1 font-semibold">
                {run.evidence_summary.deterministic} det · {run.evidence_summary.inferences} inf
              </p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.14em] text-[var(--muted)]">Context tokens</p>
              <p className="mt-1 font-semibold">
                {run.context_summary.tokens_used}/{run.context_summary.token_budget}
              </p>
            </div>
          </div>

          <ol className="space-y-2">
            {run.layers.map((layer) => (
              <li
                key={layer.layer}
                className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--border)] py-2 text-sm"
              >
                <span>
                  <span className="text-[var(--muted)]">L{layer.layer}</span> {layer.name}
                </span>
                <span className="text-[var(--muted)]">
                  {layer.status} · {layer.summary}
                </span>
              </li>
            ))}
          </ol>

          <div>
            <h3 className="text-lg font-semibold" style={{ fontFamily: "var(--font-display)" }}>
              Ranked recommendations
            </h3>
            <ul className="mt-3 space-y-3">
              {run.recommendations.map((rec) => (
                <li key={rec.title} className="rounded-[var(--radius)] border border-[var(--border)] p-3">
                  <p className="font-medium">{rec.title}</p>
                  <p className="mt-1 text-xs text-[var(--muted)]">
                    {rec.priority} · score {rec.priority_score} · inference={String(rec.depends_on_inference)}
                  </p>
                  <p className="mt-1 text-sm text-[var(--muted)]">{rec.rationale}</p>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="text-lg font-semibold" style={{ fontFamily: "var(--font-display)" }}>
              Execution plan
            </h3>
            <ul className="mt-3 space-y-2 text-sm">
              {run.tasks.map((task) => (
                <li key={task.title}>
                  {task.title}{" "}
                  <span className="text-[var(--muted)]">
                    · {task.owner_role} · {task.priority}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      ) : null}
    </section>
  );
}
