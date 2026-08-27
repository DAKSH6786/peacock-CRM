"use client";

import type {
  ExplainedScore,
  ImpactAction,
  PageOpportunity,
  SiteIntelligenceReport,
} from "@/lib/site-intelligence";

function ScoreFactorDetails({ score }: { score: ExplainedScore }) {
  return (
    <details className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--background)]/30 p-3">
      <summary style={{ cursor: "pointer" }}>
        <strong>{score.label}</strong> — {score.score}/100{" "}
        <span style={{ color: "var(--muted)" }}>· why did I get this score?</span>
      </summary>
      <p className="os-honesty" style={{ marginTop: "0.5rem" }}>
        {score.summary}
      </p>
      <ul className="os-questions" style={{ marginTop: "0.5rem" }}>
        {score.factors.map((f) => (
          <li key={f.metric}>
            <span>
              {f.metric.replaceAll("_", " ")} = {String(f.observed_value)} (benchmark: {String(f.benchmark)})
              <br />
              <span style={{ color: "var(--muted)", fontSize: "0.85rem" }}>{f.evidence}</span>
            </span>
            <em className="os-tag">
              +{f.score_contribution} · {f.confidence}
            </em>
          </li>
        ))}
      </ul>
    </details>
  );
}

function ActionCard({ action }: { action: ImpactAction }) {
  return (
    <article className="os-card" style={{ marginBottom: "0.85rem", display: "block" }}>
      <div className="cc-hero__actions" style={{ justifyContent: "space-between", marginTop: 0 }}>
        <strong>
          #{action.rank} {action.title}
        </strong>
        <em className="os-tag">Impact {action.impact_score}/100</em>
      </div>
      <p style={{ margin: "0.4rem 0", color: "var(--muted)" }}>{action.detail}</p>
      <p style={{ margin: "0.2rem 0", fontSize: "0.85rem" }}>
        Difficulty {action.difficulty} · SEO opportunity {action.seo_opportunity} · GEO opportunity{" "}
        {action.geo_opportunity} · Competitors winning {action.competitors_winning} · Confidence {action.confidence}
        {action.llms_showing_gap.length ? ` · LLMs showing gap: ${action.llms_showing_gap.join(", ")}` : ""}
      </p>
    </article>
  );
}

function PageCard({ page }: { page: PageOpportunity }) {
  return (
    <details className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--surface)] p-4" style={{ marginBottom: "0.75rem" }}>
      <summary style={{ cursor: "pointer" }}>
        <strong>{page.title || page.url}</strong>{" "}
        <em className="os-tag os-tag--warn" style={{ marginLeft: "0.5rem" }}>
          {page.priority}
        </em>{" "}
        <span style={{ color: "var(--muted)", fontSize: "0.85rem" }}>{page.url}</span>
      </summary>
      <dl className="os-stats" style={{ marginTop: "1rem" }}>
        <div>
          <dt>SEO</dt>
          <dd>{page.seo_score}</dd>
        </div>
        <div>
          <dt>AEO</dt>
          <dd>{page.aeo_score}</dd>
        </div>
        <div>
          <dt>GEO</dt>
          <dd>{page.geo_score}</dd>
        </div>
        <div>
          <dt>Content</dt>
          <dd>{page.content_score}</dd>
        </div>
        <div>
          <dt>Technical</dt>
          <dd>{page.technical_score}</dd>
        </div>
        <div>
          <dt>Authority</dt>
          <dd>{page.authority_score}</dd>
        </div>
        <div>
          <dt>Information Gain</dt>
          <dd>{page.information_gain_score}</dd>
        </div>
        <div>
          <dt>AI Citation Potential</dt>
          <dd>{page.ai_citation_potential}</dd>
        </div>
        <div>
          <dt>Peacock Impact</dt>
          <dd>{page.peacock_impact_score}</dd>
        </div>
      </dl>

      <h4 style={{ marginTop: "1rem" }}>What is wrong</h4>
      <ul className="lab-list">
        {page.whats_wrong.map((w) => (
          <li key={w}>{w}</li>
        ))}
      </ul>
      <h4 style={{ marginTop: "1rem" }}>Why it matters</h4>
      <ul className="lab-list">
        {page.why_it_matters.map((w) => (
          <li key={w}>{w}</li>
        ))}
      </ul>
      <h4 style={{ marginTop: "1rem" }}>Evidence found</h4>
      <ul className="lab-list">
        {page.evidence_found.map((w) => (
          <li key={w}>{w}</li>
        ))}
      </ul>
      <h4 style={{ marginTop: "1rem" }}>Competitor doing it better</h4>
      <p className="os-honesty">{page.competitor_doing_better}</p>
      <h4 style={{ marginTop: "1rem" }}>FIX WITH PEACOCK (draft — review before publishing)</h4>
      <ul className="lab-list">
        {page.exact_fix.map((fix, i) => (
          <li key={i} style={{ whiteSpace: "pre-wrap" }}>
            {fix}
          </li>
        ))}
      </ul>
      <p style={{ marginTop: "0.75rem", fontSize: "0.85rem", color: "var(--muted)" }}>
        Expected impact: {page.expected_impact} · Difficulty: {page.difficulty} · Confidence: {page.confidence}
      </p>
    </details>
  );
}

