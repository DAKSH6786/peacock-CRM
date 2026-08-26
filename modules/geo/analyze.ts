import type { CrawlPageArtifact } from "@/modules/crawl/analyze";

export type GeoFinding = {
  id: string;
  code: string;
  message: string;
  scoreImpact: number;
};

/**
 * Generative Engine Optimization — entity clarity, quotable facts, brand consistency.
 */
export function evaluateGeo(
  pages: CrawlPageArtifact[],
  brand: string,
): {
  score: number;
  findings: GeoFinding[];
} {
  const findings: GeoFinding[] = [];
  const brandMentions = pages.filter((p) =>
    `${p.title ?? ""} ${p.metaDescription ?? ""}`
      .toLowerCase()
      .includes(brand.toLowerCase()),
  ).length;
  const hasOrgSchema = pages.some((p) =>
    p.schemaTypes.some((t) => /organization|corporation/i.test(t)),
  );

  if (brandMentions === 0) {
    findings.push({
      id: "geo-1",
      code: "weak_brand_onpage",
      message:
        "Brand name rarely appears in title/description — weak GEO grounding",
      scoreImpact: 0.25,
    });
  }
  if (!hasOrgSchema) {
    findings.push({
      id: "geo-2",
      code: "missing_organization_schema",
      message: "Organization entity not declared in JSON-LD",
      scoreImpact: 0.2,
    });
  }
  const avgWords =
    pages.reduce((s, p) => s + p.wordCount, 0) / Math.max(pages.length, 1);
  if (avgWords < 400) {
    findings.push({
      id: "geo-3",
      code: "low_quotable_depth",
      message: "Average page depth low for generative citation",
      scoreImpact: 0.15,
    });
  }

  const penalty = findings.reduce((s, f) => s + f.scoreImpact, 0);
  return { score: Math.max(0, Math.min(1, 1 - penalty)), findings };
}
