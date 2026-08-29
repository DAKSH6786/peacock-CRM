const LOOP = [
  "OBSERVE",
  "THINK",
  "VERIFY",
  "DECIDE",
  "EXECUTE",
  "MEASURE",
  "LEARN",
] as const;

const LAYERS = [
  "L0 Classification",
  "L1 Context",
  "L2 Evidence",
  "L3 Research",
  "L4 Specialists",
  "L5 Adversarial",
  "L6 Verification",
  "L7 Decision",
  "L8 Simulation",
  "L9 Execution",
  "L10 Learning",
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
        Strategic requests decompose into Layers 0–10 with intelligent context selection.
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

      <ol className="mt-4 flex flex-wrap gap-2">
        {LAYERS.map((layer) => (
          <li
            key={layer}
            className="rounded-lg border border-[var(--primary)]/30 px-3 py-2 text-xs font-semibold tracking-wide"
          >
            {layer}
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
