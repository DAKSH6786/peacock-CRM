import { apiFetch, getApiBaseUrl } from "@/lib/api";
import type { SiteIntelligenceReport } from "@/lib/site-intelligence";

/**
 * Peacock Growth Loop — the flagship end-to-end workflow:
 *
 *   SEO + AEO + GEO -> AI Visibility -> LLM Intelligence -> Citation +
 *   Competitor Gap -> Opportunity Engine -> Content Strategy -> Content
 *   Creation -> Optimization -> AI Agents -> Human Experts -> Publishing ->
 *   Measurement -> Experiments -> Learning -> Re-optimization
 *
 * Triggers a REAL crawl (and, where AI plugin API keys are configured, real
 * LLM broadcasts) through the backend — there is no static demo fallback.
 */

export type GrowthLoopStage = { stage: string; status: "completed" | "skipped" | "unavailable"; detail: string };

export type QueryObservation = {
  intent: string;
  query_text: string;
  engine_code: string;
  engine_name: string;
  simulated: boolean;
  brand_mentioned: boolean;
  recommended: boolean;
  recommendation_position: number | null;
  competitor_mentions: string[];
  cited_domains: string[];
  cited_urls: string[];
  brand_attributes: string[];
  sentiment: string;
};

export type EngineVisibilityReport = {
  engine_code: string;
  engine_name: string;
  available: boolean;
  reason_unavailable: string | null;
  observations: QueryObservation[];
  brand_mention_rate: number;
  recommendation_rate: number;
  average_recommendation_position: number | null;
  ai_share_of_voice: number | null;
  top_competitor_mentions: string[];
  top_cited_domains: string[];
  top_brand_attributes: string[];
  dominant_sentiment: string;
};

export type AiVisibilityReport = {
  brand: string;
  queries: { intent: string; query_text: string }[];
  engine_reports: EngineVisibilityReport[];
  universal_share_of_answer: number | null;
  universal_ai_share_of_voice: number | null;
  topic_visibility: Record<string, number>;
  disclaimer: string;
};

export type CitationGapResult = {
  cited_url: string;
  cited_domain: string;
  source_class: string;
  engine_codes: string[];
  topic_context: string;
  fetch_status: string;
  cited_page_title: string | null;
  cited_page_word_count: number | null;
  entity_gap: string[];
  evidence_gap: string;
  source_gap: boolean;
  statistics_gap: string;
  authority_gap: string;
  content_gap: string[];
  recommended_fix: string[];
};

export type CitationGapReport = {
  client_brand: string;
  citations_observed: number;
  citations_analysed: number;
  gaps: CitationGapResult[];
  disclaimer: string;
};

export type ContentRecommendation = {
  content_type: string;
  title: string;
  rationale: string;
  target_topics: string[];
  priority: string;
};

export type ContentGraphNode = { kind: string; key: string; label: string };
export type ContentGraphEdge = { from_kind: string; from_key: string; to_kind: string; to_key: string };
export type ContentGraph = { nodes: ContentGraphNode[]; edges: ContentGraphEdge[] };

export type ContentBrief = {
  topic: string;
  research_notes: string[];
  outline: string[];
  draft_skeleton: string;
  sources_needed: string[];
  faqs: { question: string; answer: string }[];
  suggested_title: string;
  suggested_meta_description: string;
  suggested_schema: string;
  internal_link_suggestions: string[];
  cta_suggestion: string;
  optimization_checklist: string[];
  confidence: string;
};

export type ContentSimulation = {
  topic: string;
  brand: string;
  geo_score_breakdown: SiteIntelligenceReport["geo_score_breakdown"];
  per_platform: { engine_code: string; engine_name: string; geo_readiness_score: number; live_critique_available: boolean; live_critique: string | null; note: string }[];
  disclaimer: string;
};

export type Opportunity = {
  action: string;
  reason: string;
  affected_page: string;
  seo_opportunity: string;
  aeo_opportunity: string;
  geo_opportunity: string;
  ai_visibility_opportunity: string;
  business_value: string;
  competitor_gap: string;
  implementation_difficulty: string;
  confidence: string;
  priority: string;
  peacock_impact_score: number;
};

export type AgentTask = { title: string; detail: string; priority: string; requires_approval: boolean };
export type AgentDraft = { draft_type: string; target: string; content: string };
export type AgentResult = {
  agent_name: string;
  summary: string;
  findings: string[];
  recommendations: string[];
  tasks: AgentTask[];
  drafts: AgentDraft[];
  problems_detected: string[];
  guardrail_note: string;
};

