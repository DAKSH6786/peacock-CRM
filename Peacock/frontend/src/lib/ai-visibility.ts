import { getApiBaseUrl } from "@/lib/api";

export type EngineDistribution = {
  engine: string;
  brand_mention_probability: number;
  citation_probability: number;
  top3_probability: number;
  repetitions: number;
};

export type AiVisibilityScoreCard = {
  ai_visibility_score: number;
  measurement_confidence: string;
  peacock_visibility_confidence: number;
  based_on: { engines: number; repetitions: number; periods: number };
  brand_mention_probability: number;
  citation_probability: number;
  top3_recommendation_probability: number;
  competitor_probabilities: Record<string, number>;
  distributions: EngineDistribution[];
  summary: string;
  single_shot_rejected: boolean;
  defensible: boolean;
  probe_mode: string;
};

export const DEMO_AI_VISIBILITY: AiVisibilityScoreCard = {
  ai_visibility_score: 62.1,
  measurement_confidence: "MEDIUM",
  peacock_visibility_confidence: 0.68,
  based_on: { engines: 4, repetitions: 40, periods: 4 },
  brand_mention_probability: 0.75,
  citation_probability: 0.45,
  top3_recommendation_probability: 0.55,
  competitor_probabilities: { competitor_a: 0.42, competitor_b: 0.35 },
  distributions: [
    { engine: "openai", brand_mention_probability: 0.8, citation_probability: 0.5, top3_probability: 0.6, repetitions: 10 },
    { engine: "anthropic", brand_mention_probability: 0.7, citation_probability: 0.4, top3_probability: 0.5, repetitions: 10 },
    { engine: "google_ai_overviews", brand_mention_probability: 0.6, citation_probability: 0.3, top3_probability: 0.4, repetitions: 10 },
    { engine: "perplexity", brand_mention_probability: 0.9, citation_probability: 0.6, top3_probability: 0.7, repetitions: 10 },
  ],
  summary:
    "Acme AI Visibility Score 62.1/100 from 40 controlled repetitions across 4 engines. Measurement confidence MEDIUM. Never a single-shot measurement.",
  single_shot_rejected: true,
  defensible: true,
  probe_mode: "mock_deterministic",
};

export async function fetchAiVisibilityPreview(brand = "Acme"): Promise<AiVisibilityScoreCard> {
  try {
    const res = await fetch(`${getApiBaseUrl()}/visibility/preview?brand=${encodeURIComponent(brand)}`, {
      cache: "no-store",
    });
    if (!res.ok) return DEMO_AI_VISIBILITY;
    return (await res.json()) as AiVisibilityScoreCard;
  } catch {
    return DEMO_AI_VISIBILITY;
  }
}
