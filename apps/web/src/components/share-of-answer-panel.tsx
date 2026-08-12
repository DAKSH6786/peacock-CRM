"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api";
import { useAuthStore } from "@/stores/auth";

type Website = {
  id: string;
  name: string;
  primary_domain: string;
};

type BrandShare = {
  entity_name: string;
  is_client: boolean;
  share_of_answer: number;
  mention_rate: number;
  avg_recommendation_strength: number;
  avg_position_score: number;
  avg_answer_space: number;
  avg_citation_ownership: number;
  avg_semantic_prominence: number;
  avg_claim_balance: number;
  avg_comparison_score: number;
  token_only_share: number;
  token_vs_influence_gap: number;
  positive_claims_total: number;
  negative_claims_total: number;
  neutral_claims_total: number;
};

type ShareOfAnswerReport = {
  analysis_id: string;
  query_cluster: string;
  client_brand: string;
  methodology: string;
  token_count_alone_rejected: boolean;
  observation_count: number;
  brands: BrandShare[];
  indicator_weights: Record<string, number>;
  example_display: Array<{
    brand: string;
    share_of_answer_pct: number;
    is_client: boolean;
  }>;
};

type Catalog = {
  indicators: string[];
  default_weights: Record<string, number>;
  methodology_note: string;
};

const DEFAULT_EXCERPT = `Top enterprise CRM options include Brand A for scale,
Brand B for analytics, and Client for emerging teams.
Brand A is the strongest overall recommendation and leads on citations
from https://branda.example/docs. Brand B is a solid alternative with
strong insights. Client appears as a niche option with limited coverage.`;

function pct(value: number, digits = 1): string {
  return `${value.toFixed(digits)}%`;
}

function IndicatorBar({ label, value }: { label: string; value: number }) {
  const width = Math.max(0, Math.min(100, value * 100));
  return (
    <div className="space-y-1">
      <div className="flex justify-between gap-3 text-xs text-[var(--muted)]">
        <span>{label}</span>
        <span>{(value * 100).toFixed(0)}%</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-[var(--border)]">
        <div
          className="h-full rounded-full bg-[var(--primary)]"
          style={{ width: `${width}%` }}
        />
      </div>
    </div>
  );
}

