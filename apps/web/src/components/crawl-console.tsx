"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api";
import { useAuthStore } from "@/stores/auth";

type CrawlProgress = {
  pages_discovered: number;
  pages_crawled: number;
  pages_failed: number;
  issues_found: number;
  progress_percent: number;
  max_pages: number;
  status: string;
};

type CrawlResponse = {
  id: string;
  seed_url: string;
  status: string;
  progress: CrawlProgress;
  error_summary?: string | null;
};

const PRESETS = [
  { id: "free_trial", label: "Free trial · 100" },
  { id: "starter", label: "Starter · 1,000" },
  { id: "pro", label: "Pro · 10,000" },
  { id: "enterprise", label: "Enterprise · configurable" },
] as const;

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <p className="text-xs uppercase tracking-[0.14em] text-[var(--muted)]">{label}</p>
      <p className="mt-1 text-2xl font-semibold" style={{ fontFamily: "var(--font-display)" }}>
        {value}
      </p>
    </div>
  );
}

export function CrawlConsole({
  onCrawlIdChange,
}: {
  onCrawlIdChange?: (crawlId: string | null) => void;
}) {
  const { accessToken, workspaceId } = useAuthStore();
  const queryClient = useQueryClient();
  const [url, setUrl] = useState("https://example.com");
  const [preset, setPreset] = useState<(typeof PRESETS)[number]["id"]>("free_trial");
  const [enterprisePages, setEnterprisePages] = useState(25000);
  const [crawlId, setCrawlId] = useState<string | null>(null);

  const updateCrawlId = (id: string | null) => {
    setCrawlId(id);
    onCrawlIdChange?.(id);
  };
  const [error, setError] = useState<string | null>(null);

  const crawl = useQuery({
    queryKey: ["crawl", crawlId, accessToken],
    enabled: Boolean(accessToken && crawlId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "running" || status === "paused" || status === "queued" ? 1200 : false;
    },
    queryFn: () =>
      apiFetch<CrawlResponse>(`/crawls/${crawlId}`, {
        token: accessToken ?? undefined,
      }),
  });

  const start = useMutation({
    mutationFn: () =>
      apiFetch<CrawlResponse>("/crawls", {
        method: "POST",
        token: accessToken ?? undefined,
        body: JSON.stringify({
          url,
          workspace_id: workspaceId,
          policy_preset: preset,
          max_pages: preset === "enterprise" ? enterprisePages : undefined,
          run_inline: true,
        }),
      }),
    onSuccess: (data) => {
      setError(null);
      updateCrawlId(data.id);
      queryClient.setQueryData(["crawl", data.id, accessToken], data);
    },
    onError: (err: Error) => setError(err.message),
  });

  const control = useMutation({
    mutationFn: (action: "pause" | "resume" | "cancel" | "restart" | "retry-failed") =>
      apiFetch<CrawlResponse>(`/crawls/${crawlId}/${action}`, {
        method: "POST",
        token: accessToken ?? undefined,
      }),
    onSuccess: (data) => {
      updateCrawlId(data.id);
      queryClient.setQueryData(["crawl", data.id, accessToken], data);
    },
    onError: (err: Error) => setError(err.message),
  });

  if (!accessToken) {
    return (
      <section className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--surface)] p-6">
        <h2 className="text-xl font-semibold" style={{ fontFamily: "var(--font-display)" }}>
          Peacock Crawler
        </h2>
        <p className="mt-2 text-sm text-[var(--muted)]">Sign in to ingest a website and watch crawl progress.</p>
      </section>
    );
  }

  const progress = crawl.data?.progress;

  return (
    <section className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--surface)] p-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.2em] text-[var(--muted)]">Peacock Crawler</p>
          <h2 className="mt-1 text-2xl font-semibold" style={{ fontFamily: "var(--font-display)" }}>
            Website ingestion
          </h2>
        </div>
        {crawl.data ? (
          <p className="text-sm text-[var(--muted)]">
            Status · <span className="text-[var(--foreground)]">{crawl.data.status}</span>
          </p>
        ) : null}
      </div>

      <form
        className="mt-6 grid gap-3 md:grid-cols-[1fr_auto]"
        onSubmit={(event) => {
          event.preventDefault();
          start.mutate();
        }}
      >
        <label className="block text-sm md:col-span-2">
          <span className="text-[var(--muted)]">Seed URL</span>
          <input
            className="mt-1 w-full rounded-[var(--radius)] border border-[var(--border)] bg-transparent px-3 py-2"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com"
          />
        </label>
        <label className="block text-sm">
          <span className="text-[var(--muted)]">Crawl policy</span>
          <select
            className="mt-1 w-full rounded-[var(--radius)] border border-[var(--border)] bg-transparent px-3 py-2"
            value={preset}
            onChange={(e) => setPreset(e.target.value as (typeof PRESETS)[number]["id"])}
          >
            {PRESETS.map((item) => (
              <option key={item.id} value={item.id}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
        {preset === "enterprise" ? (
          <label className="block text-sm">
            <span className="text-[var(--muted)]">Enterprise max pages</span>
            <input
              type="number"
              min={1}
              className="mt-1 w-full rounded-[var(--radius)] border border-[var(--border)] bg-transparent px-3 py-2"
              value={enterprisePages}
              onChange={(e) => setEnterprisePages(Number(e.target.value) || 1)}
            />
          </label>
        ) : (
          <div />
        )}
        <div className="md:col-span-2">
          <Button type="submit" disabled={start.isPending}>
            {start.isPending ? "Crawling…" : "Start crawl"}
          </Button>
        </div>
      </form>

      {error ? <p className="mt-3 text-sm text-[var(--danger)]">{error}</p> : null}

      {progress ? (
        <div className="mt-8 space-y-6">
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-5">
            <Stat label="Pages discovered" value={progress.pages_discovered} />
            <Stat label="Pages crawled" value={progress.pages_crawled} />
            <Stat label="Pages failed" value={progress.pages_failed} />
            <Stat label="Issues found" value={progress.issues_found} />
            <Stat label="Progress %" value={`${progress.progress_percent}%`} />
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-[var(--border)]">
            <div
              className="h-full bg-[var(--primary)] transition-all duration-500"
              style={{ width: `${Math.min(100, progress.progress_percent)}%` }}
            />
          </div>
          <div className="flex flex-wrap gap-2">
            <Button type="button" variant="secondary" onClick={() => control.mutate("pause")}>
              Pause
            </Button>
            <Button type="button" variant="secondary" onClick={() => control.mutate("resume")}>
              Resume
            </Button>
            <Button type="button" variant="secondary" onClick={() => control.mutate("cancel")}>
              Cancel
            </Button>
            <Button type="button" variant="secondary" onClick={() => control.mutate("restart")}>
              Restart
            </Button>
            <Button type="button" variant="secondary" onClick={() => control.mutate("retry-failed")}>
              Retry failed
            </Button>
          </div>
          {crawl.data?.error_summary ? (
            <p className="text-sm text-[var(--danger)]">{crawl.data.error_summary}</p>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
