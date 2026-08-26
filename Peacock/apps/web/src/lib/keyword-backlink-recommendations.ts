import { getApiBaseUrl } from "@/lib/api";

export type OpportunityEvidence = {
  evidence_type: string;
  statement: string;
  strength: number;
};

export type OpportunityResult = {
  opportunity_key: string;
  opportunity_type: string;
  title: string;
  description: string;
  impact: number;
  urgency: number;
  confidence: number;
  difficulty: number;
  expected_value: number;
  recommended_action: string;
  evidence: OpportunityEvidence[];
  rank: number;
  opportunity_score: number;
  ranking_explanation: string;
  related_entity: string | null;
};

export type KeywordBacklinkRecommendations = {
  client_brand: string;
  summary: string;
  always_on_note: string;
  methodology_note: string;
  opportunities: OpportunityResult[];
};

export const DEMO_KEYWORD_BACKLINK_RECOMMENDATIONS: KeywordBacklinkRecommendations = {
  client_brand: "Acme",
  summary:
    "Peacock Opportunities scan ranked 4 opportunities (model v1). Top: 'AI visibility monitoring' keyword cluster is underserved (78/100).",
  always_on_note:
    "Peacock Opportunities is a continuous intelligence layer that refreshes ranked opportunities as new signals emerge.",
  methodology_note:
    "Ranking starts explainable (transparent feature contributions) and adapts from historical outcomes over time.",
  opportunities: [
    {
      opportunity_key: "high-value-topic-available-ai-visibility-monitoring-0",
      opportunity_type: "high_value_topic_available",
      title: "'AI visibility monitoring' keyword cluster is underserved",
      description:
        "Search demand for 'AI visibility monitoring' and related keywords rose 34% quarter-over-quarter with no dominant ranking page.",
      impact: 82,
      urgency: 70,
      confidence: 76,
      difficulty: 38,
      expected_value: 88,
      recommended_action:
        "Brief and publish a pillar guide targeting the keyword cluster, supported by linked cluster pages.",
      evidence: [
        {
          evidence_type: "keyword_demand",
          statement: "Search volume for the cluster rose 34% QoQ across 12 tracked keywords.",
          strength: 80,
        },
      ],
      rank: 1,
      opportunity_score: 78.5,
      ranking_explanation: "Explainable score 78.5/100 from impact, urgency, confidence, expected value, difficulty.",
      related_entity: "AI visibility monitoring",
    },
    {
      opportunity_key: "backlink-source-gained-influence-martech-review.com-1",
      opportunity_type: "backlink_source_gained_influence",
      title: "Referring domain 'martech-review.com' gained authority",
      description:
        "A previously low-authority review site jumped in domain authority and now ranks for high-intent comparison queries.",
      impact: 68,
      urgency: 55,
      confidence: 64,
      difficulty: 45,
      expected_value: 70,
      recommended_action:
        "Pursue an ethical placement (comparison listing or guest data) on the newly-influential referring domain.",
      evidence: [
        {
          evidence_type: "backlink_signal",
          statement: "martech-review.com domain authority increased and now sends referral traffic to 2 competitors.",
          strength: 62,
        },
      ],
      rank: 2,
      opportunity_score: 64.1,
      ranking_explanation: "Explainable score 64.1/100 from impact, urgency, confidence, expected value, difficulty.",
      related_entity: "martech-review.com",
    },
  ],
};

export async function fetchKeywordBacklinkRecommendations(
  brand = "Acme",
): Promise<KeywordBacklinkRecommendations> {
  try {
    const res = await fetch(`${getApiBaseUrl()}/opportunities/preview?brand=${encodeURIComponent(brand)}`, {
      cache: "no-store",
    });
    if (!res.ok) return DEMO_KEYWORD_BACKLINK_RECOMMENDATIONS;
    return (await res.json()) as KeywordBacklinkRecommendations;
  } catch {
    return DEMO_KEYWORD_BACKLINK_RECOMMENDATIONS;
  }
}
