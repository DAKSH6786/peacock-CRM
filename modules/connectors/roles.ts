import type {
  ConnectorProviderId,
  ConnectorRoleId,
  PromptTemplateId,
} from "./types";

/**
 * Canonical role → default provider mapping.
 * Pipeline stages request roles; the registry resolves providers.
 * This is the primary guard against identical prompt fan-out.
 */
export const DEFAULT_ROLE_PROVIDER: Record<
  ConnectorRoleId,
  ConnectorProviderId
> = {
  WEB_RESEARCH: "PERPLEXITY",
  CITATION_HUNT: "PERPLEXITY",
  STRUCTURAL_CRITIQUE: "ANTHROPIC",
  CONTENT_QUALITY: "ANTHROPIC",
  VERIFY_ADVERSARIAL: "ANTHROPIC",
  SYNTHESIS: "OPENAI",
  STRATEGY_FRAME: "OPENAI",
  WRITER_BRIEF: "OPENAI",
  ENTITY_EXTRACTION: "GEMINI",
  MULTIMODAL_PAGE: "GEMINI",
  KNOWLEDGE_LINK: "GEMINI",
  SECOND_OPINION: "DEEPSEEK",
  COST_SWEEP: "DEEPSEEK",
  VERIFY_CONSENSUS: "DEEPSEEK",
  VISIBILITY_PROBE: "OPENAI",
};

/**
 * Visibility probes intentionally use different templates per surface.
 * Measuring ChatGPT with a Claude critique prompt would be meaningless.
 */
export const VISIBILITY_PROBE_SURFACE_PROVIDER: Record<
  string,
  ConnectorProviderId
> = {
  CHATGPT: "OPENAI",
  GEMINI: "GEMINI",
  CLAUDE: "ANTHROPIC",
  PERPLEXITY: "PERPLEXITY",
  DEEPSEEK: "DEEPSEEK",
};

export type RolePromptSpec = {
  role: ConnectorRoleId;
  templateId: PromptTemplateId;
  /** System-level instruction unique to this role */
  systemDirective: string;
  /** User template — must reference evidence, not invent facts */
  userTemplate: string;
};

