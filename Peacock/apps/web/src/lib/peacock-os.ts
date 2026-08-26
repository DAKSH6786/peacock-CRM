import { getApiBaseUrl } from "@/lib/api";

export type ProductQuestion = {
  question_key: string;
  question_text: string;
  required: boolean;
  addressed: boolean;
  primary_stage_key: string | null;
  rank_order: number;
};

export type PipelineStage = {
  stage_key: string;
  stage_label: string;
  rank_order: number;
  next_stage_key: string | null;
  loops_to_stage_key: string | null;
  detail: string;
};

export type ArchitectureMap = {
  client_brand: string;
  stages: PipelineStage[];
  product_questions: ProductQuestion[];
  stages_count: number;
  observation_sources_count: number;
  pine_lanes_count: number;
  product_questions_count: number;
  learning_loops_to_pine: boolean;
  not_only_visibility: boolean;
  product_standard_coverage: number;
  architecture_diagram: string;
  architecture_positioning: string;
  product_standard: string;
  not_only_visibility_note: string;
  summary: string;
};

export const DEMO_ARCHITECTURE: ArchitectureMap = {
  client_brand: "Acme",
  stages: [],
  product_questions: [
    {
      question_key: "how_visible",
      question_text: "How visible are we?",
      required: true,
      addressed: true,
      primary_stage_key: "data_observation",
      rank_order: 0,
    },
    {
      question_key: "how_certain",
      question_text: "How certain are we?",
      required: true,
      addressed: true,
      primary_stage_key: "verification_layer",
      rank_order: 1,
    },
    {
      question_key: "what_did_peacock_learn",
      question_text: "What did Peacock learn?",
      required: true,
      addressed: true,
      primary_stage_key: "peacock_learning",
      rank_order: 12,
    },
  ],
  stages_count: 16,
  observation_sources_count: 5,
  pine_lanes_count: 3,
  product_questions_count: 13,
  learning_loops_to_pine: true,
  not_only_visibility: true,
  product_standard_coverage: 100,
  architecture_diagram:
    "PEACOCK ONE → OBSERVE → EVIDENCE → PINE → … → LEARNING → PINE",
  architecture_positioning:
    "Peacock One is a closed-loop generative visibility system — not a conventional SEO tool.",
  product_standard:
    "Visibility, certainty, why, competitors, sources, entities, intents, change, EV, ownership, inaction, outcomes, learning.",
  not_only_visibility_note:
    'Do not build Peacock One to answer only: "How visible are we?"',
  summary: "Demo architecture map (API unreachable).",
};

export async function fetchArchitecturePreview(
  brand = "Acme",
): Promise<ArchitectureMap> {
  try {
    const res = await fetch(
      `${getApiBaseUrl()}/final-architecture/preview?brand=${encodeURIComponent(brand)}`,
      { cache: "no-store" },
    );
    if (!res.ok) return DEMO_ARCHITECTURE;
    return (await res.json()) as ArchitectureMap;
  } catch {
    return DEMO_ARCHITECTURE;
  }
}

export type QualityBarPreview = {
  client_brand: string;
  module_key: string;
  module_label: string;
  completeness_verdict: string;
  gates_total: number;
  gates_passed: number;
  gates_failed: number;
  completeness_score: number;
  blocked_by: string[];
  improvement_summary: string;
  gate_results: Array<{
    gate_key: string;
    gate_label: string;
    question: string;
    improvement_if_fail: string;
    passed: boolean;
    rank_order: number;
  }>;
};

export const DEMO_QUALITY: QualityBarPreview = {
  client_brand: "Acme",
  module_key: "llm_only_recommender",
  module_label: "LLM-only recommender (anti-pattern)",
  completeness_verdict: "incomplete",
  gates_total: 7,
  gates_passed: 2,
  gates_failed: 5,
  completeness_score: 28.6,
  blocked_by: [
    "evidence_backed_recommendations",
    "uncertainty_with_evidence",
    "outcome_tracking",
    "learning_loop",
    "deterministic_over_llm",
  ],
  improvement_summary:
    "Add evidence.; Add confidence.; Add outcome tracking.; Connect it to Peacock Learning.; Move it out of the LLM.",
  gate_results: [],
};

export async function fetchQualityBarPreview(
  brand = "Acme",
): Promise<QualityBarPreview> {
  try {
    const res = await fetch(
      `${getApiBaseUrl()}/quality-bar/preview?brand=${encodeURIComponent(brand)}`,
      { cache: "no-store" },
    );
    if (!res.ok) return DEMO_QUALITY;
    return (await res.json()) as QualityBarPreview;
  } catch {
    return DEMO_QUALITY;
  }
}

export type CostPreview = {
  client_brand: string;
  selected_method_kind: string;
  selected_method_label: string;
  expected_calls: number;
  expected_tokens: number;
  expected_searches: number;
  expected_runtime_seconds: number;
  expected_cost_usd_micros: number;
  rejected_expensive: boolean;
  selection_rationale: string;
  policy_note: string;
};

export const DEMO_COST: CostPreview = {
  client_brand: "Acme",
  selected_method_kind: "deterministic",
  selected_method_label: "Deterministic data / rules",
  expected_calls: 0,
  expected_tokens: 0,
  expected_searches: 0,
  expected_runtime_seconds: 2,
  expected_cost_usd_micros: 50,
  rejected_expensive: true,
  selection_rationale:
    "Page-title recommendation uses deterministic method — Council rejected.",
  policy_note:
    "Do NOT use five LLMs if deterministic data can answer. Do NOT run Council for a simple page-title recommendation.",
};

