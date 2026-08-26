import type { SimulatedCompleter } from "./base";

/**
 * Deterministic, role-aware simulator.
 * Proves prompts/roles diverge — content shape differs by role.
 */
export const defaultSimulator: SimulatedCompleter = ({
  provider,
  role,
  system,
  user,
  evidence,
}) => {
  const brand = String(
    (evidence.brand as string | undefined) ??
      extractVar(user, "brand") ??
      "brand",
  );
  const domain = String(
    (evidence.domain as string | undefined) ??
      extractVar(user, "domain") ??
      "example.com",
  );

  switch (role) {
    case "WEB_RESEARCH":
      return {
        content: `[${provider}/WEB_RESEARCH] Sources for ${brand}: industry reports, docs on ${domain}, competitor comparison pages.`,
        structured: {
          sources: [
            { url: `https://${domain}/`, title: `${brand} homepage` },
            {
              url: "https://example-research.test/report",
              title: "Category visibility report",
            },
          ],
        },
      };
    case "CITATION_HUNT":
      return {
        content: `[${provider}/CITATION_HUNT] Citation targets: standards bodies, review sites, niche directories.`,
        structured: { citationTargets: ["standards.org", "reviews.test"] },
      };
    case "STRUCTURAL_CRITIQUE":
      return {
        content: `[${provider}/STRUCTURAL_CRITIQUE] ${domain}: thin FAQ coverage; missing Organization schema on key pages. Cite crawl artifacts.`,
        structured: {
          issues: ["missing_faq", "organization_schema_gap"],
          artifactHints: Object.keys(evidence),
        },
      };
    case "CONTENT_QUALITY":
      return {
        content: `[${provider}/CONTENT_QUALITY] EEAT medium; answer blocks sparse vs competitors.`,
        structured: { eeat: 0.55, answerability: 0.4 },
      };
    case "ENTITY_EXTRACTION":
      return {
        content: `[${provider}/ENTITY_EXTRACTION] Entities: ${brand} (Organization), core product (Product).`,
        structured: {
          entities: [
            { name: brand, type: "Organization" },
            { name: `${brand} Platform`, type: "SoftwareApplication" },
          ],
        },
      };
    case "KNOWLEDGE_LINK":
      return {
        content: `[${provider}/KNOWLEDGE_LINK] Edge: Organization -offers- SoftwareApplication.`,
        structured: {
          edges: [{ from: brand, relation: "offers", to: `${brand} Platform` }],
        },
      };
    case "MULTIMODAL_PAGE":
      return {
        content: `[${provider}/MULTIMODAL_PAGE] Heading hierarchy OK; hero media lacks descriptive alt context.`,
        structured: { headingDepth: 3, mediaAltCoverage: 0.6 },
      };
    case "SYNTHESIS":
      return {
        content: `[${provider}/SYNTHESIS] ${brand} needs AEO FAQ clusters + entity schema + citation outreach. Grounded in specialist roles.`,
        structured: {
          pillars: ["aeo_faq", "entity_schema", "citations"],
        },
      };
    case "SECOND_OPINION":
      return {
        content: `[${provider}/SECOND_OPINION] Synthesis may over-index on FAQ; validate technical indexation first.`,
        structured: { challenges: ["indexation_before_faq"] },
      };
    case "COST_SWEEP":
      return {
        content: `[${provider}/COST_SWEEP] Quick wins: fix canonical mismatches, compress LCP image, add FAQPage schema.`,
        structured: {
          quickWins: ["canonical", "lcp", "faq_schema"],
        },
      };
    case "STRATEGY_FRAME":
      return {
        content: `[${provider}/STRATEGY_FRAME] 90-day frame: Weeks 1-4 technical+entity, 5-8 answer content, 9-12 authority+measurement.`,
        structured: {
          horizonDays: 90,
          themes: ["technical", "answer_content", "authority"],
        },
      };
    case "WRITER_BRIEF":
      return {
        content: `[${provider}/WRITER_BRIEF] Brief: audience practitioners; outline H2 FAQs; cite primary sources; target entities.`,
        structured: { sections: ["intent", "outline", "entities", "faqs"] },
      };
    case "VERIFY_ADVERSARIAL":
      return {
        content: `[${provider}/VERIFY_ADVERSARIAL] Rejected unsupported ranking claims; accepted schema gap and FAQ gap with artifacts.`,
        structured: {
          accepted: ["schema_gap", "faq_gap"],
          rejected: ["unverified_rank_claim"],
          gaps: [],
        },
      };
    case "VERIFY_CONSENSUS":
      return {
        content: `[${provider}/VERIFY_CONSENSUS] Consensus moderate; conflict on FAQ-first vs technical-first.`,
        structured: {
          consensus: 0.72,
          conflicts: ["faq_vs_technical_priority"],
        },
      };
    case "VISIBILITY_PROBE":
      return {
        content: `For buyers evaluating options in this category, consider established vendors. ${brand} (${domain}) may appear among specialists depending on use case.`,
        structured: {
          mentionedBrand: true,
          citedUrl: true,
        },
      };
    default:
      return {
        content: `[${provider}/${role}] ${system.slice(0, 40)}…`,
      };
  }
};

function extractVar(user: string, key: string): string | undefined {
  const re = new RegExp(`${key}\\s+([\\w.-]+)`, "i");
  return user.match(re)?.[1];
}