export const ROLE_PROMPTS: Record<ConnectorRoleId, RolePromptSpec> = {
  WEB_RESEARCH: {
    role: "WEB_RESEARCH",
    templateId: "observe.web_research",
    systemDirective:
      "You are a live-web research specialist. Return only sources and facts tied to the query. Do not invent rankings.",
    userTemplate:
      "Research current generative-search visibility signals for {{brand}} ({{domain}}). Focus topics: {{topics}}. Return bullet findings with source URLs.",
  },
  CITATION_HUNT: {
    role: "CITATION_HUNT",
    templateId: "observe.citation_hunt",
    systemDirective:
      "Find citable sources that answer engines may trust. Prefer primary sources.",
    userTemplate:
      "For brand {{brand}}, list high-authority citation opportunities related to: {{topics}}.",
  },
  STRUCTURAL_CRITIQUE: {
    role: "STRUCTURAL_CRITIQUE",
    templateId: "think.structural_critique",
    systemDirective:
      "Critique information architecture and schema using ONLY provided crawl/SEO artifacts. Cite artifact IDs.",
    userTemplate:
      "Given evidence {{evidenceSummary}}, critique structural SEO/AEO readiness for {{domain}}. Cite artifact IDs.",
  },
  CONTENT_QUALITY: {
    role: "CONTENT_QUALITY",
    templateId: "think.content_quality",
    systemDirective:
      "Assess content quality, EEAT, and answerability from provided page extracts only.",
    userTemplate:
      "Score content quality for {{domain}} using extracts in evidence. List gaps vs competitor themes: {{competitorThemes}}.",
  },
  VERIFY_ADVERSARIAL: {
    role: "VERIFY_ADVERSARIAL",
    templateId: "verify.adversarial",
    systemDirective:
      "You are an adversarial verifier. Reject claims not supported by artifact IDs. Output JSON: {accepted[], rejected[], gaps[]}.",
    userTemplate:
      "Verify these claims against artifacts: {{claims}}. Evidence keys: {{evidenceKeys}}.",
  },
  SYNTHESIS: {
    role: "SYNTHESIS",
    templateId: "think.synthesis",
    systemDirective:
      "Synthesize specialist outputs into a coherent diagnosis. Every bullet must cite an artifact or specialist role output.",
    userTemplate:
      "Synthesize specialist findings for {{brand}}. Inputs: {{specialistSummaries}}.",
  },
  STRATEGY_FRAME: {
    role: "STRATEGY_FRAME",
    templateId: "think.strategy_frame",
    systemDirective:
      "Frame a 90-day GEO/AEO/SEO strategy from decided priorities only. No new unverified claims.",
    userTemplate:
      "Build a 90-day frame for {{brand}} from priorities: {{priorities}}.",
  },
  WRITER_BRIEF: {
    role: "WRITER_BRIEF",
    templateId: "execute.writer_brief",
    systemDirective:
      "Produce a writer brief with audience, outline, entities, FAQs, and citation targets from approved recommendations.",
    userTemplate:
      "Writer brief for recommendation: {{recommendationTitle}}. Context: {{recommendationSummary}}.",
  },
  ENTITY_EXTRACTION: {
    role: "ENTITY_EXTRACTION",
    templateId: "think.entity_extraction",
    systemDirective:
      "Extract entities and types from page/crawl evidence. Prefer schema.org types.",
    userTemplate:
      "Extract entities for {{domain}} from evidence pages. Return name, type, evidence URL.",
  },
  MULTIMODAL_PAGE: {
    role: "MULTIMODAL_PAGE",
    templateId: "observe.multimodal_page",
    systemDirective:
      "Analyze page structure signals (headings, media, schema) from provided structured page data.",
    userTemplate:
      "Analyze page signals for {{url}} using structured page JSON in evidence.",
  },
  KNOWLEDGE_LINK: {
    role: "KNOWLEDGE_LINK",
    templateId: "think.knowledge_link",
    systemDirective:
      "Propose knowledge-graph edges between entities grounded in evidence.",
    userTemplate:
      "Link entities for {{brand}} into graph edges. Entities: {{entities}}.",
  },
  SECOND_OPINION: {
    role: "SECOND_OPINION",
    templateId: "think.second_opinion",
    systemDirective:
      "Independent second opinion. Challenge synthesis. Do not copy prior wording.",
    userTemplate:
      "Challenge this synthesis for {{brand}}: {{synthesis}}. What is overstated?",
  },
  COST_SWEEP: {
    role: "COST_SWEEP",
    templateId: "think.cost_sweep",
    systemDirective:
      "Economical sweep for missed quick wins from technical findings only.",
    userTemplate:
      "List quick wins from technical findings: {{technicalFindings}}.",
  },
  VERIFY_CONSENSUS: {
    role: "VERIFY_CONSENSUS",
    templateId: "verify.consensus",
    systemDirective:
      "Score consensus between specialist outputs. Return JSON {consensus:0-1, conflicts[]}.",
    userTemplate: "Score consensus across: {{specialistSummaries}}.",
  },
  VISIBILITY_PROBE: {
    role: "VISIBILITY_PROBE",
    templateId: "measure.visibility_probe",
    systemDirective:
      "Answer as a normal assistant user query. Do not mention Peacock One. We measure whether the brand appears naturally.",
    userTemplate: "{{probeQuestion}}",
  },
};

export function renderUserPrompt(
  role: ConnectorRoleId,
  variables: Record<string, string | number | boolean>,
): string {
  let template = ROLE_PROMPTS[role].userTemplate;
  for (const [key, value] of Object.entries(variables)) {
    template = template.replaceAll(`{{${key}}}`, String(value));
  }
  return template;
}

export function systemDirectiveFor(role: ConnectorRoleId): string {
  return ROLE_PROMPTS[role].systemDirective;
}