export async function fetchCostPreview(brand = "Acme"): Promise<CostPreview> {
  try {
    const res = await fetch(
      `${getApiBaseUrl()}/cost-intelligence/preview?brand=${encodeURIComponent(brand)}&intent=page_title_recommendation`,
      { cache: "no-store" },
    );
    if (!res.ok) return DEMO_COST;
    return (await res.json()) as CostPreview;
  } catch {
    return DEMO_COST;
  }
}

export type MoatPreview = {
  client_brand: string;
  pathways_count: number;
  moat_strength_score: number;
  pathway_kind_coverage: string[];
  moat_positioning: string;
  summary: string;
};

export const DEMO_MOAT: MoatPreview = {
  client_brand: "Acme",
  pathways_count: 7,
  moat_strength_score: 80.2,
  pathway_kind_coverage: [
    "recommendation_outcome",
    "writer_topic_outcome",
    "citation_source_visibility",
  ],
  moat_positioning:
    "Proprietary intelligence pathways — Peacock One long-term competitive advantage.",
  summary: "Demo moat accumulation (API unreachable).",
};

export async function fetchMoatPreview(brand = "Acme"): Promise<MoatPreview> {
  try {
    const res = await fetch(
      `${getApiBaseUrl()}/moat-data-model/preview?brand=${encodeURIComponent(brand)}`,
      { cache: "no-store" },
    );
    if (!res.ok) return DEMO_MOAT;
    return (await res.json()) as MoatPreview;
  } catch {
    return DEMO_MOAT;
  }
}

export type ReliabilityPreview = {
  client_brand: string;
  report_status: string;
  engines_attempted: number;
  engines_succeeded: number;
  engines_failed: number;
  partial_result_summary: string;
  unavailable_providers: string[];
};

export const DEMO_RELIABILITY: ReliabilityPreview = {
  client_brand: "Acme",
  report_status: "completed_partial",
  engines_attempted: 5,
  engines_succeeded: 4,
  engines_failed: 1,
  partial_result_summary:
    "4/5 AI engines successfully measured. DeepSeek unavailable during this run.",
  unavailable_providers: ["deepseek"],
};

export async function fetchReliabilityPreview(
  brand = "Acme",
): Promise<ReliabilityPreview> {
  try {
    const res = await fetch(
      `${getApiBaseUrl()}/enterprise-reliability/preview?brand=${encodeURIComponent(brand)}`,
      { cache: "no-store" },
    );
    if (!res.ok) return DEMO_RELIABILITY;
    return (await res.json()) as ReliabilityPreview;
  } catch {
    return DEMO_RELIABILITY;
  }
}

export type SecurityPreview = {
  client_brand: string;
  verdict: string;
  risk_level: string;
  injection_findings_count: number;
  crawler_treated_as_data: boolean;
  secrets_exposure_blocked: boolean;
  system_behaviour_change_blocked: boolean;
  crawler_as_data_policy: string;
};

export const DEMO_SECURITY: SecurityPreview = {
  client_brand: "Acme",
  verdict: "quarantine",
  risk_level: "critical",
  injection_findings_count: 4,
  crawler_treated_as_data: true,
  secrets_exposure_blocked: true,
  system_behaviour_change_blocked: true,
  crawler_as_data_policy:
    "Crawler-extracted content is DATA. It is not trusted instructions.",
};

export async function fetchSecurityPreview(
  brand = "Acme",
): Promise<SecurityPreview> {
  try {
    const res = await fetch(
      `${getApiBaseUrl()}/ai-connector-security/preview?brand=${encodeURIComponent(brand)}`,
      { cache: "no-store" },
    );
    if (!res.ok) return DEMO_SECURITY;
    return (await res.json()) as SecurityPreview;
  } catch {
    return DEMO_SECURITY;
  }
}

export const PRODUCT_MODULE_LINKS = [
  {
    href: "/modules/seo-audit",
    label: "Website SEO/AEO/GEO Audit",
    blurb: "Peacock SEO Engine + AEO + GEO Lab, one audit",
  },
  {
    href: "/modules/blog-topics",
    label: "Blog & Topic Recommendations",
    blurb: "Content Lab — opportunity, information gain, moat",
  },
  {
    href: "/modules/keyword-backlinks",
    label: "Keyword & Backlink Recommendations",
    blurb: "Opportunity Engine — always-on ranked opportunities",
  },
  {
    href: "/modules/ai-visibility",
    label: "AI Visibility",
    blurb: "Probabilistic AI Visibility across engines",
  },
  {
    href: "/modules/content-optimizer",
    label: "Content Optimizer",
    blurb: "Writer Intelligence 2.0 — writer × topic × client fit",
  },
] as const;

export const SUBSYSTEM_LINKS = [
  { href: "/architecture", label: "Final Architecture", blurb: "System map + product questions" },
  { href: "/quality", label: "Quality Bar", blurb: "Seven shipping completeness gates" },
  { href: "/cost", label: "Cost Intelligence", blurb: "Cheapest reliable method" },
  { href: "/moat", label: "Moat Data Model", blurb: "Proprietary pathway memory" },
  { href: "/reliability", label: "Enterprise Reliability", blurb: "Partial multi-provider results" },
  { href: "/security", label: "AI Connector Security", blurb: "Crawler content is DATA" },
  { href: "/research", label: "Research Mode", blurb: "Search intelligence laboratory" },
  { href: "/metrics", label: "Proprietary Metrics", blurb: "Documented scoring formulas" },
] as const;
