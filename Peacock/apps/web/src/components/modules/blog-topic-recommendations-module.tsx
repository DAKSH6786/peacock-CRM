"use client";

import { useEffect, useState } from "react";

import { ModuleShell } from "@/components/module-shell";
import {
  DEMO_BLOG_TOPIC_RECOMMENDATIONS,
  fetchBlogTopicRecommendations,
  type BlogTopicRecommendations,
} from "@/lib/blog-topic-recommendations";

export function BlogTopicRecommendationsModule() {
  const [data, setData] = useState<BlogTopicRecommendations>(DEMO_BLOG_TOPIC_RECOMMENDATIONS);

  useEffect(() => {
    let active = true;
    void fetchBlogTopicRecommendations("Acme").then((result) => {
      if (active) setData(result);
    });
    return () => {
      active = false;
    };
  }, []);

  return (
    <ModuleShell
      title="Blog & Topic Recommendations"
      kicker="Module · Peacock Content Lab"
      lede="Ranks proposed content by SEO/AEO/GEO opportunity, information gain, content moat, and generative citability — not keyword volume alone."
    >
      <p className="os-honesty">{data.citability_disclaimer}</p>

      {data.top_recommendation ? (
        <div className="os-callout" style={{ marginTop: "1.5rem" }}>
          Top recommendation: <strong>{data.top_recommendation.title}</strong> — priority{" "}
          {data.top_recommendation.lab_priority_score}/100
        </div>
      ) : null}

      <section className="os-cards" style={{ marginTop: "1.5rem" }}>
        {data.proposals.map((p) => (
          <article key={p.slug} className="os-card">
            <strong>{p.title}</strong>
            <span>
              {p.content_format.replaceAll("_", " ")}
              {p.angle ? ` — ${p.angle}` : ""}
            </span>
            <span>
              Priority {p.lab_priority_score}/100 · Info gain {p.information_gain_score}/100 ·
              Moat {p.content_moat_score}/100 · Citability {p.generative_citability_score}/100
            </span>
            <span>{p.recommendation_summary}</span>
          </article>
        ))}
      </section>

      <section style={{ marginTop: "2.5rem", paddingTop: "1.5rem", borderTop: "1px solid var(--border)" }}>
        <h2 style={{ fontFamily: "var(--font-display)" }}>Content moat priors by format</h2>
        <dl className="os-stats">
          {data.example_moat.map((m) => (
            <div key={m.content_format}>
              <dt>{m.content_format.replaceAll("_", " ")}</dt>
              <dd>{m.moat_prior}</dd>
            </div>
          ))}
        </dl>
      </section>
    </ModuleShell>
  );
}
