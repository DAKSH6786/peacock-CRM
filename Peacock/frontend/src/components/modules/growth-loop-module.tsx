"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  approveExpertTask,
  assignExpertTask,
  GrowthLoopError,
  markReadyToPublish,
  runGrowthLoop,
  startExpertReview,
  type AgentResult,
  type ExpertTask,
  type GrowthLoopReport,
  type Opportunity,
} from "@/lib/growth-loop";

function StageTracker({ stages }: { stages: GrowthLoopReport["stages"] }) {
  return (
    <ol className="mt-4 grid gap-2 md:grid-cols-2 lg:grid-cols-3" style={{ listStyle: "none", padding: 0 }}>
      {stages.map((s, i) => (
        <li
          key={s.stage}
          className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--background)]/30 p-3"
          style={{ fontSize: "0.85rem" }}
        >
          <strong>
            {i + 1}. {s.stage.replaceAll("_", " ")}
          </strong>{" "}
          <em className={`os-tag ${s.status === "skipped" ? "os-tag--warn" : ""}`}>{s.status}</em>
          <p style={{ margin: "0.3rem 0 0", color: "var(--muted)" }}>{s.detail}</p>
        </li>
      ))}
    </ol>
  );
}

function ExecutiveSummaryPanel({ report }: { report: GrowthLoopReport }) {
  const es = report.executive_summary;
  return (
    <section className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--surface)] p-6 mt-6">
      <h2 style={{ fontFamily: "var(--font-display)" }}>Peacock Executive Dashboard</h2>
      <dl className="os-stats" style={{ marginTop: "1rem" }}>
        <div>
          <dt>Peacock Visibility Score</dt>
          <dd>{es.peacock_visibility_score}</dd>
        </div>
        <div>
          <dt>SEO</dt>
          <dd>{es.seo}</dd>
        </div>
        <div>
          <dt>AEO</dt>
          <dd>{es.aeo}</dd>
        </div>
        <div>
          <dt>GEO</dt>
          <dd>{es.geo}</dd>
        </div>
        <div>
          <dt>AI Visibility (share of answer)</dt>
          <dd>{es.ai_visibility !== null ? `${Math.round(es.ai_visibility * 100)}%` : "Data unavailable"}</dd>
        </div>
        <div>
          <dt>Entity Authority</dt>
          <dd>{es.entity_authority}</dd>
        </div>
        <div>
          <dt>Content Authority (Evidence)</dt>
          <dd>{es.content_authority}</dd>
        </div>
        <div>
          <dt>Information Gain</dt>
          <dd>{es.information_gain}</dd>
        </div>
        <div>
          <dt>Citation Gaps Found</dt>
          <dd>{es.citation_authority}</dd>
        </div>
      </dl>

      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <div>
          <h4>What changed?</h4>
          <p className="os-honesty">{es.what_changed}</p>
        </div>
        <div>
          <h4>Why?</h4>
          <p className="os-honesty">{es.why}</p>
        </div>
        <div>
          <h4>What should we do next?</h4>
          <p className="os-honesty">{es.what_should_we_do_next}</p>
        </div>
        <div>
          <h4>Competitive position</h4>
          <p className="os-honesty">{es.competitive_position}</p>
        </div>
        <div>
          <h4>Which agent is working?</h4>
          <p className="os-honesty">{es.which_agent_is_working.join(", ")}</p>
        </div>
        <div>
          <h4>Requires human approval?</h4>
          <p className="os-honesty">{es.requires_human_approval.length ? `${es.requires_human_approval.length} task(s) pending review.` : "Nothing pending."}</p>
        </div>
        <div>
          <h4>What worked?</h4>
          <p className="os-honesty">{es.what_worked}</p>
        </div>
        <div>
          <h4>What failed?</h4>
          <p className="os-honesty">{es.what_failed}</p>
        </div>
      </div>
    </section>
  );
}

