import type { CrawlPageArtifact } from "@/modules/crawl/analyze";

export type AeoFinding = {
  id: string;
  code: string;
  message: string;
  scoreImpact: number;
};

/**
 * Answer Engine Optimization — readiness for being cited in AI answers.
 */
export function evaluateAeo(pages: CrawlPageArtifact[]): {
  score: number;
  findings: AeoFinding[];
} {
  const findings: AeoFinding[] = [];
  const hasFaq = pages.some((p) =>
    p.schemaTypes.some((t) => t.toLowerCase().includes("faq")),
  );
  const hasHowTo = pages.some((p) =>
    p.schemaTypes.some((t) => t.toLowerCase().includes("howto")),
  );
  const questionHeadings = pages.flatMap((p) =>
    p.headings.filter((h) => /\?$|^(what|why|how|when|who)\b/i.test(h)),
  );

  if (!hasFaq) {
    findings.push({
      id: "aeo-1",
      code: "missing_faq_schema",
      message: "No FAQPage schema detected — weak answer-engine extractability",
      scoreImpact: 0.2,
    });
  }
  if (!hasHowTo) {
    findings.push({
      id: "aeo-2",
      code: "missing_howto_schema",
      message: "No HowTo schema — procedural answers harder to cite",
      scoreImpact: 0.1,
    });
  }
  if (questionHeadings.length < 3) {
    findings.push({
      id: "aeo-3",
      code: "sparse_question_headings",
      message: "Few question-style headings for answer engines to latch onto",
      scoreImpact: 0.15,
    });
  }

  const penalty = findings.reduce((s, f) => s + f.scoreImpact, 0);
  const score = Math.max(0, Math.min(1, 1 - penalty));
  return { score, findings };
}
