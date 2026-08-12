"use client";

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";

type HealthResponse = {
  status: string;
  app: string;
  env: string;
  database: string;
  redis: string;
  job_backend: string;
};

export function HealthCard() {
  const query = useQuery({
    queryKey: ["health"],
    queryFn: () => apiFetch<HealthResponse>("/health"),
    refetchInterval: 15_000,
  });

  return (
    <section className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--surface)] p-6">
      <h2 className="text-xl font-semibold" style={{ fontFamily: "var(--font-display)" }}>
        Platform health
      </h2>
      <p className="mt-1 text-sm text-[var(--muted)]">
        Live check against the FastAPI composition root.
      </p>
      {query.isLoading ? (
        <p className="mt-6 text-sm text-[var(--muted)]">Checking…</p>
      ) : query.isError ? (
        <p className="mt-6 text-sm text-[var(--danger)]">
          API unreachable. Start docker compose or local uvicorn.
        </p>
      ) : (
        <dl className="mt-6 grid grid-cols-2 gap-3 text-sm">
          <div>
            <dt className="text-[var(--muted)]">Status</dt>
            <dd className="font-semibold">{query.data?.status}</dd>
          </div>
          <div>
            <dt className="text-[var(--muted)]">Env</dt>
            <dd className="font-semibold">{query.data?.env}</dd>
          </div>
          <div>
            <dt className="text-[var(--muted)]">Database</dt>
            <dd className="font-semibold">{query.data?.database}</dd>
          </div>
          <div>
            <dt className="text-[var(--muted)]">Redis</dt>
            <dd className="font-semibold">{query.data?.redis}</dd>
          </div>
          <div>
            <dt className="text-[var(--muted)]">Jobs</dt>
            <dd className="font-semibold">{query.data?.job_backend}</dd>
          </div>
        </dl>
      )}
    </section>
  );
}
