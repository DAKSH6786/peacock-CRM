import { getApiBaseUrl } from "@/lib/api";

export type ContentProposalScore = {
  title: string;
  slug: string;
  content_format: string;
  angle: string | null;
  lab_priority_score: number;
  information_gain_score: number;
  content_moat_score: number;
  generative_citability_score: number;
  moat_rationale: string;
  recommendation_summary: string;
};

export type BlogTopicRecommendations = {
  client_brand: string;
  citability_disclaimer: string;
  proposals: ContentProposalScore[];
  example_moat: { content_format: string; moat_prior: number }[];
  top_recommendation: { title: string; slug: string; lab_priority_score: number } | null;
};

export const DEMO_BLOG_TOPIC_RECOMMENDATIONS: BlogTopicRecommendations = {
  client_brand: "Acme",
  citability_disclaimer:
    "Generative Citability Score is Peacock's proprietary estimate — not a guaranteed third-party ranking factor.",
  proposals: [
    {
      title: "2025 AI Visibility Benchmark: 500 Brands Compared",
      slug: "ai-visibility-benchmark-2025",
      content_format: "proprietary_benchmark_study",
      angle: "Original dataset comparing brand mention and citation rates across 5 AI engines.",
      lab_priority_score: 68,
      information_gain_score: 80,
      content_moat_score: 98,
      generative_citability_score: 49,
      moat_rationale: "Benchmark studies are hardest for competitors to replicate.",
      recommendation_summary: "Lab priority 68/100. High information gain and content moat.",
    },
    {
      title: "What Is AEO? A Practical Definition for Marketers",
      slug: "what-is-aeo",
      content_format: "generic_listicle",
      angle: "Basics of answer engine optimisation.",
      lab_priority_score: 38,
      information_gain_score: 22,
      content_moat_score: 15,
      generative_citability_score: 40,
      moat_rationale: "Generic listicles are the easiest format for competitors to replicate.",
      recommendation_summary: "Lab priority 38/100. Low information gain — needs a differentiated angle.",
    },
  ],
  example_moat: [
    { content_format: "generic_listicle", moat_prior: 18 },
    { content_format: "expert_interview", moat_prior: 51 },
    { content_format: "original_dataset", moat_prior: 86 },
    { content_format: "proprietary_benchmark_study", moat_prior: 94 },
  ],
  top_recommendation: {
    title: "2025 AI Visibility Benchmark: 500 Brands Compared",
    slug: "ai-visibility-benchmark-2025",
    lab_priority_score: 68,
  },
};

export async function fetchBlogTopicRecommendations(
  brand = "Acme",
): Promise<BlogTopicRecommendations> {
  try {
    const res = await fetch(`${getApiBaseUrl()}/content-lab/preview?brand=${encodeURIComponent(brand)}`, {
      cache: "no-store",
    });
    if (!res.ok) return DEMO_BLOG_TOPIC_RECOMMENDATIONS;
    return (await res.json()) as BlogTopicRecommendations;
  } catch {
    return DEMO_BLOG_TOPIC_RECOMMENDATIONS;
  }
}
