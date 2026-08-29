"use client";

import { useEffect, useState } from "react";

import { ModuleShell } from "@/components/module-shell";
import { Button } from "@/components/ui/button";
import { DEMO_GEO_INTELLIGENCE, fetchGeoIntelligencePreview, type GeoIntelligenceReport } from "@/lib/geo-intelligence";
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
import { analyzeSite, SiteIntelligenceError, type SiteIntelligenceReport } from "@/lib/site-intelligence";

import { SiteIntelligenceReportView } from "./site-intelligence-report";

export function SeoAeoGeoAuditModule() {
  const [seo, setSeo] = useState<SeoAuditPreview>(DEMO_SEO_AUDIT);
  const [aeo, setAeo] = useState<AeoAuditPreview>(DEMO_AEO_AUDIT);
  const [geo, setGeo] = useState<GeoAuditPreview>(DEMO_GEO_AUDIT);
  const [geoIntelligence, setGeoIntelligence] = useState<GeoIntelligenceReport>(DEMO_GEO_INTELLIGENCE);

  const [url, setUrl] = useState("");
  const [competitorUrl, setCompetitorUrl] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);
  const [report, setReport] = useState<SiteIntelligenceReport | null>(null);

  useEffect(() => {
    let active = true;
    void fetchSeoAuditPreview("Acme").then((data) => active && setSeo(data));
    void fetchAeoAuditPreview("Acme").then((data) => active && setAeo(data));
    void fetchGeoAuditPreview("Acme").then((data) => active && setGeo(data));
    void fetchGeoIntelligencePreview("Acme").then((data) => active && setGeoIntelligence(data));
    return () => {
      active = false;
    };
  }, []);

  const runAnalysis = async () => {
    if (!url.trim()) {
      setAnalyzeError("Enter a website URL to analyse.");
      return;
    }
    setAnalyzing(true);
    setAnalyzeError(null);
    try {
      const result = await analyzeSite(url.trim(), {
        competitorUrl: competitorUrl.trim() || undefined,
        maxPages: 8,
      });
      setReport(result);
    } catch (err) {
      setAnalyzeError(err instanceof SiteIntelligenceError ? err.message : "Analysis failed. Please try again.");
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <ModuleShell
      title="Website SEO/AEO/GEO Audit"
      kicker="Module · Peacock Site Intelligence — enterprise SEO + GEO reporting"
      lede="Crawl → Understand → Benchmark → Query LLMs → Extract AI Signals → Compare Competitors → Identify Gaps → Prioritize Opportunities → Generate Exact Fixes."
    >
      <section
        className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--surface)] p-6"
        aria-labelledby="analyze-heading"
      >
        <h2 id="analyze-heading" style={{ fontFamily: "var(--font-display)" }}>
          Run a real Peacock analysis
        </h2>
        <p className="os-honesty">
          Crawls the pages you specify in real time and queries the connected AI plugins — nothing here
          is pre-recorded demo data.
        </p>
        <form
          className="mt-4 grid gap-3 md:grid-cols-[1fr_1fr_auto]"
          onSubmit={(e) => {
            e.preventDefault();
            void runAnalysis();
          }}
        >
          <label className="block text-sm">
            <span className="text-[var(--muted)]">Website URL</span>
            <input
              className="mt-1 w-full rounded-[var(--radius)] border border-[var(--border)] bg-transparent px-3 py-2"
              placeholder="https://example.com"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
          </label>
          <label className="block text-sm">
            <span className="text-[var(--muted)]">Competitor URL (optional)</span>
            <input
              className="mt-1 w-full rounded-[var(--radius)] border border-[var(--border)] bg-transparent px-3 py-2"
              placeholder="https://competitor.com"
              value={competitorUrl}
              onChange={(e) => setCompetitorUrl(e.target.value)}
            />
          </label>
          <div className="flex items-end">
            <Button type="submit" disabled={analyzing}>
              {analyzing ? "Analyzing…" : "Run Peacock Analysis"}
            </Button>
          </div>
        </form>
        {analyzing ? (
          <p className="mt-3 text-sm text-[var(--muted)]">
            Crawling pages, running SEO/AEO/GEO scoring, and broadcasting to AI plugins — this can take
            up to a minute for a live LLM run.
          </p>
        ) : null}
        {analyzeError ? <p className="mt-3 text-sm text-[var(--danger)]">{analyzeError}</p> : null}
      </section>

      {report ? (
        <div style={{ marginTop: "2.5rem" }}>
          <SiteIntelligenceReportView report={report} />
        </div>
      ) : (
        <>
          <p className="os-honesty" style={{ marginTop: "2.5rem" }}>
            Example preview below (Acme demo data) — run a real analysis above to replace it with your
            own site&apos;s report.
          </p>
          <section style={{ marginTop: "1rem" }}>
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

      <section style={{ marginTop: "2.5rem", paddingTop: "1.5rem", borderTop: "1px solid var(--border)" }}>
        <h2 style={{ fontFamily: "var(--font-display)" }}>AI platform signals (GEO Intelligence Layer)</h2>
        <p className="os-honesty">
          Extracted from the same multi-LLM broadcast used by{" "}
          <a href="/modules/geo-intelligence">Peacock GEO Intelligence</a> — {geoIntelligence.disclaimer}
        </p>
        <h3 style={{ marginTop: "1rem" }}>Missing topics across AI platforms</h3>
        <ul className="os-questions">
          {geoIntelligence.missing_topics.map((topic) => (
            <li key={topic}>
              <span>{topic}</span>
              <em className="os-tag os-tag--warn">gap</em>
            </li>
          ))}
        </ul>
        <h3 style={{ marginTop: "1.5rem" }}>Domains cited by AI platforms</h3>
        <ul className="os-questions">
          {geoIntelligence.citations.slice(0, 6).map((c) => (
            <li key={c.url}>
              <span>{c.domain}</span>
              <em className="os-tag">
                {c.source_class} · {c.engine_code}
              </em>
            </li>
          ))}
        </ul>
      </section>
        </>
      )}
    </ModuleShell>
  );
}