function OpportunityCard({ opportunity, rank }: { opportunity: Opportunity; rank: number }) {
  return (
    <article className="os-card" style={{ marginBottom: "0.75rem", display: "block" }}>
      <div className="cc-hero__actions" style={{ justifyContent: "space-between", marginTop: 0 }}>
        <strong>
          #{rank} {opportunity.action}
        </strong>
        <em className="os-tag">Impact {opportunity.peacock_impact_score}/100 · {opportunity.priority}</em>
      </div>
      <p style={{ margin: "0.4rem 0", color: "var(--muted)" }}>{opportunity.reason}</p>
      <p style={{ margin: "0.2rem 0", fontSize: "0.85rem" }}>
        SEO {opportunity.seo_opportunity} · AEO {opportunity.aeo_opportunity} · GEO {opportunity.geo_opportunity} · AI
        Visibility {opportunity.ai_visibility_opportunity} · Business value {opportunity.business_value} · Competitor
        gap {opportunity.competitor_gap} · Difficulty {opportunity.implementation_difficulty} · Confidence{" "}
        {opportunity.confidence}
      </p>
    </article>
  );
}

function AgentResultCard({ result }: { result: AgentResult }) {
  return (
    <details className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--surface)] p-4" style={{ marginBottom: "0.6rem" }}>
      <summary style={{ cursor: "pointer" }}>
        <strong>{result.agent_name}</strong> — {result.summary}
      </summary>
      {result.findings.length > 0 && (
        <>
          <h4 style={{ marginTop: "0.8rem" }}>Findings</h4>
          <ul className="lab-list">
            {result.findings.map((f) => (
              <li key={f}>{f}</li>
            ))}
          </ul>
        </>
      )}
      {result.tasks.length > 0 && (
        <>
          <h4 style={{ marginTop: "0.8rem" }}>Tasks prepared</h4>
          <ul className="lab-list">
            {result.tasks.map((t) => (
              <li key={t.title}>
                <strong>{t.title}</strong> ({t.priority}) — {t.detail}
              </li>
            ))}
          </ul>
        </>
      )}
      <p className="os-honesty" style={{ marginTop: "0.6rem" }}>
        {result.guardrail_note}
      </p>
    </details>
  );
}

function ExpertTaskPanel({ task: initialTask }: { task: ExpertTask }) {
  const [task, setTask] = useState(initialTask);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handle = async (action: () => Promise<ExpertTask>) => {
    setBusy(true);
    setError(null);
    try {
      setTask(await action());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--surface)] p-6 mt-6">
      <h2 style={{ fontFamily: "var(--font-display)" }}>Peacock Experts — {task.title}</h2>
      <p className="os-honesty">
        Workflow: AI Generated → Human Assigned → Review → Changes Requested → Revised → Approved → Ready to
        Publish. Current status: <strong>{task.status}</strong>
      </p>
      {error && <p style={{ color: "var(--danger, #d33)" }}>{error}</p>}
      <div className="cc-hero__actions" style={{ marginTop: "0.8rem" }}>
        {task.status === "ai_generated" && (
          <Button disabled={busy} onClick={() => handle(() => assignExpertTask(task.task_id, "Jane Doe", "seo_expert"))}>
            Assign to SEO Expert
          </Button>
        )}
        {task.status === "human_assigned" && (
          <Button disabled={busy} onClick={() => handle(() => startExpertReview(task.task_id))}>
            Start Review
          </Button>
        )}
        {task.status === "in_review" && (
          <Button disabled={busy} onClick={() => handle(() => approveExpertTask(task.task_id, "Jane Doe"))}>
            Approve
          </Button>
        )}
        {task.status === "approved" && (
          <Button disabled={busy} onClick={() => handle(() => markReadyToPublish(task.task_id))}>
            Mark Ready to Publish
          </Button>
        )}
      </div>
      {task.assignee && (
        <p style={{ fontSize: "0.85rem", marginTop: "0.6rem" }}>
          Assigned to {task.assignee} ({task.assignee_role})
        </p>
      )}
      {task.approved_by && (
        <p style={{ fontSize: "0.85rem" }}>
          Approved by {task.approved_by} at {task.approved_at}
        </p>
      )}
    </section>
  );
}

