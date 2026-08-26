"use client";

import { useEffect, useState } from "react";

import { ModuleShell } from "@/components/module-shell";
import { DEMO_GEO_INTELLIGENCE, fetchGeoIntelligencePreview, type GeoIntelligenceReport } from "@/lib/geo-intelligence";
import {
  DEMO_KEYWORD_BACKLINK_RECOMMENDATIONS,
  fetchKeywordBacklinkRecommendations,
  type KeywordBacklinkRecommendations,
} from "@/lib/keyword-backlink-recommendations";

const TYPE_LABEL: Record<string, string> = {
  high_value_topic_available: "Keyword opportunity",
  search_demand_shifted: "Keyword opportunity",
  backlink_source_gained_influence: "Backlink opportunity",
  new_citation_source_emerged: "Backlink opportunity",
  competitor_content_outdated: "Content gap",
  existing_article_decaying: "Refresh opportunity",
};

export function KeywordBacklinkRecommendationsModule() {
  const [data, setData] = useState<KeywordBacklinkRecommendations>(
    DEMO_KEYWORD_BACKLINK_RECOMMENDATIONS,
  );
  const [geoIntelligence, setGeoIntelligence] = useState<GeoIntelligenceReport>(DEMO_GEO_INTELLIGENCE);

  useEffect(() => {
    let active = true;
    void fetchKeywordBacklinkRecommendations("Acme").then((result) => {
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
      title="Keyword & Backlink Recommendations"
      kicker="Module · Peacock Opportunity Engine"
      lede="Always-on, explainable ranking of keyword and backlink opportunities — impact, urgency, confidence, expected value, and difficulty, never a frozen forever-formula."
    >
      <p className="os-callout">{data.summary}</p>
      <p className="os-honesty">{data.always_on_note}</p>

      <section style={{ marginTop: "1.5rem" }}>
        {data.opportunities.map((opp) => (
          <article
            key={opp.opportunity_key}
            className="os-card"
            style={{ marginBottom: "0.85rem", display: "block" }}
          >
            <div className="cc-hero__actions" style={{ justifyContent: "space-between", marginTop: 0 }}>
              <strong>
                #{opp.rank} · {opp.title}
              </strong>
              <em className="os-tag">{opp.opportunity_score.toFixed(0)}/100</em>
            </div>
            <span>{TYPE_LABEL[opp.opportunity_type] ?? opp.opportunity_type.replaceAll("_", " ")}</span>
            <p style={{ margin: "0.5rem 0", color: "var(--muted)" }}>{opp.description}</p>
            <p style={{ margin: "0.35rem 0" }}>
              <span style={{ color: "var(--muted)" }}>Recommended action · </span>
              {opp.recommended_action}
            </p>
            <p style={{ margin: "0.35rem 0", fontSize: "0.85rem", color: "var(--muted)" }}>
              Impact {opp.impact} · Urgency {opp.urgency} · Confidence {opp.confidence} · Difficulty{" "}
              {opp.difficulty} · Expected value {opp.expected_value}
            </p>
          </article>
        ))}
      </section>

      <p className="os-honesty" style={{ marginTop: "1.5rem" }}>
        {data.methodology_note}
      </p>

      <section style={{ marginTop: "2.5rem", paddingTop: "1.5rem", borderTop: "1px solid var(--border)" }}>
        <h2 style={{ fontFamily: "var(--font-display)" }}>Keywords &amp; citation domains from AI platforms (GEO Intelligence)</h2>
        <p className="os-honesty">
          Recurring keywords/phrases and cited domains observed across ChatGPT, Gemini, Claude,
          Perplexity, and DeepSeek responses — sourced from{" "}
          <a href="/modules/geo-intelligence">Peacock GEO Intelligence</a>. These are AI visibility
          signals, not guaranteed backlink targets.
        </p>
        <h3 style={{ marginTop: "1rem" }}>Recurring keywords across AI platforms</h3>
        <ul className="os-questions">
          {geoIntelligence.keywords.slice(0, 8).map((k) => (
            <li key={k.phrase}>
              <span>{k.phrase}</span>
              <em className="os-tag">
                {k.frequency}× · {k.engine_codes.length} platform(s)
              </em>
            </li>
          ))}
        </ul>
        <h3 style={{ marginTop: "1.5rem" }}>Domains cited by AI platforms (backlink/citation targets)</h3>
        <ul className="os-questions">
          {geoIntelligence.citations.slice(0, 8).map((c) => (
            <li key={c.url}>
              <span>{c.domain}</span>
              <em className="os-tag">
                {c.source_class} · {c.engine_code}
              </em>
            </li>
          ))}
        </ul>
      </section>
    </ModuleShell>
  );
}
