"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  DEMO_ARCHITECTURE,
  SUBSYSTEM_LINKS,
  fetchArchitecturePreview,
  type ArchitectureMap,
} from "@/lib/peacock-os";

export function PeacockOsHub() {
  const [map, setMap] = useState<ArchitectureMap>(DEMO_ARCHITECTURE);

  useEffect(() => {
    let active = true;
    void fetchArchitecturePreview("Acme").then((data) => {
      if (active) setMap(data);
    });
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="cc-shell">
      <header className="os-hero">
        <p className="cc-hero__kicker">Not Semrush + an AI dashboard</p>
        <h1 className="cc-hero__brand" style={{ fontFamily: "var(--font-display)" }}>
          Peacock One
        </h1>
        <p className="os-lede">
          An Adaptive Search, Answer &amp; Generative Intelligence Operating System.
        </p>
        <p className="cc-hero__lede">{map.architecture_positioning}</p>
        <div className="cc-hero__actions">
          <Link href="/" className="cc-btn cc-btn--ghost">
            Command Centre
          </Link>
          <Link href="/architecture" className="cc-btn cc-btn--primary">
            Open architecture map
          </Link>
        </div>
      </header>

      <section className="os-moat">
        <h2 style={{ fontFamily: "var(--font-display)" }}>Target moat</h2>
        <p>
          multi-source evidence · probabilistic AI measurement · multi-model reasoning ·
          citation graph · entity intelligence · experiments · writer intelligence ·
          decision optimisation · execution · proprietary outcome learning
        </p>
      </section>

      <section className="os-standard">
        <h2 style={{ fontFamily: "var(--font-display)" }}>Product standard</h2>
        <p className="os-callout">{map.not_only_visibility_note}</p>
        <ul className="os-questions">
          {(map.product_questions.length
            ? map.product_questions
            : DEMO_ARCHITECTURE.product_questions
          ).map((q) => (
            <li key={q.question_key}>
              <span>{q.question_text}</span>
              {q.addressed ? (
                <em className="os-tag">addressed</em>
              ) : (
                <em className="os-tag os-tag--warn">gap</em>
              )}
            </li>
          ))}
        </ul>
        <p className="os-meta">
          Coverage {map.product_standard_coverage}% · Learning loops to PINE:{" "}
          {map.learning_loops_to_pine ? "yes" : "no"}
        </p>
      </section>

      <section className="os-grid">
        <h2 style={{ fontFamily: "var(--font-display)" }}>Subsystem surfaces</h2>
        <p className="os-honesty">
          Preview UIs call public <code>/preview</code> endpoints. Demo fallbacks apply
          if the API is unreachable. Persistence APIs require auth + Postgres migrations —
          see <code>docs/functional-status.md</code>.
        </p>
        <div className="os-cards">
          {SUBSYSTEM_LINKS.map((item) => (
            <Link key={item.href} href={item.href} className="os-card">
              <strong>{item.label}</strong>
              <span>{item.blurb}</span>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
