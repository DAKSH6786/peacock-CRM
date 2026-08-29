import { getApiBaseUrl } from "@/lib/api";

export type ExecutiveAnswer = {
  question_key: string;
  question_label: string;
  answer: string;
  evidence_note: string;
  confidence: number;
  rank_order: number;
};

export type RoleSummary = {
  role: string;
  title: string;
  body: string;
  call_to_action: string;
};

export type ExecutiveBrainBrief = {
  client_brand: string;
  generated_at: string;
  horizon_days: number;
  budget_label: string;
  overall_confidence: number;
  headline: string;
  answers: ExecutiveAnswer[];
  role_summaries: RoleSummary[];
  methodology_note: string;
  summary: string;
};

export const DEMO_EXECUTIVE_BRIEF: ExecutiveBrainBrief = {
  client_brand: "Acme",
  generated_at: new Date().toISOString(),
  horizon_days: 90,
  budget_label: "₹10 lakh",
  overall_confidence: 0.78,
  headline: "Acme · Executive Brain · 90-day generative visibility brief",
  methodology_note:
    "Peacock Executive Brain strips SEO complexity into executive questions with CEO/CMO summaries.",
  summary: "Executive Brain demo brief.",
  answers: [
    {
      question_key: "where_winning",
      question_label: "Where are we winning?",
      answer:
        "Acme still leads category search visibility on branded + mid-funnel hubs; content opportunity score is high — clear room to gain on comparison pages",
      evidence_note: "Command Centre win signals",
      confidence: 0.81,
      rank_order: 0,
    },
    {
      question_key: "where_losing",
      question_label: "Where are we losing?",
      answer:
        "Competitor A citation share rose 18% → 31% on research queries; AI visibility and Share of Answer softened this week (esp. Claude/Perplexity)",
      evidence_note: "Command Centre loss signals",
      confidence: 0.875,
      rank_order: 1,
    },
    {
      question_key: "why",
      question_label: "Why?",
      answer:
        "Competitor A shipped 3 research pages that answer engines now prefer; our comparison hubs lack quotable evidence density and entity coverage",
      evidence_note: "Driver signals",
      confidence: 0.86,
      rank_order: 2,
    },
    {
      question_key: "what_changed",
      question_label: "What changed?",
      answer:
        "This week: citation surge for competitor, AI visibility dip, anomaly alerts",
      evidence_note: "Temporal + anomaly movement",
      confidence: 0.83,
      rank_order: 3,
    },
    {
      question_key: "worth_doing",
      question_label: "What is worth doing?",
      answer:
        "Publish a proprietary benchmark study + refresh /compare and /pricing",
      evidence_note: "Priority actions",
      confidence: 0.85,
      rank_order: 4,
    },
    {
      question_key: "what_cost",
      question_label: "What will it cost?",
      answer:
        "Plan around ₹10 lakh over the next 90 days, sized to capacity — citability content, entity/schema, citation outreach, and measurement.",
      evidence_note: "Budget envelope ₹10 lakh / 90d",
      confidence: 0.76,
      rank_order: 5,
    },
    {
      question_key: "what_return",
      question_label: "What could it return?",
      answer:
        "Directional SoA recovery in a mid-single to low-double-digit pp range over 90 days; commercial prompt clusters tie to material but uncertain pipeline exposure",
      evidence_note: "Return ranges",
      confidence: 0.6,
      rank_order: 6,
    },
    {
      question_key: "if_do_nothing",
      question_label: "What happens if we do nothing?",
      answer:
        "If we do nothing, competitor citation lead likely widens and AI presence keeps eroding",
      evidence_note: "Do-nothing risk",
      confidence: 0.815,
      rank_order: 7,
    },
  ],
  role_summaries: [
    {
      role: "ceo",
      title: "CEO brief",
      body:
        "Acme is not losing the whole board — search and content opportunity still hold — but generative visibility is the strategic risk. Competitor A jumped citation share 18% → 31% on research queries after three new pages. A focused 90-day push (~₹10 lakh) to publish proprietary proof and harden commercial hubs is the executive decision. Doing nothing likely widens the gap. Treat returns as ranges.",
      call_to_action:
        "Approve the 90-day generative-visibility programme and name an owner for citation + AI Share-of-Answer outcomes.",
    },
    {
      role: "cmo",
      title: "CMO brief",
      body:
        "Marketing priority: stop bleeding AI answer presence. Win zones remain branded search and high-opportunity pages; loss zones are citations and multi-engine SoA. Why: evidence density. Change this week: competitor research pages + our soft AI scores. Worth doing: benchmark study + /compare + /pricing refresh. Cost envelope ₹10 lakh; expected return is directional SoA recovery, not a point forecast. If we wait, the narrative compounds against Acme.",
      call_to_action:
        "Greenlight the benchmark + hub refresh sprint; hold low-ROI volume until citability work lands.",
    },
  ],
};

export async function fetchExecutiveBrainPreview(
  brand = "Acme",
): Promise<ExecutiveBrainBrief> {
  try {
    const response = await fetch(
      `${getApiBaseUrl()}/executive-brain/preview?brand=${encodeURIComponent(brand)}`,
      { cache: "no-store" },
    );
    if (!response.ok) {
      return DEMO_EXECUTIVE_BRIEF;
    }
    return (await response.json()) as ExecutiveBrainBrief;
  } catch {
    return DEMO_EXECUTIVE_BRIEF;
  }
}
