import { getApiBaseUrl } from "@/lib/api";

export type MetricComponent = {
  component_key: string;
  component_label: string;
  raw_value: number;
  weight: number;
  contribution: number;
  rank_order: number;
};

export type MetricScore = {
  metric_key: string;
  metric_label: string;
  score: number;
  unit: string;
  formula_id: string;
  formula_text: string;
  explanation: string;
  proprietary_note: string;
  components: MetricComponent[];
};

export type ProprietaryMetricsScorecard = {
  client_brand: string;
  scored_at: string;
  metrics_scored: number;
  proprietary_disclaimer: string;
  methodology_note: string;
  summary: string;
  metrics: MetricScore[];
  not_official_platforms: string[];
};

export const DEMO_METRICS: ProprietaryMetricsScorecard = {
  client_brand: "Acme",
  scored_at: new Date().toISOString(),
  metrics_scored: 13,
  proprietary_disclaimer:
    "All Peacock Proprietary Metrics are Peacock One indicators. They are NOT Google, OpenAI, Anthropic, or Perplexity official ranking factors.",
  methodology_note: "Documented Peacock proprietary scoring framework.",
  summary: "Demo proprietary metrics scorecard.",
  not_official_platforms: ["Google", "OpenAI", "Anthropic", "Perplexity"],
  metrics: [
    {
      metric_key: "peacock_visibility_index",
      metric_label: "Peacock Visibility Index",
      score: 59.4,
      unit: "0-100",
      formula_id: "PVI-1",
      formula_text:
        "PVI = mean(Search Visibility, AI Visibility, Share of Answer, Entity Authority, Citation Authority, Content Opportunity, Agent Readiness)",
      explanation: "Equal-weight mean of seven Peacock dimensions.",
      proprietary_note:
        "Peacock proprietary indicator — not a Google/OpenAI/Anthropic/Perplexity ranking factor.",
      components: [],
    },
  ],
};

export async function fetchProprietaryMetricsPreview(
  brand = "Acme",
): Promise<ProprietaryMetricsScorecard> {
  try {
    const response = await fetch(
      `${getApiBaseUrl()}/proprietary-metrics/preview?brand=${encodeURIComponent(brand)}`,
      { cache: "no-store" },
    );
    if (!response.ok) return DEMO_METRICS;
    return (await response.json()) as ProprietaryMetricsScorecard;
  } catch {
    return DEMO_METRICS;
  }
}
