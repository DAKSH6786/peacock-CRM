import type { CrawlPageArtifact } from "@/modules/crawl/analyze";

export type TechnicalSeoFinding = {
  id: string;
  severity: "low" | "medium" | "high";
  code: string;
  message: string;
  url?: string;
};

export function evaluateTechnicalSeo(
  pages: CrawlPageArtifact[],
): TechnicalSeoFinding[] {
  const findings: TechnicalSeoFinding[] = [];
  let i = 0;
  for (const page of pages) {
    for (const flag of page.technicalFlags) {
      findings.push({
        id: `tech-${++i}`,
        severity: severityFor(flag),
        code: flag,
        message: humanize(flag),
        url: page.url,
      });
    }
    if (page.statusCode >= 400) {
      findings.push({
        id: `tech-${++i}`,
        severity: "high",
        code: "http_error",
        message: `HTTP ${page.statusCode}`,
        url: page.url,
      });
    }
  }
  return findings;
}

function severityFor(flag: string): "low" | "medium" | "high" {
  if (flag === "thin_content" || flag === "missing_jsonld") return "medium";
  if (flag.startsWith("missing_")) return "high";
  return "low";
}

function humanize(flag: string): string {
  return flag.replaceAll("_", " ");
}
