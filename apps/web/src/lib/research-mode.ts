import { getApiBaseUrl } from "@/lib/api";

export type ResearchPage = {
  url: string;
  page_role: string;
  label: string | null;
  rank_order: number;
};

export type ResearchPrompt = {
  prompt_text: string;
  prompt_cluster: string | null;
  rank_order: number;
};

export type ResearchFinding = {
  finding_index: number;
  verdict: string;
  claim: string;
  evidence: string;
  uncertainty_band: string;
  uncertainty_rationale: string;
  auto_causal_conclusion_rejected: boolean;
  next_step: string;
};

export type ResearchStudy = {
  client_brand: string;
  research_question: string;
  hypothesis: string;
  metric_key: string;
  metric_label: string;
  treatment_description: string;
  completed_phases: string[];
  pages: ResearchPage[];
  prompts: ResearchPrompt[];
  findings: ResearchFinding[];
  baseline_mean: number | null;
  treatment_mean: number | null;
  absolute_delta: number | null;
  relative_delta_pct: number | null;
  control_adjusted_delta: number | null;
  uncertainty_band: string;
  uncertainty_score: number;
  finding_verdict: string;
  finding_summary: string;
  observation_rounds: number;
  pages_count: number;
  prompts_count: number;
  laboratory_positioning: string;
  causality_warning: string;
  methodology_note: string;
  analysed_at: string;
};

export const DEMO_RESEARCH_STUDY: ResearchStudy = {
  client_brand: "Acme",
  research_question:
    "Does adding proprietary statistics increase AI citation probability?",
  hypothesis:
    "Adding proprietary statistics to treatment pages increases AI citation probability versus baseline on selected prompts.",
  metric_key: "ai_citation_probability",
  metric_label: "AI citation probability",
  treatment_description: "Add proprietary statistics blocks to treatment pages.",
  completed_phases: [
    "hypothesis",
    "metric",
    "pages",
    "prompts",
    "baseline",
    "treatment",
    "repeat_observations",
    "uncertainty",
    "findings",
  ],
  pages: [
    {
      url: "https://example.com/guides/benchmarks",
      page_role: "treatment",
      label: "Benchmarks hub",
      rank_order: 0,
    },
    {
      url: "https://example.com/guides/roi",
      page_role: "treatment",
      label: "ROI guide",
      rank_order: 1,
    },
    {
      url: "https://example.com/blog/industry-overview",
      page_role: "control",
      label: "Control overview",
      rank_order: 2,
    },
  ],
  prompts: [
    {
      prompt_text: "What are the best enterprise CRM benchmarks?",
      prompt_cluster: "commercial",
      rank_order: 0,
    },
    {
      prompt_text: "Which CRM vendors publish original statistics?",
      prompt_cluster: "evidence",
      rank_order: 1,
    },
    {
      prompt_text: "Compare CRM platforms with proprietary data",
      prompt_cluster: "comparison",
      rank_order: 2,
    },
  ],
  findings: [
    {
      finding_index: 0,
      verdict: "supports_hypothesis",
      claim:
        "Observed AI citation probability change on treatment pages after adding proprietary statistics blocks.",
      evidence:
        "Baseline mean=0.23, treatment mean=0.34, absolute Δ=+0.11, control-adjusted Δ=+0.09, rounds=3.",
      uncertainty_band: "moderate",
      uncertainty_rationale:
        "Uncertainty band=moderate with adequate design coverage. Not a p-value; directional laboratory uncertainty.",
      auto_causal_conclusion_rejected: true,
      next_step:
        "Repeat observations across more prompt clusters and holdout pages before operationalising the treatment broadly.",
    },
  ],
  baseline_mean: 0.23,
  treatment_mean: 0.34,
  absolute_delta: 0.11,
  relative_delta_pct: 47.8,
  control_adjusted_delta: 0.09,
  uncertainty_band: "moderate",
  uncertainty_score: 0.35,
  finding_verdict: "supports_hypothesis",
  finding_summary:
    "Study on proprietary statistics vs AI citation probability: treatment pages moved with moderate uncertainty. Auto causal slogans rejected.",
  observation_rounds: 3,
  pages_count: 3,
  prompts_count: 3,
  laboratory_positioning:
    "Peacock Research Mode is how Peacock moves from SEO software toward a search intelligence laboratory.",
  causality_warning:
    "CAUTION: Research Mode does not automatically conclude that a treatment caused a metric change.",
  methodology_note: "Controlled analysis with uncertainty.",
  analysed_at: new Date().toISOString(),
};

export async function fetchResearchModePreview(
  brand = "Acme",
): Promise<ResearchStudy> {
  try {
    const response = await fetch(
      `${getApiBaseUrl()}/research-mode/preview?brand=${encodeURIComponent(brand)}`,
      { cache: "no-store" },
    );
    if (!response.ok) return DEMO_RESEARCH_STUDY;
    return (await response.json()) as ResearchStudy;
  } catch {
    return DEMO_RESEARCH_STUDY;
  }
}
