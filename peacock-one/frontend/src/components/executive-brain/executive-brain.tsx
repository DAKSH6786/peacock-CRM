"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  DEMO_EXECUTIVE_BRIEF,
  fetchExecutiveBrainPreview,
  type ExecutiveBrainBrief,
} from "@/lib/executive-brain";

export function ExecutiveBrainView() {
  const [brief, setBrief] = useState<ExecutiveBrainBrief>(DEMO_EXECUTIVE_BRIEF);

  useEffect(() => {
    let active = true;
    void fetchExecutiveBrainPreview("Acme").then((data) => {
      if (active) setBrief(data);
    });
    return () => {
      active = false;
    };
  }, []);

  const ceo = brief.role_summaries.find((r) => r.role === "ceo");
  const cmo = brief.role_summaries.find((r) => r.role === "cmo");

  return (
    <div className="eb-shell">
      <header className="eb-hero">
        <p className="eb-kicker">
          <Link href="/">← Command Centre</Link>
        </p>
        <h1 className="eb-brand" style={{ fontFamily: "var(--font-display)" }}>
          Peacock Executive Brain
        </h1>
        <p className="eb-lede">
          A special executive view — not SEO complexity. Where we win, where we
          lose, why, what changed, what is worth doing, cost, return, and the
          cost of doing nothing.
        </p>
        <p className="eb-meta">
          {brief.client_brand} · {brief.horizon_days}-day horizon ·{" "}
          {brief.budget_label} · confidence{" "}
          {Math.round(brief.overall_confidence * 100)}%
        </p>
      </header>

      <section className="eb-summaries" aria-label="CEO and CMO summaries">
        {ceo && (
          <article className="eb-summary" data-role="ceo">
            <p className="eb-summary__role">{ceo.title}</p>
            <p className="eb-summary__body">{ceo.body}</p>
            <p className="eb-summary__cta">
              <span>Decide</span>
              {ceo.call_to_action}
            </p>
          </article>
        )}
        {cmo && (
          <article className="eb-summary" data-role="cmo">
            <p className="eb-summary__role">{cmo.title}</p>
            <p className="eb-summary__body">{cmo.body}</p>
            <p className="eb-summary__cta">
              <span>Decide</span>
              {cmo.call_to_action}
            </p>
          </article>
        )}
      </section>

      <section className="eb-questions" aria-labelledby="eb-questions-title">
        <div className="eb-section-head">
          <h2 id="eb-questions-title" style={{ fontFamily: "var(--font-display)" }}>
            Executive questions
          </h2>
          <p>Plain answers. No SEO clutter.</p>
        </div>
        <ol className="eb-qa">
          {brief.answers.map((item, index) => (
            <li
              key={item.question_key}
              style={{ animationDelay: `${0.05 * index}s` }}
            >
              <h3 style={{ fontFamily: "var(--font-display)" }}>
                {item.question_label}
              </h3>
              <p className="eb-qa__answer">{item.answer}</p>
              <p className="eb-qa__foot">
                <span>Evidence</span> {item.evidence_note}
                <em>{Math.round(item.confidence * 100)}%</em>
              </p>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
