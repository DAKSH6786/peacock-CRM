"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  DEMO_ARCHITECTURE,
  DEMO_COST,
  DEMO_MOAT,
  DEMO_QUALITY,
  DEMO_RELIABILITY,
  DEMO_SECURITY,
  fetchArchitecturePreview,
  fetchCostPreview,
  fetchMoatPreview,
  fetchQualityBarPreview,
  fetchReliabilityPreview,
  fetchSecurityPreview,
  type ArchitectureMap,
  type CostPreview,
  type MoatPreview,
  type QualityBarPreview,
  type ReliabilityPreview,
  type SecurityPreview,
} from "@/lib/peacock-os";

function Shell({
  title,
  kicker,
  children,
}: {
  title: string;
  kicker: string;
  children: React.ReactNode;
}) {
  return (
    <div className="cc-shell">
      <p className="cc-hero__kicker">{kicker}</p>
      <h1 className="cc-hero__brand" style={{ fontFamily: "var(--font-display)" }}>
        {title}
      </h1>
      <div className="cc-hero__actions" style={{ marginBottom: "2rem" }}>
        <Link href="/os" className="cc-btn cc-btn--ghost">
          Peacock One OS
        </Link>
        <Link href="/" className="cc-btn cc-btn--ghost">
          Command Centre
        </Link>
      </div>
      {children}
    </div>
  );
}

export function ArchitectureView() {
  const [map, setMap] = useState<ArchitectureMap>(DEMO_ARCHITECTURE);
  useEffect(() => {
    void fetchArchitecturePreview().then(setMap);
  }, []);
  return (
    <Shell title="Final Architecture" kicker="Peacock One system map">
      <pre className="os-diagram">{map.architecture_diagram}</pre>
      <p>{map.product_standard}</p>
      <ol className="os-stage-list">
        {map.stages.map((s) => (
          <li key={s.stage_key}>
            <strong>{s.stage_label}</strong>
            <span>{s.detail}</span>
            {s.loops_to_stage_key ? (
              <em className="os-tag">loops → {s.loops_to_stage_key}</em>
            ) : null}
          </li>
        ))}
      </ol>
    </Shell>
  );
}

export function QualityView() {
  const [data, setData] = useState<QualityBarPreview>(DEMO_QUALITY);
  useEffect(() => {
    void fetchQualityBarPreview().then(setData);
  }, []);
  return (
    <Shell title="Quality Bar" kicker="Module completeness gates">
      <p className="os-callout">
        Verdict: <strong>{data.completeness_verdict}</strong> — {data.gates_passed}/
        {data.gates_total} gates ({data.completeness_score})
      </p>
      <p>{data.improvement_summary}</p>
      <ul className="os-questions">
        {data.gate_results.map((g) => (
          <li key={g.gate_key}>
            <span>
              {g.question} → {g.improvement_if_fail}
            </span>
            <em className={g.passed ? "os-tag" : "os-tag os-tag--warn"}>
              {g.passed ? "pass" : "fail"}
            </em>
          </li>
        ))}
      </ul>
    </Shell>
  );
}

export function CostView() {
  const [data, setData] = useState<CostPreview>(DEMO_COST);
  useEffect(() => {
    void fetchCostPreview().then(setData);
  }, []);
  return (
    <Shell title="Cost Intelligence" kicker="Intelligence Budget Engine">
      <p className="os-callout">{data.policy_note}</p>
      <dl className="os-stats">
        <div>
          <dt>Selected method</dt>
          <dd>{data.selected_method_label}</dd>
        </div>
        <div>
          <dt>Calls</dt>
          <dd>{data.expected_calls}</dd>
        </div>
        <div>
          <dt>Tokens</dt>
          <dd>{data.expected_tokens}</dd>
        </div>
        <div>
          <dt>Searches</dt>
          <dd>{data.expected_searches}</dd>
        </div>
        <div>
          <dt>Runtime</dt>
          <dd>{data.expected_runtime_seconds}s</dd>
        </div>
        <div>
          <dt>Cost (µUSD)</dt>
          <dd>{data.expected_cost_usd_micros}</dd>
        </div>
      </dl>
      <p>{data.selection_rationale}</p>
    </Shell>
  );
}

export function MoatView() {
  const [data, setData] = useState<MoatPreview>(DEMO_MOAT);
  useEffect(() => {
    void fetchMoatPreview().then(setData);
  }, []);
  return (
    <Shell title="Moat Data Model" kicker="Proprietary intelligence pathways">
      <p className="os-callout">{data.moat_positioning}</p>
      <dl className="os-stats">
        <div>
          <dt>Pathways</dt>
          <dd>{data.pathways_count}</dd>
        </div>
        <div>
          <dt>Moat strength</dt>
          <dd>{data.moat_strength_score}</dd>
        </div>
      </dl>
      <p>{data.summary}</p>
      <ul className="os-questions">
        {data.pathway_kind_coverage.map((k) => (
          <li key={k}>
            <span>{k}</span>
          </li>
        ))}
      </ul>
    </Shell>
  );
}

export function ReliabilityView() {
  const [data, setData] = useState<ReliabilityPreview>(DEMO_RELIABILITY);
  useEffect(() => {
    void fetchReliabilityPreview().then(setData);
  }, []);
  return (
    <Shell title="Enterprise Reliability" kicker="Partial multi-provider results">
      <p className="os-callout">{data.partial_result_summary}</p>
      <dl className="os-stats">
        <div>
          <dt>Status</dt>
          <dd>{data.report_status}</dd>
        </div>
        <div>
          <dt>Succeeded</dt>
          <dd>
            {data.engines_succeeded}/{data.engines_attempted}
          </dd>
        </div>
      </dl>
      <p>
        Unavailable:{" "}
        {data.unavailable_providers.length
          ? data.unavailable_providers.join(", ")
          : "none"}
      </p>
    </Shell>
  );
}

export function SecurityView() {
  const [data, setData] = useState<SecurityPreview>(DEMO_SECURITY);
  useEffect(() => {
    void fetchSecurityPreview().then(setData);
  }, []);
  return (
    <Shell title="AI Connector Security" kicker="LLM I/O is untrusted">
      <p className="os-callout">{data.crawler_as_data_policy}</p>
      <dl className="os-stats">
        <div>
          <dt>Verdict</dt>
          <dd>{data.verdict}</dd>
        </div>
        <div>
          <dt>Risk</dt>
          <dd>{data.risk_level}</dd>
        </div>
        <div>
          <dt>Injections blocked</dt>
          <dd>{data.injection_findings_count}</dd>
        </div>
      </dl>
      <ul className="os-questions">
        <li>
          <span>Crawler treated as DATA</span>
          <em className="os-tag">{data.crawler_treated_as_data ? "yes" : "no"}</em>
        </li>
        <li>
          <span>Secrets exposure blocked</span>
          <em className="os-tag">{data.secrets_exposure_blocked ? "yes" : "no"}</em>
        </li>
        <li>
          <span>System behaviour change blocked</span>
          <em className="os-tag">
            {data.system_behaviour_change_blocked ? "yes" : "no"}
          </em>
        </li>
      </ul>
    </Shell>
  );
}
