import { getApiBaseUrl } from "@/lib/api";

export type ScoreResult = {
  code: string;
  label: string;
  score: number;
  confidence: number;
  major_positive_factors: string[];
  major_negative_factors: string[];
};

export type SeoRecommendation = {
  code: string;
  title: string;
  priority: string;
  impact: number;
  effort: number;
  confidence: number;
  suggested_fix: string;
  priority_score: number;
};

export type SeoAuditPreview = {
  title: string;
  summary: string;
  peacock_seo_score: ScoreResult;
  scores: Record<string, ScoreResult>;
  recommendations: SeoRecommendation[];
  critical_issues: unknown[];
  warnings: unknown[];
  opportunities: unknown[];
};

export const DEMO_SEO_AUDIT: SeoAuditPreview = {
  title: "Acme — Peacock SEO preview audit",
  summary: "Peacock SEO Score 84.7/100 (confidence 0.82). 2 critical, 5 warnings, 3 opportunities across 3 crawled page(s).",
  peacock_seo_score: {
    code: "peacock_seo_score",
    label: "Peacock SEO Score",
    score: 84.7,
    confidence: 0.82,
    major_positive_factors: ["Strong overall Peacock SEO Score", "robots.txt present", "sitemap discovered"],
    major_negative_factors: [],
  },
  scores: {},
  recommendations: [
    {
      code: "demo",
      title: "Add a unique title and meta description to /pricing",
      priority: "high",
      impact: 0.7,
      effort: 0.2,
      confidence: 0.8,
      suggested_fix: "Write a unique, descriptive <title> (30–65 characters) and meta description.",
      priority_score: 0.6,
    },
  ],
  critical_issues: [],
  warnings: [],
  opportunities: [],
};

export async function fetchSeoAuditPreview(brand = "Acme"): Promise<SeoAuditPreview> {
  try {
    const res = await fetch(`${getApiBaseUrl()}/seo/preview?brand=${encodeURIComponent(brand)}`, {
      cache: "no-store",
    });
    if (!res.ok) return DEMO_SEO_AUDIT;
    return (await res.json()) as SeoAuditPreview;
  } catch {
    return DEMO_SEO_AUDIT;
  }
}

export type AeoAuditPreview = {
  aeo_score: number;
  answerability_score: number;
  faq_coverage_score: number;
  citation_readiness_score: number;
  entity_coverage: number;
  question_coverage: number;
  recommendations: string[];
  scoring_note: string;
};

export const DEMO_AEO_AUDIT: AeoAuditPreview = {
  aeo_score: 53,
  answerability_score: 53,
  faq_coverage_score: 48,
  citation_readiness_score: 41,
  entity_coverage: 38,
  question_coverage: 45,
  recommendations: [
    "Add an FAQ block with direct, quotable answers.",
    "Increase entity density with named products, people, and organisations.",
  ],
  scoring_note:
    "Proprietary deterministic estimate from crawled page structure — not a live answer-engine ranking.",
};

export async function fetchAeoAuditPreview(brand = "Acme"): Promise<AeoAuditPreview> {
  try {
    const res = await fetch(`${getApiBaseUrl()}/aeo/preview?brand=${encodeURIComponent(brand)}`, {
      cache: "no-store",
    });
    if (!res.ok) return DEMO_AEO_AUDIT;
    return (await res.json()) as AeoAuditPreview;
  } catch {
    return DEMO_AEO_AUDIT;
  }
}

export type GeoAuditPreview = {
  hypothesis: string;
  overall_causality_level: string;
  overall_summary: string;
  causality_warning: string;
  design_features: string[];
};

export const DEMO_GEO_AUDIT: GeoAuditPreview = {
  hypothesis: "Publishing an original benchmarks dataset increases AI citation probability.",
  overall_causality_level: "correlation",
  overall_summary:
    "GEO Lab analysed 2 page(s), 1 metric(s), 4 observation(s). Overall causality ceiling: correlation.",
  causality_warning:
    "CAUSALITY WARNING: Peacock GEO Lab does NOT automatically conclude that Change X caused a visibility improvement.",
  design_features: ["before_after", "control_pages", "test_pages"],
};

export async function fetchGeoAuditPreview(brand = "Acme"): Promise<GeoAuditPreview> {
  try {
    const res = await fetch(`${getApiBaseUrl()}/geo-lab/preview?brand=${encodeURIComponent(brand)}`, {
      cache: "no-store",
    });
    if (!res.ok) return DEMO_GEO_AUDIT;
    return (await res.json()) as GeoAuditPreview;
  } catch {
    return DEMO_GEO_AUDIT;
  }
}