export function SiteIntelligenceReportView({ report }: { report: SiteIntelligenceReport }) {
  const gb = report.geo_score_breakdown;

  return (
    <div>
      <section>
        <h2 style={{ fontFamily: "var(--font-display)" }}>Executive Summary</h2>
        <p className="os-callout">{report.executive_summary}</p>
        <p className="os-honesty">{report.disclaimer}</p>
      </section>

      <section style={{ marginTop: "2rem" }}>
        <h2 style={{ fontFamily: "var(--font-display)" }}>Peacock Visibility Score</h2>
        <dl className="os-stats">
          <div>
            <dt>Peacock Visibility</dt>
            <dd>{report.peacock_visibility_score}</dd>
          </div>
          <div>
            <dt>SEO Score</dt>
            <dd>{report.seo_score}</dd>
          </div>
          <div>
            <dt>AEO Score</dt>
            <dd>{report.aeo_score}</dd>
          </div>
          <div>
            <dt>GEO Score</dt>
            <dd>{report.geo_score}</dd>
          </div>
          <div>
            <dt>Information Gain</dt>
            <dd>{report.information_gain_score}</dd>
          </div>
        </dl>
      </section>

      <section style={{ marginTop: "2rem" }}>
        <h2 style={{ fontFamily: "var(--font-display)" }}>GEO Score — transparent breakdown (example page)</h2>
        <p className="os-honesty">{gb.formula}</p>
        <div style={{ display: "grid", gap: "0.6rem", marginTop: "0.75rem" }}>
          <ScoreFactorDetails score={gb.entity_authority} />
          <ScoreFactorDetails score={gb.citation_readiness} />
          <ScoreFactorDetails score={gb.answerability} />
          <ScoreFactorDetails score={gb.evidence} />
          <ScoreFactorDetails score={gb.topical_coverage} />
          <ScoreFactorDetails score={gb.technical_ai_accessibility} />
          <ScoreFactorDetails score={gb.brand_authority} />
        </div>
      </section>

      <section style={{ marginTop: "2rem" }}>
        <h2 style={{ fontFamily: "var(--font-display)" }}>Technical Health</h2>
        <ul className="os-questions">
          <li>
            <span>Pages with broken status (4xx/5xx)</span>
            <em className="os-tag">{String(report.technical_health.pages_with_broken_status)}</em>
          </li>
          <li>
            <span>JavaScript-heavy pages</span>
            <em className="os-tag">{String(report.technical_health.pages_js_heavy)}</em>
          </li>
          <li>
            <span>Pages missing schema.org data</span>
            <em className="os-tag">{String(report.technical_health.pages_missing_schema)}</em>
          </li>
          <li>
            <span>robots.txt present</span>
            <em className="os-tag">{String(report.technical_health.robots_txt_present)}</em>
          </li>
          <li>
            <span>Sitemap URLs found</span>
            <em className="os-tag">{String(report.technical_health.sitemap_urls_found)}</em>
          </li>
          <li>
            <span>Core Web Vitals</span>
            <em className="os-tag os-tag--warn">{String(report.technical_health.core_web_vitals)}</em>
          </li>
        </ul>
      </section>

      <section style={{ marginTop: "2rem" }}>
        <h2 style={{ fontFamily: "var(--font-display)" }}>AI Visibility — per-platform GEO Score</h2>
        <p className="os-honesty">{report.ai_citation_presence.note}</p>
        <div className="os-cards">
          {report.ai_visibility.map((a) => (
            <article key={a.engine_code} className="os-card">
              <strong>{a.engine_name}</strong>
              {a.available ? (
                <span>GEO Score: {a.score}/100 · brand mentioned: {String(a.brand_mentioned)}</span>
              ) : (
                <span style={{ color: "var(--accent)" }}>{a.reason_unavailable}</span>
              )}
            </article>
          ))}
        </div>
      </section>

      <section style={{ marginTop: "2rem" }}>
        <h2 style={{ fontFamily: "var(--font-display)" }}>LLM-by-LLM Visibility — platform recommendations</h2>
        {report.llm_by_llm_visibility.map((rec) => (
          <article key={rec.engine_code} className="os-card" style={{ marginBottom: "0.75rem", display: "block" }}>
            <strong>{rec.platform_label}</strong>
            <ul className="lab-list" style={{ marginTop: "0.5rem" }}>
              {rec.opportunities.map((o) => (
                <li key={o}>{o}</li>
              ))}
            </ul>
          </article>
        ))}
      </section>

      <section style={{ marginTop: "2rem" }}>
        <h2 style={{ fontFamily: "var(--font-display)" }}>Critical Issues</h2>
        <ul className="os-questions">
          {report.critical_issues.length ? (
            report.critical_issues.map((issue) => (
              <li key={issue}>
                <span>{issue}</span>
              </li>
            ))
          ) : (
            <li>
              <span>No critical issues detected in this crawl.</span>
            </li>
          )}
        </ul>
      </section>

      <section style={{ marginTop: "2rem" }}>
        <h2 style={{ fontFamily: "var(--font-display)" }}>TOP 10 ACTIONS TO TAKE</h2>
        <p className="os-honesty">
          Ranked by Peacock Impact Score = Visibility Opportunity × Business Intent × Competitive Gap ×
          Fix Confidence ÷ Implementation Difficulty — not raw technical severity.
        </p>
        {report.top_actions.map((action) => (
          <ActionCard key={action.rank} action={action} />
        ))}
      </section>

      <section style={{ marginTop: "2rem" }}>
        <h2 style={{ fontFamily: "var(--font-display)" }}>Keyword Opportunities — LLM Keyword Map</h2>
        <p className="os-honesty">
          Terminology that recurs inside LLM answers, not Google search volume. Universal terms appear
          across 3+ platforms; platform-specific terms are strongly tied to one model.
        </p>
        <div style={{ overflowX: "auto", marginTop: "0.75rem" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.9rem" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border)" }}>
                <th style={{ textAlign: "left", padding: "0.4rem" }}>Term</th>
                <th style={{ textAlign: "left", padding: "0.4rem" }}>Platforms</th>
                <th style={{ textAlign: "left", padding: "0.4rem" }}>Opportunity</th>
              </tr>
            </thead>
            <tbody>
              {report.keyword_opportunities.entries.slice(0, 15).map((entry) => (
                <tr key={entry.term} style={{ borderBottom: "1px solid rgba(36,48,73,0.5)" }}>
                  <td style={{ padding: "0.4rem" }}>{entry.term}</td>
                  <td style={{ padding: "0.4rem", color: "var(--muted)" }}>
                    {Object.entries(entry.per_engine_present)
                      .filter(([, present]) => present)
                      .map(([code]) => code)
                      .join(", ") || "—"}
                  </td>
                  <td style={{ padding: "0.4rem" }}>{entry.opportunity}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <h3 style={{ marginTop: "1.5rem" }}>Universal LLM Terms</h3>
        <p>{report.keyword_opportunities.universal_terms.join(", ") || "None identified yet."}</p>

        <h3 style={{ marginTop: "1rem" }}>Platform-Specific Terms</h3>
        <ul className="os-questions">
          {Object.entries(report.keyword_opportunities.platform_specific_terms).map(([platform, terms]) => (
            <li key={platform}>
              <span>{platform}</span>
              <em className="os-tag">{terms.join(", ")}</em>
            </li>
          ))}
        </ul>

        <h3 style={{ marginTop: "1rem" }}>Competitive Association Gap</h3>
        {report.keyword_opportunities.competitive_association_gaps.length ? (
          report.keyword_opportunities.competitive_association_gaps.map((gap) => (
            <p key={gap.competitor} className="os-callout">
              {gap.competitor} → {gap.competitor_topics.join(" + ") || "no topics detected"}
              <br />
              Your brand → {gap.brand_topics.join(" + ") || "no topics detected"}
              <br />
              Missing: {gap.missing_topics.join(", ") || "none detected"}
            </p>
          ))
        ) : (
          <p className="os-honesty">
            No competitive association gap detected yet — this strengthens as more live LLM plugins are
            connected.
          </p>
        )}
      </section>

      <section style={{ marginTop: "2rem" }}>
        <h2 style={{ fontFamily: "var(--font-display)" }}>Entity Opportunities</h2>
        <p>{report.entity_opportunities.join(", ") || "None identified yet."}</p>
      </section>

      <section style={{ marginTop: "2rem" }}>
        <h2 style={{ fontFamily: "var(--font-display)" }}>Content Gaps</h2>
        <p>{report.content_gaps.join(", ") || "None identified yet."}</p>
      </section>

      <section style={{ marginTop: "2rem" }}>
        <h2 style={{ fontFamily: "var(--font-display)" }}>Citation / Source Opportunities</h2>
        <p>{report.citation_opportunities.join(", ") || "None observed yet."}</p>
      </section>

      <section style={{ marginTop: "2rem" }}>
        <h2 style={{ fontFamily: "var(--font-display)" }}>Backlink Opportunities</h2>
        <p className="os-honesty">{report.backlink_opportunities}</p>
      </section>

      <section style={{ marginTop: "2rem" }}>
        <h2 style={{ fontFamily: "var(--font-display)" }}>Top Performing Pages</h2>
        {report.top_performing_pages.map((p) => (
          <PageCard key={p.url} page={p} />
        ))}
      </section>

      <section style={{ marginTop: "2rem" }}>
        <h2 style={{ fontFamily: "var(--font-display)" }}>Weak Pages</h2>
        {report.weak_pages.map((p) => (
          <PageCard key={p.url} page={p} />
        ))}
      </section>

      <section style={{ marginTop: "2rem" }}>
        <h2 style={{ fontFamily: "var(--font-display)" }}>Competitor Comparison</h2>
        {report.competitor_gap.available ? (
          <>
            <h3>Why the competitor is winning</h3>
            <ul className="lab-list">
              {report.competitor_gap.why_competitor_is_winning.map((w) => (
                <li key={w}>{w}</li>
              ))}
            </ul>
          </>
        ) : (
          <p className="os-honesty">{report.competitor_gap.reason_unavailable}</p>
        )}
        <dl className="os-stats" style={{ marginTop: "1rem" }}>
          {[
            ["SEO visibility", report.competitor_gap.seo_visibility],
            ["Content coverage", report.competitor_gap.content_coverage],
            ["Entity coverage", report.competitor_gap.entity_coverage],
            ["Structured data", report.competitor_gap.structured_data],
            ["Question coverage", report.competitor_gap.question_coverage],
            ["AI mentions", report.competitor_gap.ai_mentions],
            ["Backlink signals", report.competitor_gap.backlink_signals],
          ].map(([label, value]) => (
            <div key={label}>
              <dt>{label}</dt>
              <dd style={{ fontSize: "0.85rem" }}>{value}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section style={{ marginTop: "2rem" }}>
        <h2 style={{ fontFamily: "var(--font-display)" }}>30 / 60 / 90-Day Action Plan</h2>
        <h3>30-Day</h3>
        {report.thirty_day_plan.length ? report.thirty_day_plan.map((a) => <ActionCard key={`30-${a.rank}`} action={a} />) : <p className="os-honesty">No 30-day actions ranked yet.</p>}
        <h3 style={{ marginTop: "1rem" }}>60-Day</h3>
        {report.sixty_day_plan.length ? report.sixty_day_plan.map((a) => <ActionCard key={`60-${a.rank}`} action={a} />) : <p className="os-honesty">No 60-day actions ranked yet.</p>}
        <h3 style={{ marginTop: "1rem" }}>90-Day</h3>
        {report.ninety_day_plan.length ? report.ninety_day_plan.map((a) => <ActionCard key={`90-${a.rank}`} action={a} />) : <p className="os-honesty">No 90-day actions ranked yet.</p>}
      </section>

      <section style={{ marginTop: "2rem", paddingBottom: "1rem" }}>
        <h2 style={{ fontFamily: "var(--font-display)" }}>Data Availability</h2>
        <h3>Genuinely measured</h3>
        <ul className="lab-list">
          {report.data_availability.measured.map((m) => (
            <li key={m}>{m}</li>
          ))}
        </ul>
        <h3 style={{ marginTop: "1rem" }}>Data unavailable</h3>
        <ul className="lab-list">
          {report.data_availability.unavailable.map((m) => (
            <li key={m}>{m}</li>
          ))}
        </ul>
      </section>
    </div>
  );
}
