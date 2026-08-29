"use client";

import { useEffect, useState } from "react";

import { ModuleShell } from "@/components/module-shell";
import {
  DEMO_AI_VISIBILITY,
  fetchAiVisibilityPreview,
  type AiVisibilityScoreCard,
} from "@/lib/ai-visibility";
import { DEMO_GEO_INTELLIGENCE, fetchGeoIntelligencePreview, type GeoIntelligenceReport } from "@/lib/geo-intelligence";

export function AiVisibilityModule() {
  const [data, setData] = useState<AiVisibilityScoreCard>(DEMO_AI_VISIBILITY);
  const [geoIntelligence, setGeoIntelligence] = useState<GeoIntelligenceReport>(DEMO_GEO_INTELLIGENCE);

  useEffect(() => {
    let active = true;
    void fetchAiVisibilityPreview("Acme").then((result) => {
      if (active) setData(result);
    });
    void fetchGeoIntelligencePreview("Acme").then((result) => {
      if (active) setGeoIntelligence(result);
    });
    return () => {
      active = false;
    };
  }, []);

  return (
    <ModuleShell
      title="AI Visibility"
      kicker="Module · Probabilistic AI Visibility (GEO Engine)"
      lede="Distributional measurement from controlled repeated probes across AI engines — never a single-shot claim."
    >
      <div className="os-callout">{data.summary}</div>

      <dl className="os-stats">
        <div>
          <dt>AI Visibility Score</dt>
          <dd>{data.ai_visibility_score}</dd>
        </div>
        <div>
          <dt>Confidence</dt>
          <dd>{data.measurement_confidence}</dd>
        </div>
        <div>
          <dt>Brand mention prob.</dt>
          <dd>{(data.brand_mention_probability * 100).toFixed(0)}%</dd>
        </div>
        <div>
          <dt>Citation prob.</dt>
          <dd>{(data.citation_probability * 100).toFixed(0)}%</dd>
        </div>
        <div>
          <dt>Top-3 recommendation prob.</dt>
          <dd>{(data.top3_recommendation_probability * 100).toFixed(0)}%</dd>
        </div>
        <div>
          <dt>Repetitions</dt>
          <dd>
            {data.based_on.repetitions} · {data.based_on.engines} engines
          </dd>
        </div>
      </dl>

      <section style={{ marginTop: "2rem" }}>
        <h2 style={{ fontFamily: "var(--font-display)" }}>Per-engine distribution</h2>
        <ul className="os-questions">
          {data.distributions.map((d) => (
            <li key={d.engine}>
              <span>{d.engine.replaceAll("_", " ")}</span>
              <em className="os-tag">
                mention {(d.brand_mention_probability * 100).toFixed(0)}% · citation{" "}
                {(d.citation_probability * 100).toFixed(0)}% · top-3 {(d.top3_probability * 100).toFixed(0)}%
              </em>
            </li>
          ))}
        </ul>
      </section>

      <section style={{ marginTop: "2rem" }}>
        <h2 style={{ fontFamily: "var(--font-display)" }}>Competitor comparison</h2>
        <ul className="os-questions">
          {Object.entries(data.competitor_probabilities).map(([name, prob]) => (
            <li key={name}>
              <span>{name.replaceAll("_", " ")}</span>
              <em className="os-tag">{(prob * 100).toFixed(0)}%</em>
            </li>
          ))}
        </ul>
      </section>

      <p className="os-honesty" style={{ marginTop: "1.5rem" }}>
        Probe mode: {data.probe_mode}. Single-shot measurement rejected —{" "}
        {data.defensible ? "measurement is defensible" : "more repetitions recommended before reporting"}.
      </p>

      <section style={{ marginTop: "2.5rem", paddingTop: "1.5rem", borderTop: "1px solid var(--border)" }}>
        <h2 style={{ fontFamily: "var(--font-display)" }}>
          Platform-specific GEO recommendations (ChatGPT, Gemini, Claude, Perplexity, DeepSeek)
        </h2>
        <p className="os-honesty">{geoIntelligence.disclaimer}</p>
        {geoIntelligence.recommendations.map((rec) => (
          <article key={rec.engine_code} className="os-card" style={{ marginBottom: "0.85rem", display: "block" }}>
            <strong>{rec.platform_label}</strong>
            <ul className="lab-list" style={{ marginTop: "0.5rem" }}>
              {rec.opportunities.slice(0, 3).map((opp) => (
                <li key={opp}>{opp}</li>
              ))}
            </ul>
          </article>
        ))}
        <p style={{ marginTop: "0.75rem" }}>
          <a href="/modules/geo-intelligence" className="cc-btn cc-btn--ghost">
            Open full Peacock GEO Intelligence
          </a>
        </p>
      </section>
    </ModuleShell>
  );
}
