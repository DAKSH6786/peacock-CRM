"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  DEMO_METRICS,
  fetchProprietaryMetricsPreview,
  type ProprietaryMetricsScorecard,
} from "@/lib/proprietary-metrics";

export function ProprietaryMetricsView() {
  const [card, setCard] = useState<ProprietaryMetricsScorecard>(DEMO_METRICS);
  const [openKey, setOpenKey] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    void fetchProprietaryMetricsPreview("Acme").then((data) => {
      if (active) {
        setCard(data);
        setOpenKey(data.metrics[0]?.metric_key ?? null);
      }
    });
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="pm-shell">
      <header className="pm-hero">
        <p className="pm-kicker">
          <Link href="/">← Command Centre</Link>
          <span aria-hidden>·</span>
          <Link href="/research">Research Mode</Link>
        </p>
        <h1 className="pm-brand" style={{ fontFamily: "var(--font-display)" }}>
          Peacock Proprietary Metrics
        </h1>
        <p className="pm-lede">
          Documented scoring framework. Every formula is published. These are
          Peacock indicators — never official platform ranking factors.
        </p>
        <p className="pm-disclaimer">{card.proprietary_disclaimer}</p>
        <p className="pm-platforms">
          Not: {card.not_official_platforms.join(" · ")}
        </p>
      </header>

      <section className="pm-list" aria-label="Metric scorecard">
        {card.metrics.map((m) => {
          const open = openKey === m.metric_key;
          return (
            <article key={m.metric_key} className="pm-item" data-open={open}>
              <button
                type="button"
                className="pm-item__head"
                onClick={() => setOpenKey(open ? null : m.metric_key)}
                aria-expanded={open}
              >
                <span>
                  <em>{m.formula_id}</em>
                  <strong style={{ fontFamily: "var(--font-display)" }}>
                    {m.metric_label}
                  </strong>
                </span>
                <span className="pm-item__score">
                  {m.unit === "0-1" ? m.score.toFixed(3) : m.score.toFixed(1)}
                  <small>{m.unit}</small>
                </span>
              </button>
              {open && (
                <div className="pm-item__body">
                  <p className="pm-formula">
                    <span>Formula</span>
                    {m.formula_text}
                  </p>
                  <p className="pm-explain">{m.explanation}</p>
                  {m.components.length > 0 && (
                    <ul className="pm-components">
                      {m.components.map((c) => (
                        <li key={c.component_key}>
                          <span>{c.component_label}</span>
                          <strong>
                            {c.raw_value.toFixed(2)} × {c.weight.toFixed(2)} →{" "}
                            {c.contribution.toFixed(2)}
                          </strong>
                        </li>
                      ))}
                    </ul>
                  )}
                  <p className="pm-note">{m.proprietary_note}</p>
                </div>
              )}
            </article>
          );
        })}
      </section>
    </div>
  );
}
