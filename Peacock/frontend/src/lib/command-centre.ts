import { getApiBaseUrl } from "@/lib/api";

export type VisibilitySignal = {
  dimension: string;
  label: string;
  score: number;
  delta: number;
  rank_order: number;
};

export type SituationItem = {
  kind: string;
  label: string;
  title: string;
  detail: string;
  severity: string;
  rank_order: number;
};

export type FeedItem = {
  feed_index: number;
  detection_label: string;
  headline: string;
  body: string;
  primary_driver: string;
  potential_response: string;
  confidence: number;
  confidence_pct: number;
  detected_at: string;
  graph_surface: string | null;
};

export type CommandCentreSnapshot = {
  client_brand: string;
  visibility_index: number;
  visibility_delta: number;
  captured_at: string;
  headline: string;
  signals: VisibilitySignal[];
  situations: SituationItem[];
  feed_items: FeedItem[];
  methodology_note: string;
  summary: string;
};

export const DEMO_SNAPSHOT: CommandCentreSnapshot = {
  client_brand: "Acme",
  visibility_index: 59.4,
  visibility_delta: -0.6,
  captured_at: new Date().toISOString(),
  headline: "Acme · Peacock Visibility Index 59",
  methodology_note:
    "Peacock Command Centre is the flagship command surface for generative visibility intelligence.",
  summary: "Command Centre demo snapshot.",
  signals: [
    { dimension: "search_visibility", label: "Search Visibility", score: 72, delta: 1.4, rank_order: 0 },
    { dimension: "ai_visibility", label: "AI Visibility", score: 58, delta: -3.8, rank_order: 1 },
    { dimension: "share_of_answer", label: "Share of Answer", score: 41, delta: -2.1, rank_order: 2 },
    { dimension: "entity_authority", label: "Entity Authority", score: 63, delta: 0.6, rank_order: 3 },
    { dimension: "citation_authority", label: "Citation Authority", score: 47, delta: -5.2, rank_order: 4 },
    { dimension: "content_opportunity", label: "Content Opportunity", score: 81, delta: 4.0, rank_order: 5 },
    { dimension: "agent_readiness", label: "Agent Readiness", score: 54, delta: 1.1, rank_order: 6 },
  ],
  situations: [
    {
      kind: "biggest_opportunity",
      label: "Biggest Opportunity",
      title: "Proprietary benchmark study",
      detail:
        "Publishing an owned benchmark can reclaim citation share Acme lost on commercial prompts.",
      severity: "high",
      rank_order: 0,
    },
    {
      kind: "biggest_threat",
      label: "Biggest Threat",
      title: "Competitor A citation surge",
      detail: "Competitor A citation share jumped 18% → 31% on category research queries.",
      severity: "critical",
      rank_order: 1,
    },
    {
      kind: "fastest_win",
      label: "Fastest Win",
      title: "Refresh /compare + /pricing hubs",
      detail: "Entity-dense comparison tables are the shortest path to SoA recovery this sprint.",
      severity: "high",
      rank_order: 2,
    },
    {
      kind: "competitor_movement",
      label: "Competitor Movement",
      title: "Competitor A shipped 3 research pages",
      detail: "Those pages are the primary driver behind the citation-share acceleration.",
      severity: "high",
      rank_order: 3,
    },
    {
      kind: "ai_visibility_change",
      label: "AI Visibility Change",
      title: "AI Visibility −3.8 this week",
      detail: "Claude and Perplexity presence softened; ChatGPT held flatter.",
      severity: "medium",
      rank_order: 4,
    },
    {
      kind: "critical_technical_issue",
      label: "Critical Technical Issue",
      title: "Indexation gap on /guides/*",
      detail:
        "Agent and crawler readiness checks flag thin schema + blocked snippets on guide templates.",
      severity: "critical",
      rank_order: 5,
    },
  ],
  feed_items: [
    {
      feed_index: 0,
      detection_label: "PEACOCK DETECTED",
      headline: "Competitor A increased citation share",
      body: "Competitor A increased citation share from 18% → 31%.",
      primary_driver: "3 recently published research pages.",
      potential_response: "Publish proprietary benchmark study.",
      confidence: 0.87,
      confidence_pct: 87,
      detected_at: new Date().toISOString(),
      graph_surface: "citation_graph",
    },
    {
      feed_index: 1,
      detection_label: "PEACOCK DETECTED",
      headline: "AI Visibility dipped across two engines",
      body: "Share of Answer softened on Claude (−4pp) and Perplexity (−2pp) week-over-week.",
      primary_driver: "Citation disappearance on commercial prompt cluster.",
      potential_response: "Reinforce comparison hubs with quotable specs and sources.",
      confidence: 0.81,
      confidence_pct: 81,
      detected_at: new Date().toISOString(),
      graph_surface: "anomaly_engine",
    },
    {
      feed_index: 2,
      detection_label: "PEACOCK DETECTED",
      headline: "Content opportunity cluster opened on /security",
      body: "Opportunity Engine ranks /security in the top GEO improvement set.",
      primary_driver: "Entity Authority gap on ‘enterprise reliability’ facet.",
      potential_response: "Assign evidence-dense writer; ship FAQ + source block variant.",
      confidence: 0.76,
      confidence_pct: 76,
      detected_at: new Date().toISOString(),
      graph_surface: "opportunity_engine",
    },
  ],
};

export async function fetchCommandCentrePreview(
  brand = "Acme",
): Promise<CommandCentreSnapshot> {
  try {
    const response = await fetch(
      `${getApiBaseUrl()}/command-centre/preview?brand=${encodeURIComponent(brand)}`,
      { cache: "no-store" },
    );
    if (!response.ok) {
      return DEMO_SNAPSHOT;
    }
    return (await response.json()) as CommandCentreSnapshot;
  } catch {
    return DEMO_SNAPSHOT;
  }
}
