import { getApiBaseUrl } from "@/lib/api";

/**
 * Peacock Site Intelligence — enterprise SEO + GEO reporting engine.
 * Triggers a REAL crawl of the given URL (and optional competitor URL)
 * through the backend, so this always returns live-measured data — there is
 * no static demo fallback for this endpoint.
 */

export type ScoreFactor = {
  metric: string;
  observed_value: unknown;
  benchmark: unknown;
  weight: number;
  score_contribution: number;
  evidence: string;
  confidence: string;
};

export type ExplainedScore = {
  score: number;
  label: string;
  summary: string;
  factors: ScoreFactor[];
};

export type GeoScoreBreakdown = {
  geo_score: number;
  formula: string;
  entity_authority: ExplainedScore;
  citation_readiness: ExplainedScore;
  answerability: ExplainedScore;
  evidence: ExplainedScore;
  topical_coverage: ExplainedScore;
  technical_ai_accessibility: ExplainedScore;
  brand_authority: ExplainedScore;
};

export type PageOpportunity = {
  url: string;
  title: string | null;
  seo_score: number;
  aeo_score: number;
  geo_score: number;
  content_score: number;
  technical_score: number;
  authority_score: number;
  information_gain_score: number;
  ai_citation_potential: number;
  whats_wrong: string[];
  why_it_matters: string[];
  evidence_found: string[];
  competitor_doing_better: string;
  exact_fix: string[];
  expected_impact: string;
  difficulty: string;
  priority: string;
  confidence: string;
  peacock_impact_score: number;
};

export type ImpactAction = {
  rank: number;
  title: string;
  impact_score: number;
  difficulty: string;
  seo_opportunity: string;
  geo_opportunity: string;
  competitors_winning: number;
  llms_showing_gap: string[];
  detail: string;
  confidence: string;
  day_bucket: number;
};

export type LlmKeywordMapEntry = {
  term: string;
  per_engine_present: Record<string, boolean>;
  opportunity: string;
};

export type CompetitiveAssociationGap = {
  competitor: string;
  competitor_topics: string[];
  brand_topics: string[];
  missing_topics: string[];
};

export type LlmKeywordMap = {
  entries: LlmKeywordMapEntry[];
  universal_terms: string[];
  platform_specific_terms: Record<string, string[]>;
  missing_semantic_entities: string[];
  competitive_association_gaps: CompetitiveAssociationGap[];
};

export type CompetitorComparison = {
  competitor_url: string | null;
  available: boolean;
  reason_unavailable: string | null;
  seo_visibility: string;
  content_coverage: string;
  keyword_coverage: string;
  entity_coverage: string;
  backlink_signals: string;
  topical_authority: string;
  structured_data: string;
  question_coverage: string;
  ai_mentions: string;
  ai_citations: string;
  cited_domain_overlap: string;
  source_authority: string;
  content_freshness: string;
  page_depth: string;
  information_gain_comparison: string;
  why_competitor_is_winning: string[];
};

export type PerLlmGeoScore = {
  engine_code: string;
  engine_name: string;
  available: boolean;
  score: number | null;
  reason_unavailable: string | null;
  brand_mentioned: boolean;
  entities_mentioned: string[];
  questions_raised: string[];
  citations: string[];
  opportunities: string[];
  confidence: string;
};

export type DataAvailability = { measured: string[]; unavailable: string[] };

export type SiteIntelligenceReport = {
  url: string;
  brand: string;
  crawled_pages_count: number;
  crawl_status: string;
  executive_summary: string;
  peacock_visibility_score: number;
  seo_score: number;
  aeo_score: number;
  geo_score: number;
  geo_score_breakdown: GeoScoreBreakdown;
  technical_health: Record<string, unknown>;
  ai_visibility: PerLlmGeoScore[];
  ai_citation_presence: { own_domain_cited_by_ai: boolean; total_citations_observed_across_platforms: number; note: string };
  information_gain_score: number;
  competitor_gap: CompetitorComparison;
  llm_by_llm_visibility: Array<{ engine_code: string; engine_name: string; platform_label: string; opportunities: string[]; signal_strength: string }>;
  critical_issues: string[];
  top_actions: ImpactAction[];
  keyword_opportunities: LlmKeywordMap;
  entity_opportunities: string[];
  content_gaps: string[];
  citation_opportunities: string[];
  backlink_opportunities: string;
  top_performing_pages: PageOpportunity[];
  weak_pages: PageOpportunity[];
  thirty_day_plan: ImpactAction[];
  sixty_day_plan: ImpactAction[];
  ninety_day_plan: ImpactAction[];
  data_availability: DataAvailability;
  pages: PageOpportunity[];
  disclaimer: string;
};

export class SiteIntelligenceError extends Error {}

export async function analyzeSite(
  url: string,
  options?: { competitorUrl?: string; maxPages?: number; engineCodes?: string[] },
): Promise<SiteIntelligenceReport> {
  const response = await fetch(`${getApiBaseUrl()}/site-intelligence/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      url,
      competitor_url: options?.competitorUrl || null,
      max_pages: options?.maxPages ?? 8,
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
    throw new SiteIntelligenceError(detail || `Request failed: ${response.status}`);
  }
  return (await response.json()) as SiteIntelligenceReport;
}
