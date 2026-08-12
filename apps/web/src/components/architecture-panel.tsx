const LOOP = [
  "OBSERVE",
  "THINK",
  "VERIFY",
  "DECIDE",
  "EXECUTE",
  "MEASURE",
  "LEARN",
] as const;

const SERVICES = [
  "crawler",
  "intelligence",
  "llm_gateway",
  "seo_engine",
  "geo_engine",
  "aeo_engine",
  "content_engine",
  "writer_engine",
  "competitor_engine",
  "strategy_engine",
  "monitoring_engine",
  "learning_engine",
] as const;

export function ArchitecturePanel() {
  return (
    <section className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--surface)] p-6">
      <h2 className="text-xl font-semibold" style={{ fontFamily: "var(--font-display)" }}>
        Monorepo surface
      </h2>
      <p className="mt-1 text-sm text-[var(--muted)]">
        Provider-specific LLM logic stays in <code>llm_gateway</code> adapters.
        Jobs run through a Celery backend behind a Temporal-ready port.
      </p>

      <ol className="mt-6 flex flex-wrap gap-2">
        {LOOP.map((stage, index) => (
          <li
            key={stage}
            className="rounded-lg border border-[var(--border)] px-3 py-2 text-xs font-semibold tracking-wide"
          >
            <span className="text-[var(--muted)]">{index + 1}. </span>
            {stage}
          </li>
        ))}
      </ol>

      <div className="mt-6 grid gap-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
        {SERVICES.map((service) => (
          <div
            key={service}
            className="rounded-lg border border-[var(--border)] px-3 py-2 text-sm text-[var(--muted)]"
          >
            {service}
          </div>
        ))}
      </div>
    </section>
  );
}
