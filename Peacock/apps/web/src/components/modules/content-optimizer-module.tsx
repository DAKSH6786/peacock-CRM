"use client";

import { useEffect, useState } from "react";

import { ModuleShell } from "@/components/module-shell";
import {
  DEMO_CONTENT_OPTIMIZER,
  fetchContentOptimizerPreview,
  type ContentOptimizerResult,
} from "@/lib/content-optimizer";

export function ContentOptimizerModule() {
  const [data, setData] = useState<ContentOptimizerResult>(DEMO_CONTENT_OPTIMIZER);

  useEffect(() => {
    let active = true;
    void fetchContentOptimizerPreview("Acme").then((result) => {
      if (active) setData(result);
    });
    return () => {
      active = false;
    };
  }, []);

  return (
    <ModuleShell
      title="Content Optimizer"
      kicker="Module · Writer Intelligence 2.0"
      lede="Optimises WHO writes WHAT for THIS topic, client, and audience — Writer DNA and outcome history, not sample-similarity matching."
    >
      <p className="os-callout">{data.decision_question}</p>
      <p className="os-honesty">{data.similarity_rejection_note}</p>

      <section style={{ marginTop: "1.5rem" }}>
        <h2 style={{ fontFamily: "var(--font-display)" }}>Ranked writer recommendations</h2>
        {data.recommendations.map((rec) => (
          <article
            key={rec.writer_key}
            className="os-card"
            style={{ marginBottom: "0.85rem", display: "block" }}
          >
            <div className="cc-hero__actions" style={{ justifyContent: "space-between", marginTop: 0 }}>
              <strong>
                #{rec.rank} · {rec.display_name}
              </strong>
              <em className="os-tag">{rec.predicted_outcome_score.toFixed(0)}/100</em>
            </div>
            <span>{rec.rationale}</span>
            <span style={{ fontSize: "0.85rem" }}>
              DNA fit {rec.dna_fit_score.toFixed(0)} · Topic fit {rec.topic_fit_score.toFixed(0)} · Client fit{" "}
              {rec.client_fit_score.toFixed(0)} · Audience fit {rec.audience_fit_score.toFixed(0)} · Historical{" "}
              {rec.historical_outcome_score.toFixed(0)}
            </span>
          </article>
        ))}
      </section>

      <section style={{ marginTop: "2.5rem", paddingTop: "1.5rem", borderTop: "1px solid var(--border)" }}>
        <h2 style={{ fontFamily: "var(--font-display)" }}>Writer DNA</h2>
        <dl className="os-stats">
          {data.dna_profiles.map((p) => (
            <div key={p.writer_key}>
              <dt>{p.display_name}</dt>
              <dd>{p.dna_composite_score.toFixed(0)}</dd>
            </div>
          ))}
        </dl>
        <ul className="os-questions">
          {data.dna_profiles.map((p) => (
            <li key={p.writer_key}>
              <span>{p.dna_summary}</span>
            </li>
          ))}
        </ul>
      </section>

      <p className="os-honesty" style={{ marginTop: "1.5rem" }}>
        {data.summary}
      </p>
    </ModuleShell>
  );
}
