"use client";

import { useEffect, useState } from "react";

import { ModuleShell } from "@/components/module-shell";
import {
  DEMO_AEO_AUDIT,
  DEMO_GEO_AUDIT,
  DEMO_SEO_AUDIT,
  fetchAeoAuditPreview,
  fetchGeoAuditPreview,
  fetchSeoAuditPreview,
  type AeoAuditPreview,
  type GeoAuditPreview,
  type SeoAuditPreview,
} from "@/lib/seo-aeo-geo-audit";

export function SeoAeoGeoAuditModule() {
  const [seo, setSeo] = useState<SeoAuditPreview>(DEMO_SEO_AUDIT);
  const [aeo, setAeo] = useState<AeoAuditPreview>(DEMO_AEO_AUDIT);
  const [geo, setGeo] = useState<GeoAuditPreview>(DEMO_GEO_AUDIT);

  useEffect(() => {
    let active = true;
    void fetchSeoAuditPreview("Acme").then((data) => active && setSeo(data));
    void fetchAeoAuditPreview("Acme").then((data) => active && setAeo(data));
    void fetchGeoAuditPreview("Acme").then((data) => active && setGeo(data));
    return () => {
      active = false;
    };
  }, []);

  return (
    <ModuleShell
      title="Website SEO/AEO/GEO Audit"
      kicker="Module · Peacock SEO Engine + AEO + GEO Lab"
      lede="One audit across classic search (SEO), answer engines (AEO), and generative engines (GEO) — deterministic scoring first, cautious causality always."
    >
      <section>
        <h2 style={{ fontFamily: "var(--font-display)" }}>SEO</h2>
        <p className="os-callout">{seo.summary}</p>
        <dl className="os-stats">
          <div>
            <dt>Peacock SEO Score</dt>
            <dd>{seo.peacock_seo_score.score}</dd>
          </div>
          <div>
            <dt>Confidence</dt>
            <dd>{(seo.peacock_seo_score.confidence * 100).toFixed(0)}%</dd>
          </div>
        </dl>
        <ul className="os-questions">
          {seo.recommendations.slice(0, 5).map((rec) => (
            <li key={rec.code + rec.title}>
              <span>{rec.title}</span>
              <em className="os-tag">{rec.priority}</em>
            </li>
          ))}
        </ul>
      </section>

      <section style={{ marginTop: "2.5rem", paddingTop: "1.5rem", borderTop: "1px solid var(--border)" }}>
        <h2 style={{ fontFamily: "var(--font-display)" }}>AEO — Answer Engine Optimisation</h2>
        <p className="os-honesty">{aeo.scoring_note}</p>
        <dl className="os-stats">
          <div>
            <dt>AEO score</dt>
            <dd>{aeo.aeo_score}</dd>
          </div>
          <div>
            <dt>FAQ coverage</dt>
            <dd>{aeo.faq_coverage_score}</dd>
          </div>
          <div>
            <dt>Citation readiness</dt>
            <dd>{aeo.citation_readiness_score}</dd>
          </div>
          <div>
            <dt>Entity coverage</dt>
            <dd>{aeo.entity_coverage}</dd>
          </div>
          <div>
            <dt>Question coverage</dt>
            <dd>{aeo.question_coverage}</dd>
          </div>
        </dl>
        <ul className="os-questions">
          {aeo.recommendations.map((rec) => (
            <li key={rec}>
              <span>{rec}</span>
            </li>
          ))}
        </ul>
      </section>

      <section style={{ marginTop: "2.5rem", paddingTop: "1.5rem", borderTop: "1px solid var(--border)" }}>
        <h2 style={{ fontFamily: "var(--font-display)" }}>GEO — Generative Engine Optimisation</h2>
        <p className="os-callout">{geo.hypothesis}</p>
        <dl className="os-stats">
          <div>
            <dt>Causality ceiling</dt>
            <dd>{geo.overall_causality_level.replaceAll("_", " ")}</dd>
          </div>
        </dl>
        <ul className="os-questions">
          {geo.design_features.map((f) => (
            <li key={f}>
              <span>{f.replaceAll("_", " ")}</span>
            </li>
          ))}
        </ul>
        <p className="os-honesty">{geo.overall_summary}</p>
        <aside className="lab-warning" role="note">
          {geo.causality_warning}
        </aside>
      </section>
    </ModuleShell>
  );
}