export function GrowthLoopModule() {
  const [url, setUrl] = useState("");
  const [competitorUrl, setCompetitorUrl] = useState("");
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<GrowthLoopReport | null>(null);

  const run = async () => {
    if (!url.trim()) {
      setError("Enter a website URL to run the Growth Loop.");
      return;
    }
    setRunning(true);
    setError(null);
    try {
      const result = await runGrowthLoop(url.trim(), { competitorUrl: competitorUrl.trim() || undefined, maxPages: 6 });
      setReport(result);
    } catch (err) {
      setError(err instanceof GrowthLoopError ? err.message : "Growth Loop run failed. Please try again.");
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="cc-shell">
      <p className="cc-hero__kicker">Flagship module · Peacock Growth Loop</p>
      <h1 className="cc-hero__brand" style={{ fontFamily: "var(--font-display)" }}>
        Peacock Growth Loop
      </h1>
      <p className="os-lede">
        SEO + AEO + GEO → AI Visibility → LLM Intelligence → Opportunity Discovery → Content Strategy → Content
        Creation → Optimization → AI Agents → Human Experts → Publishing → Measurement → Experiments → Learning →
        Re-optimization.
      </p>

      <section className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--surface)] p-6">
        <h2 style={{ fontFamily: "var(--font-display)" }}>Run the Growth Loop</h2>
        <p className="os-honesty">
          Crawls the site in real time, runs every engine below, and (where AI plugin API keys are configured)
          broadcasts real queries to ChatGPT, Gemini, Claude, Perplexity, and DeepSeek. Nothing is published, deleted,
          or changed in production without a later, explicit human approval.
        </p>
        <form
          className="mt-4 grid gap-3 md:grid-cols-[1fr_1fr_auto]"
          onSubmit={(e) => {
            e.preventDefault();
            void run();
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
            <Button type="submit" disabled={running}>
              {running ? "Running Growth Loop…" : "Run Peacock Growth Loop"}
            </Button>
          </div>
        </form>
        {error && <p style={{ color: "var(--danger, #d33)", marginTop: "0.75rem" }}>{error}</p>}
      </section>

      {report && (
        <>
          <section className="mt-6">
            <h2 style={{ fontFamily: "var(--font-display)" }}>Pipeline stages</h2>
            <StageTracker stages={report.stages} />
          </section>

          <ExecutiveSummaryPanel report={report} />

          <section className="mt-6">
            <h2 style={{ fontFamily: "var(--font-display)" }}>TOP ACTIONS TO TAKE</h2>
            {report.top_opportunities.map((o, i) => (
              <OpportunityCard key={`${i}-${o.action}`} opportunity={o} rank={i + 1} />
            ))}
          </section>

          <section className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--surface)] p-6 mt-6">
            <h2 style={{ fontFamily: "var(--font-display)" }}>AI Visibility Command Center</h2>
            <p className="os-honesty">{report.ai_visibility.disclaimer}</p>
            <div className="mt-3 grid gap-3 md:grid-cols-2 lg:grid-cols-3">
              {report.ai_visibility.engine_reports.map((e) => (
                <div key={e.engine_code} className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--background)]/30 p-3">
                  <strong>{e.engine_name}</strong>
                  {e.available ? (
                    <ul className="lab-list" style={{ marginTop: "0.4rem" }}>
                      <li>Mention rate: {Math.round(e.brand_mention_rate * 100)}%</li>
                      <li>Recommendation rate: {Math.round(e.recommendation_rate * 100)}%</li>
                      <li>Share of voice: {e.ai_share_of_voice !== null ? `${Math.round(e.ai_share_of_voice * 100)}%` : "n/a"}</li>
                      <li>Sentiment: {e.dominant_sentiment}</li>
                    </ul>
                  ) : (
                    <p className="os-honesty" style={{ marginTop: "0.4rem" }}>{e.reason_unavailable}</p>
                  )}
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--surface)] p-6 mt-6">
            <h2 style={{ fontFamily: "var(--font-display)" }}>Citation Gap Engine</h2>
            <p className="os-honesty">{report.citation_gaps.disclaimer}</p>
            {report.citation_gaps.gaps.length === 0 ? (
              <p className="os-honesty">No citations were observed across the available AI plugins for this research prompt.</p>
            ) : (
              report.citation_gaps.gaps.map((g) => (
                <details key={g.cited_url} className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--background)]/30 p-3" style={{ marginTop: "0.5rem" }}>
                  <summary style={{ cursor: "pointer" }}>
                    <strong>{g.cited_domain}</strong> — {g.fetch_status}
                  </summary>
                  <p style={{ marginTop: "0.4rem" }}>{g.evidence_gap}</p>
                  {g.content_gap.length > 0 && <p>Content gap: {g.content_gap.join(", ")}</p>}
                  {g.entity_gap.length > 0 && <p>Entity gap: {g.entity_gap.join(", ")}</p>}
                  <ul className="lab-list">
                    {g.recommended_fix.map((fix) => (
                      <li key={fix}>{fix}</li>
                    ))}
                  </ul>
                </details>
              ))
            )}
          </section>

          <section className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--surface)] p-6 mt-6">
            <h2 style={{ fontFamily: "var(--font-display)" }}>Content Strategy Engine</h2>
            <p style={{ fontSize: "0.85rem", color: "var(--muted)" }}>
              Relationship graph: {report.content_graph.nodes.length} nodes, {report.content_graph.edges.length} edges
              (Brand → Topic → Subtopic → Entity → Keyword → Search Query → AI Prompt → Content Page).
            </p>
            <div className="mt-3 grid gap-3 md:grid-cols-2">
              {report.content_recommendations.map((rec, i) => (
                <div key={`${i}-${rec.title}`} className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--background)]/30 p-3">
                  <em className="os-tag">{rec.content_type.replaceAll("_", " ")}</em>
                  <p style={{ margin: "0.3rem 0 0" }}>
                    <strong>{rec.title}</strong>
                  </p>
                  <p style={{ color: "var(--muted)", fontSize: "0.85rem" }}>{rec.rationale}</p>
                </div>
              ))}
            </div>
          </section>

          {report.top_content_brief && (
            <section className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--surface)] p-6 mt-6">
              <h2 style={{ fontFamily: "var(--font-display)" }}>CREATE WITH PEACOCK — {report.top_content_brief.topic}</h2>
              <p className="os-honesty">
                Peacock never invents research, statistics, quotations, citations, or sources — placeholders below
                need a human writer/expert.
              </p>
              <h4 style={{ marginTop: "0.8rem" }}>Outline</h4>
              <ul className="lab-list">
                {report.top_content_brief.outline.map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
              <h4 style={{ marginTop: "0.8rem" }}>Suggested title</h4>
              <p>{report.top_content_brief.suggested_title}</p>
              <h4 style={{ marginTop: "0.8rem" }}>Suggested meta description</h4>
              <p>{report.top_content_brief.suggested_meta_description}</p>
              <h4 style={{ marginTop: "0.8rem" }}>Optimization checklist</h4>
              <ul className="lab-list">
                {report.top_content_brief.optimization_checklist.map((c) => (
                  <li key={c}>{c}</li>
                ))}
              </ul>
              {report.content_simulation && (
                <>
                  <h4 style={{ marginTop: "0.8rem" }}>Multi-LLM Content Simulator</h4>
                  <p className="os-honesty">{report.content_simulation.disclaimer}</p>
                  <p>GEO readiness estimate: {report.content_simulation.geo_score_breakdown.geo_score}/100</p>
                  <ul className="lab-list">
                    {report.content_simulation.per_platform.map((p) => (
                      <li key={p.engine_code}>
                        {p.engine_name}: {p.note}
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </section>
          )}

          <section className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--surface)] p-6 mt-6">
            <h2 style={{ fontFamily: "var(--font-display)" }}>AI Agents</h2>
            {Object.values(report.agent_results).map((result) => (
              <AgentResultCard key={result.agent_name} result={result} />
            ))}
          </section>

          {report.expert_task && <ExpertTaskPanel task={report.expert_task} />}

          {report.publishing_preview && (
            <section className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--surface)] p-6 mt-6">
              <h2 style={{ fontFamily: "var(--font-display)" }}>Publishing (preview only)</h2>
              <p className="os-honesty">
                Peacock One → Publishing Connector → CMS. Publishing always requires explicit approval — this is a
                preview, not a live publish.
              </p>
              <p>
                Connector: <strong>{report.publishing_preview.connector}</strong> · Status:{" "}
                <strong>{report.publishing_preview.status}</strong>
              </p>
              <p style={{ color: "var(--muted)" }}>{report.publishing_preview.detail}</p>
            </section>
          )}

          {report.measurement_snapshot && (
            <section className="rounded-[var(--radius)] border border-[var(--border)] bg-[var(--surface)] p-6 mt-6">
              <h2 style={{ fontFamily: "var(--font-display)" }}>Measurement snapshot captured</h2>
              <p style={{ color: "var(--muted)" }}>
                Captured at {report.measurement_snapshot.captured_at}. Re-run the Growth Loop later on the same URL to
                see a real before/after comparison. Rankings, impressions, clicks, CTR, traffic, leads, and
                conversions require a Search Console/Analytics/CRM connector and are always shown as unavailable
                until one is configured.
              </p>
            </section>
          )}
        </>
      )}
    </div>
  );
}
