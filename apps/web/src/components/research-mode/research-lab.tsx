"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  DEMO_RESEARCH_STUDY,
  fetchResearchModePreview,
  type ResearchStudy,
} from "@/lib/research-mode";

function fmt(n: number | null | undefined, digits = 3) {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  return n.toFixed(digits);
}

export function ResearchLabView() {
  const [study, setStudy] = useState<ResearchStudy>(DEMO_RESEARCH_STUDY);

  useEffect(() => {
    let active = true;
    void fetchResearchModePreview("Acme").then((data) => {
      if (active) setStudy(data);
    });
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="lab-shell">
      <header className="lab-hero">
        <p className="lab-kicker">
          <Link href="/">← Command Centre</Link>
          <span aria-hidden>·</span>
          <Link href="/metrics">Proprietary Metrics</Link>
        </p>
        <h1 className="lab-brand" style={{ fontFamily: "var(--font-display)" }}>
          Peacock Research Mode
        </h1>
        <p className="lab-lede">
          Search intelligence laboratory — controlled analyses for serious
          enterprise users. Not SEO software theatre.
        </p>
        <p className="lab-position">{study.laboratory_positioning}</p>
      </header>

      <section className="lab-question" aria-labelledby="lab-q-title">
        <p className="lab-label">Research question</p>
        <h2 id="lab-q-title" style={{ fontFamily: "var(--font-display)" }}>
          {study.research_question}
        </h2>
        <p className="lab-hypothesis">
          <span>Hypothesis</span>
          {study.hypothesis}
        </p>
        <p className="lab-treatment">
          <span>Treatment</span>
          {study.treatment_description}
        </p>
      </section>

      <section className="lab-phases" aria-label="Study phases">
        <ol>
          {study.completed_phases.map((phase) => (
            <li key={phase}>{phase.replaceAll("_", " ")}</li>
          ))}
        </ol>
      </section>

      <section className="lab-design" aria-label="Design">
        <div>
          <p className="lab-label">Metric</p>
          <p className="lab-design__value">{study.metric_label}</p>
        </div>
        <div>
          <p className="lab-label">Pages</p>
          <ul className="lab-list">
            {study.pages.map((p) => (
              <li key={p.url}>
                <em>{p.page_role}</em> {p.label || p.url}
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="lab-label">Prompts</p>
          <ul className="lab-list">
            {study.prompts.map((p) => (
              <li key={p.prompt_text}>{p.prompt_text}</li>
            ))}
          </ul>
        </div>
      </section>

      <section className="lab-results" aria-labelledby="lab-results-title">
        <h2 id="lab-results-title" style={{ fontFamily: "var(--font-display)" }}>
          Baseline → treatment
        </h2>
        <div className="lab-results__grid">
          <div>
            <p className="lab-label">Baseline mean</p>
            <p className="lab-stat">{fmt(study.baseline_mean)}</p>
          </div>
          <div>
            <p className="lab-label">Treatment mean</p>
            <p className="lab-stat">{fmt(study.treatment_mean)}</p>
          </div>
          <div>
            <p className="lab-label">Absolute Δ</p>
            <p className="lab-stat">
              {study.absolute_delta !== null && study.absolute_delta >= 0 ? "+" : ""}
              {fmt(study.absolute_delta)}
            </p>
          </div>
          <div>
            <p className="lab-label">Control-adjusted Δ</p>
            <p className="lab-stat">
              {study.control_adjusted_delta !== null &&
              study.control_adjusted_delta >= 0
                ? "+"
                : ""}
              {fmt(study.control_adjusted_delta)}
            </p>
          </div>
          <div>
            <p className="lab-label">Uncertainty</p>
            <p className="lab-stat lab-stat--band">{study.uncertainty_band}</p>
          </div>
          <div>
            <p className="lab-label">Verdict</p>
            <p className="lab-stat lab-stat--verdict">
              {study.finding_verdict.replaceAll("_", " ")}
            </p>
          </div>
        </div>
        <p className="lab-summary">{study.finding_summary}</p>
      </section>

      <section className="lab-findings" aria-labelledby="lab-findings-title">
        <h2 id="lab-findings-title" style={{ fontFamily: "var(--font-display)" }}>
          Findings
        </h2>
        {study.findings.map((f) => (
          <article key={f.finding_index} className="lab-finding">
            <p className="lab-label">{f.verdict.replaceAll("_", " ")}</p>
            <h3 style={{ fontFamily: "var(--font-display)" }}>{f.claim}</h3>
            <p>{f.evidence}</p>
            <p className="lab-finding__u">{f.uncertainty_rationale}</p>
            <p className="lab-finding__next">
              <span>Next</span>
              {f.next_step}
            </p>
            {f.auto_causal_conclusion_rejected && (
              <p className="lab-finding__reject">Auto causal conclusion rejected</p>
            )}
          </article>
        ))}
      </section>

      <aside className="lab-warning" role="note">
        {study.causality_warning}
      </aside>
    </div>
  );
}
