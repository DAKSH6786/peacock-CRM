import { getApiBaseUrl } from "@/lib/api";

export type WriterRecommendation = {
  writer_key: string;
  display_name: string;
  rank: number;
  predicted_outcome_score: number;
  dna_fit_score: number;
  topic_fit_score: number;
  client_fit_score: number;
  audience_fit_score: number;
  historical_outcome_score: number;
  rationale: string;
  decision_answer: string;
};

export type WriterDnaProfile = {
  writer_key: string;
  display_name: string;
  dna_composite_score: number;
  dna_summary: string;
};

export type ContentOptimizerResult = {
  client_brand: string;
  topic: string;
  audience: string;
  decision_question: string;
  similarity_rejection_note: string;
  dna_profiles: WriterDnaProfile[];
  recommendations: WriterRecommendation[];
  top_writer_key: string | null;
  top_outcome_score: number | null;
  summary: string;
};

export const DEMO_CONTENT_OPTIMIZER: ContentOptimizerResult = {
  client_brand: "Acme",
  topic: "AI visibility monitoring",
  audience: "Marketing & SEO leaders",
  decision_question:
    "Which writer is most likely to produce the best outcome for topic «AI visibility monitoring», client «Acme», audience «Marketing & SEO leaders»?",
  similarity_rejection_note:
    "Similarity-only matching (embed samples → nearest neighbor) is rejected as the primary decision method.",
  dna_profiles: [
    {
      writer_key: "writer_amina",
      display_name: "Amina Chen",
      dna_composite_score: 70,
      dna_summary: "DNA composite 70/100. Strengths: deadline reliability, subject expertise, client acceptance.",
    },
    {
      writer_key: "writer_diego",
      display_name: "Diego Alvarez",
      dna_composite_score: 55,
      dna_summary: "DNA composite 55/100. Strengths: storytelling, client acceptance, deadline reliability.",
    },
  ],
  recommendations: [
    {
      writer_key: "writer_amina",
      display_name: "Amina Chen",
      rank: 1,
      predicted_outcome_score: 75,
      dna_fit_score: 74,
      topic_fit_score: 75,
      client_fit_score: 93,
      audience_fit_score: 63,
      historical_outcome_score: 68,
      rationale: "Predicted outcome 75/100 — strong DNA, topic, and client fit.",
      decision_answer: "Amina Chen is evaluated for best outcome on THIS topic, client, and audience.",
    },
    {
      writer_key: "writer_diego",
      display_name: "Diego Alvarez",
      rank: 2,
      predicted_outcome_score: 37,
      dna_fit_score: 55,
      topic_fit_score: 35,
      client_fit_score: 0,
      audience_fit_score: 46,
      historical_outcome_score: 41,
      rationale: "Predicted outcome 37/100 — weaker topic and client fit for this brief.",
      decision_answer: "Diego Alvarez is evaluated for best outcome on THIS topic, client, and audience.",
    },
  ],
  top_writer_key: "writer_amina",
  top_outcome_score: 75,
  summary:
    "Writer Intelligence 2.0 ranked 2 writer(s). Top: Amina Chen (predicted outcome 75/100). Similarity-only matching rejected as the primary decision method.",
};

export async function fetchContentOptimizerPreview(brand = "Acme"): Promise<ContentOptimizerResult> {
  try {
    const res = await fetch(
      `${getApiBaseUrl()}/writer-intelligence/preview?brand=${encodeURIComponent(brand)}`,
      { cache: "no-store" },
    );
    if (!res.ok) return DEMO_CONTENT_OPTIMIZER;
    return (await res.json()) as ContentOptimizerResult;
  } catch {
    return DEMO_CONTENT_OPTIMIZER;
  }
}
