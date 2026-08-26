"use client";

import { useEffect, useState } from "react";

import { ModuleShell } from "@/components/module-shell";
import {
  DEMO_AI_GATEWAY_CATALOG,
  DEMO_GEO_INTELLIGENCE,
  fetchAiGatewayPlugins,
  fetchGeoIntelligencePreview,
  type AiGatewayCatalog,
  type GeoIntelligenceReport,
} from "@/lib/geo-intelligence";

const STRENGTH_LABEL: Record<string, string> = {
  high: "Strong signal",
  medium: "Moderate signal",
  low: "Weak signal",
};

export function GeoIntelligenceModule() {
  const [catalog, setCatalog] = useState<AiGatewayCatalog>(DEMO_AI_GATEWAY_CATALOG);
  const [report, setReport] = useState<GeoIntelligenceReport>(DEMO_GEO_INTELLIGENCE);
  const [activeEngine, setActiveEngine] = useState<string>("chatgpt");

  useEffect(() => {
    let active = true;
    void fetchAiGatewayPlugins().then((data) => active && setCatalog(data));
    void fetchGeoIntelligencePreview("Acme").then((data) => {
      if (active) {
        setReport(data);
        setActiveEngine(data.provider_responses[0]?.engine_code ?? "chatgpt");
      }
    });
    return () => {
      active = false;
    };
  }, []);

  const activeResponse = report.provider_responses.find((r) => r.engine_code === activeEngine);
  const activeTerminology = report.terminology_by_engine.find((t) => t.engine_code === activeEngine);
  const activeRecommendation = report.recommendations.find((r) => r.engine_code === activeEngine);

  return (
    <ModuleShell
      title="Peacock GEO Intelligence"
      kicker="AI Plugins → Peacock AI Gateway → Multi-LLM Collection → GEO Intelligence Layer"
      lede="Sends the same research prompt to every AI plugin, then extracts keywords, entities, questions, citations, and competitor mentions to generate platform-specific GEO opportunities."
    >
      <section>
        <h2 style={{ fontFamily: "var(--font-display)" }}>AI plugin connectors</h2>
        <p className="os-honesty">
          Each plugin is an independent adapter behind a common interface — enable one by setting
          its API key as an environment variable (e.g. <code>OPENAI_API_KEY</code>,{" "}
          <code>ANTHROPIC_API_KEY</code>, <code>GEMINI_API_KEY</code>, <code>PERPLEXITY_API_KEY</code>,{" "}
          <code>DEEPSEEK_API_KEY</code>). No credentials are hardcoded in the application.
        </p>
        <ul className="os-questions">
          {catalog.plugins.map((plugin) => (
            <li key={plugin.engine_code}>
              <span>
                {plugin.engine_name} <em style={{ color: "var(--muted)" }}>({plugin.provider_code})</em>
              </span>
              <em className={plugin.live ? "os-tag" : "os-tag os-tag--warn"}>
                {plugin.live ? "live" : "simulated · no API key"}
              </em>
            </li>
          ))}
        </ul>
      </section>

      <section style={{ marginTop: "2.5rem", paddingTop: "1.5rem", borderTop: "1px solid var(--border)" }}>
        <h2 style={{ fontFamily: "var(--font-display)" }}>Broadcast research prompt</h2>
        <p className="os-callout">{report.research_prompt}</p>

        <div className="cc-hero__actions" style={{ marginTop: "1rem" }}>
          {report.provider_responses.map((r) => (
            <button
              key={r.engine_code}
              type="button"
              className={`cc-btn ${activeEngine === r.engine_code ? "cc-btn--primary" : "cc-btn--ghost"}`}
              onClick={() => setActiveEngine(r.engine_code)}
            >
              {r.engine_name}
              {r.simulated ? " (simulated)" : ""}
            </button>
          ))}
        </div>

        {activeResponse ? (
          <div className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--background)]/40 p-4" style={{ marginTop: "1rem" }}>
            <p style={{ color: "var(--muted)", fontSize: "0.85rem", marginBottom: "0.5rem" }}>
              {activeResponse.engine_name} response{activeResponse.simulated ? " (simulated — no API key configured)" : ""}
            </p>
            <p>{activeResponse.content}</p>
          </div>
        ) : null}
      </section>

      <section style={{ marginTop: "2.5rem", paddingTop: "1.5rem", borderTop: "1px solid var(--border)" }}>
        <h2 style={{ fontFamily: "var(--font-display)" }}>Extraction — across all AI plugins</h2>

        <h3 style={{ marginTop: "1rem" }}>Recurring keywords &amp; phrases</h3>
        <ul className="os-questions">
          {report.keywords.slice(0, 10).map((k) => (
            <li key={k.phrase}>
              <span>{k.phrase}</span>
              <em className="os-tag">
                {k.frequency}× · {k.engine_codes.length} platform(s)
              </em>
            </li>
          ))}
        </ul>

        <h3 style={{ marginTop: "1.5rem" }}>Entities &amp; brands mentioned</h3>
        <ul className="os-questions">
          {report.entities.slice(0, 10).map((e) => (
            <li key={e.name}>
              <span>{e.name}</span>
              <em className={e.kind === "competitor" ? "os-tag os-tag--warn" : "os-tag"}>{e.kind}</em>
            </li>
          ))}
        </ul>

        <h3 style={{ marginTop: "1.5rem" }}>Questions &amp; search intents</h3>
        <ul className="os-questions">
          {report.questions.slice(0, 8).map((q) => (
            <li key={q.question}>
              <span>{q.question}</span>
              <em className="os-tag">{q.engine_code}</em>
            </li>
          ))}
        </ul>

        <h3 style={{ marginTop: "1.5rem" }}>Sources / domains cited</h3>
        <ul className="os-questions">
          {report.citations.slice(0, 8).map((c) => (
            <li key={c.url}>
              <span>{c.domain}</span>
              <em className="os-tag">
                {c.source_class} · {c.engine_code}
              </em>
            </li>
          ))}
        </ul>

        <h3 style={{ marginTop: "1.5rem" }}>Missing topics for this website</h3>
        <ul className="os-questions">
          {report.missing_topics.map((topic) => (
            <li key={topic}>
              <span>{topic}</span>
              <em className="os-tag os-tag--warn">gap</em>
            </li>
          ))}
        </ul>
      </section>

      <section style={{ marginTop: "2.5rem", paddingTop: "1.5rem", borderTop: "1px solid var(--border)" }}>
        <h2 style={{ fontFamily: "var(--font-display)" }}>Terminology used by {activeResponse?.engine_name ?? "this platform"}</h2>
        <ul className="os-questions">
          {(activeTerminology?.top_terms ?? []).map((term) => (
            <li key={term}>
              <span>{term}</span>
            </li>
          ))}
        </ul>
      </section>

      <section style={{ marginTop: "2.5rem", paddingTop: "1.5rem", borderTop: "1px solid var(--border)" }}>
        <h2 style={{ fontFamily: "var(--font-display)" }}>Platform-specific GEO recommendations</h2>
        <p className="os-honesty">{report.disclaimer}</p>
        {report.recommendations.map((rec) => (
          <article
            key={rec.engine_code}
            className="os-card"
            style={{ marginBottom: "0.85rem", display: "block" }}
          >
            <div className="cc-hero__actions" style={{ justifyContent: "space-between", marginTop: 0 }}>
              <strong>{rec.platform_label}</strong>
              <em className="os-tag">{STRENGTH_LABEL[rec.signal_strength] ?? rec.signal_strength}</em>
            </div>
            <ul className="lab-list" style={{ marginTop: "0.5rem" }}>
              {rec.opportunities.map((opp) => (
                <li key={opp}>{opp}</li>
              ))}
            </ul>
          </article>
        ))}
      </section>

      <p className="os-honesty" style={{ marginTop: "1.5rem" }}>
        {report.methodology_note}
      </p>
    </ModuleShell>
  );
}