export function ShareOfAnswerPanel() {
  const { accessToken, workspaceId } = useAuthStore();
  const [queryCluster, setQueryCluster] = useState("Enterprise CRM");
  const [clientBrand, setClientBrand] = useState("Client");
  const [competitors, setCompetitors] = useState("Brand A, Brand B");
  const [excerpt, setExcerpt] = useState(DEFAULT_EXCERPT);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<ShareOfAnswerReport | null>(null);

  const websites = useQuery({
    queryKey: ["websites", accessToken],
    enabled: Boolean(accessToken),
    queryFn: () =>
      apiFetch<Website[]>("/websites", { token: accessToken ?? undefined }),
  });

  const catalog = useQuery({
    queryKey: ["soa-catalog", accessToken],
    enabled: Boolean(accessToken),
    queryFn: () =>
      apiFetch<Catalog>("/share-of-answer/catalog", {
        token: accessToken ?? undefined,
      }),
  });

  const websiteId = useMemo(
    () => websites.data?.[0]?.id ?? null,
    [websites.data],
  );

  const analyse = useMutation({
    mutationFn: () => {
      if (!websiteId) {
        throw new Error("Ingest a website first so Share of Answer has a site scope.");
      }
      const competitor_brands = competitors
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
      return apiFetch<ShareOfAnswerReport>("/share-of-answer/analyses", {
        method: "POST",
        token: accessToken ?? undefined,
        body: JSON.stringify({
          website_id: websiteId,
          workspace_id: workspaceId,
          name: `${queryCluster} Share of Answer`,
          query_cluster: queryCluster,
          client_brand: clientBrand,
          competitor_brands,
          observations: [
            {
              prompt_text: `best ${queryCluster} platforms`,
              engine_code: "chatgpt",
              raw_excerpt: excerpt,
            },
            {
              prompt_text: `${queryCluster} comparison shortlist`,
              engine_code: "perplexity",
              raw_excerpt: excerpt,
            },
          ],
        }),
      });
    },
    onSuccess: (data) => {
      setError(null);
      setReport(data);
    },
    onError: (err: Error) => setError(err.message),
  });

  if (!accessToken) {
    return (
      <section className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--surface)] p-6">
        <h2 className="text-xl font-semibold" style={{ fontFamily: "var(--font-display)" }}>
          Share of Answer
        </h2>
        <p className="mt-2 text-sm text-[var(--muted)]">
          Sign in to measure brand control of generative answers — beyond Share of Voice.
        </p>
      </section>
    );
  }

  return (
    <section className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--surface)] p-6">
      <p className="text-sm uppercase tracking-[0.2em] text-[var(--muted)]">
        Beyond Share of Voice
      </p>
      <h2 className="mt-1 text-2xl font-semibold" style={{ fontFamily: "var(--font-display)" }}>
        Share of Answer
      </h2>
      <p className="mt-2 max-w-3xl text-sm text-[var(--muted)]">
        Measures how much of a generative answer is controlled by or favourable to each
        brand using mention, position, recommendation strength, answer space, citation
        ownership, semantic prominence, claim polarity, and comparison outcome — not token
        count alone.
      </p>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <label className="block text-sm">
          <span className="text-[var(--muted)]">Query cluster</span>
          <input
            className="mt-1 w-full rounded-[var(--radius)] border border-[var(--border)] bg-transparent px-3 py-2"
            value={queryCluster}
            onChange={(e) => setQueryCluster(e.target.value)}
          />
        </label>
        <label className="block text-sm">
          <span className="text-[var(--muted)]">Client brand</span>
          <input
            className="mt-1 w-full rounded-[var(--radius)] border border-[var(--border)] bg-transparent px-3 py-2"
            value={clientBrand}
            onChange={(e) => setClientBrand(e.target.value)}
          />
        </label>
        <label className="block text-sm md:col-span-2">
          <span className="text-[var(--muted)]">Competitors (comma-separated)</span>
          <input
            className="mt-1 w-full rounded-[var(--radius)] border border-[var(--border)] bg-transparent px-3 py-2"
            value={competitors}
            onChange={(e) => setCompetitors(e.target.value)}
          />
        </label>
        <label className="block text-sm md:col-span-2">
          <span className="text-[var(--muted)]">Generative answer excerpt</span>
          <textarea
            className="mt-1 min-h-32 w-full rounded-[var(--radius)] border border-[var(--border)] bg-transparent px-3 py-2"
            value={excerpt}
            onChange={(e) => setExcerpt(e.target.value)}
          />
        </label>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <Button
          type="button"
          disabled={analyse.isPending || !websiteId}
          onClick={() => analyse.mutate()}
        >
          {analyse.isPending ? "Scoring…" : "Analyse Share of Answer"}
        </Button>
        {!websiteId ? (
          <p className="text-sm text-[var(--muted)]">
            Ingest a website above to scope the analysis.
          </p>
        ) : null}
      </div>
      {error ? <p className="mt-3 text-sm text-[var(--danger)]">{error}</p> : null}

      {catalog.data ? (
        <p className="mt-4 text-xs text-[var(--muted)]">{catalog.data.methodology_note}</p>
      ) : null}

      {report ? (
        <div className="mt-8 space-y-8">
          <div>
            <p className="text-xs uppercase tracking-[0.14em] text-[var(--muted)]">
              Query cluster · {report.query_cluster}
            </p>
            <h3
              className="mt-2 text-lg font-semibold"
              style={{ fontFamily: "var(--font-display)" }}
            >
              Brand Share of Answer
            </h3>
            <ul className="mt-4 space-y-3">
              {report.example_display.map((row) => (
                <li
                  key={row.brand}
                  className="flex items-end justify-between gap-4 border-b border-[var(--border)] pb-3"
                >
                  <div>
                    <p className="text-lg font-semibold" style={{ fontFamily: "var(--font-display)" }}>
                      {row.brand}
                      {row.is_client ? (
                        <span className="ml-2 text-xs font-normal uppercase tracking-[0.14em] text-[var(--muted)]">
                          client
                        </span>
                      ) : null}
                    </p>
                  </div>
                  <p className="text-3xl font-semibold tabular-nums" style={{ fontFamily: "var(--font-display)" }}>
                    {pct(row.share_of_answer_pct)}
                  </p>
                </li>
              ))}
            </ul>
            <p className="mt-3 text-xs text-[var(--muted)]">
              Methodology: {report.methodology}
              {report.token_count_alone_rejected
                ? " · token count alone rejected"
                : null}{" "}
              · {report.observation_count} observations
            </p>
          </div>

          <div className="grid gap-4 lg:grid-cols-3">
            {report.brands.map((brand) => (
              <article
                key={brand.entity_name}
                className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--background)]/40 p-4"
              >
                <div className="flex items-baseline justify-between gap-2">
                  <h4 className="font-semibold" style={{ fontFamily: "var(--font-display)" }}>
                    {brand.entity_name}
                  </h4>
                  <span className="text-xl font-semibold tabular-nums">
                    {pct(brand.share_of_answer)}
                  </span>
                </div>
                <div className="mt-4 space-y-3">
                  <IndicatorBar label="Mention rate" value={brand.mention_rate} />
                  <IndicatorBar label="Position" value={brand.avg_position_score} />
                  <IndicatorBar
                    label="Recommendation"
                    value={brand.avg_recommendation_strength}
                  />
                  <IndicatorBar label="Answer space" value={brand.avg_answer_space} />
                  <IndicatorBar label="Citations" value={brand.avg_citation_ownership} />
                  <IndicatorBar label="Prominence" value={brand.avg_semantic_prominence} />
                  <IndicatorBar label="Claim balance" value={brand.avg_claim_balance} />
                  <IndicatorBar label="Comparison" value={brand.avg_comparison_score} />
                </div>
                <p className="mt-4 text-xs text-[var(--muted)]">
                  Claims +{brand.positive_claims_total} / −{brand.negative_claims_total} / ~
                  {brand.neutral_claims_total}
                  <br />
                  Token-only share {pct(brand.token_only_share)} · gap{" "}
                  {brand.token_vs_influence_gap > 0 ? "+" : ""}
                  {pct(brand.token_vs_influence_gap)}
                </p>
              </article>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}