export type ExpertTask = {
  task_id: string;
  title: string;
  task_type: string;
  content: string;
  status: string;
  assignee: string | null;
  assignee_role: string | null;
  comments: { author: string; body: string; created_at: string }[];
  versions: { version: number; content: string; changed_by: string; changed_at: string; note: string | null }[];
  review_notes: string[];
  approved_by: string | null;
  approved_at: string | null;
  created_at: string;
  updated_at: string;
};

export type PublishResult = {
  connector: string;
  published: boolean;
  status: string;
  detail: string;
  external_url: string | null;
  external_id: string | null;
};

export type Snapshot = {
  url: string;
  captured_at: string;
  seo_score: number;
  aeo_score: number;
  geo_score: number;
  information_gain_score: number;
  word_count: number;
  content_hash: string | null;
  citations_count: number;
  ai_mentions: number | null;
  universal_share_of_answer: number | null;
};

export type RecommendationRecord = {
  record_id: string;
  recommendation: string;
  recommendation_type: string;
  page_url: string;
  logged_at: string;
  baseline_score: number | null;
  confidence_at_log_time: string;
  action_taken: boolean;
  result_7_day: number | null;
  result_30_day: number | null;
  result_90_day: number | null;
  outcome: string;
};

export type ExecutiveSummary = {
  peacock_visibility_score: number;
  seo: number;
  aeo: number;
  geo: number;
  ai_visibility: number | null;
  citation_authority: number;
  entity_authority: number;
  content_authority: number;
  technical_health: number | null;
  information_gain: number;
  competitive_position: string;
  what_changed: string;
  why: string;
  what_should_we_do_next: string;
  highest_impact_opportunity: Opportunity | null;
  which_agent_is_working: string[];
  requires_human_approval: ExpertTask[];
  what_worked: string;
  what_failed: string;
};

export type GrowthLoopReport = {
  url: string;
  brand: string;
  stages: GrowthLoopStage[];
  site_intelligence: SiteIntelligenceReport;
  ai_visibility: AiVisibilityReport;
  citation_gaps: CitationGapReport;
  content_recommendations: ContentRecommendation[];
  content_graph: ContentGraph;
  top_content_brief: ContentBrief | null;
  content_simulation: ContentSimulation | null;
  top_opportunities: Opportunity[];
  agent_results: Record<string, AgentResult>;
  expert_task: ExpertTask | null;
  publishing_preview: PublishResult | null;
  measurement_snapshot: Snapshot | null;
  learning_record: RecommendationRecord | null;
  executive_summary: ExecutiveSummary;
  disclaimer: string;
};

export class GrowthLoopError extends Error {}

export async function runGrowthLoop(
  url: string,
  options?: { competitorUrl?: string; maxPages?: number; engineCodes?: string[] },
): Promise<GrowthLoopReport> {
  const response = await fetch(`${getApiBaseUrl()}/growth-loop/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      url,
      competitor_url: options?.competitorUrl || null,
      max_pages: options?.maxPages ?? 6,
      engine_codes: options?.engineCodes ?? null,
    }),
  });
  if (!response.ok) {
    const body = await response.text();
    let detail = body;
    try {
      detail = JSON.parse(body).detail || body;
    } catch {
      // keep raw body
    }
    throw new GrowthLoopError(detail || `Request failed: ${response.status}`);
  }
  return (await response.json()) as GrowthLoopReport;
}

export async function assignExpertTask(taskId: string, assignee: string, assigneeRole: string): Promise<ExpertTask> {
  return apiFetch<ExpertTask>(`/growth-loop/experts/tasks/${taskId}/assign`, {
    method: "POST",
    body: JSON.stringify({ assignee, assignee_role: assigneeRole }),
  });
}

export async function startExpertReview(taskId: string): Promise<ExpertTask> {
  return apiFetch<ExpertTask>(`/growth-loop/experts/tasks/${taskId}/start-review`, { method: "POST" });
}

export async function approveExpertTask(taskId: string, approver: string): Promise<ExpertTask> {
  return apiFetch<ExpertTask>(`/growth-loop/experts/tasks/${taskId}/approve`, {
    method: "POST",
    body: JSON.stringify({ approver }),
  });
}

export async function markReadyToPublish(taskId: string): Promise<ExpertTask> {
  return apiFetch<ExpertTask>(`/growth-loop/experts/tasks/${taskId}/ready-to-publish`, { method: "POST" });
}

export async function listPublishingConnectors(): Promise<{ connectors: { name: string; configured: boolean }[] }> {
  return apiFetch(`/growth-loop/publishing/connectors`);
}

export async function logExperiment(hypothesis: string, pageUrl: string, changeDescription: string, changeCategory = "other") {
  return apiFetch(`/growth-loop/experiments`, {
    method: "POST",
    body: JSON.stringify({ hypothesis, page_url: pageUrl, change_description: changeDescription, change_category: changeCategory }),
  });
}
