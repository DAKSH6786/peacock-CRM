/**
 * Prompt Universe Intelligence — complete intent landscape, not a fixed 25/50/100 set.
 */

import { createHash } from "crypto";

export const PROMPT_TYPES = [
  "discovery",
  "recommendation",
  "comparison",
  "problem_solving",
  "purchase",
  "research",
  "validation",
  "alternative",
  "pricing",
  "trust",
  "risk",
  "technical",
  "educational",
  "transactional",
] as const;

export type PromptType = (typeof PROMPT_TYPES)[number];

export const PROMPT_SOURCE_KINDS = [
  "product",
  "service",
  "keyword",
  "search_console_query",
  "competitor_ranking",
  "forum",
  "serp",
  "people_also_ask",
  "customer_persona",
  "funnel_stage",
  "location",
  "industry_concept",
  "ai_query_pattern",
  "prompt_taxonomy",
  "manual",
] as const;

export type PromptSourceKind = (typeof PROMPT_SOURCE_KINDS)[number];

export const FUNNEL_STAGES = [
  "awareness",
  "consideration",
  "decision",
  "retention",
  "advocacy",
] as const;

export type FunnelStage = (typeof FUNNEL_STAGES)[number];

export type SyntheticPersona = {
  code: string;
  name: string;
  description: string;
  queryStyle: string;
  contextTemplate: string;
};

/** Analytical personas — not fake real identities. */
export const SYNTHETIC_PERSONAS: SyntheticPersona[] = [
  {
    code: "cfo",
    name: "CFO",
    description:
      "Financial decision-maker focused on ROI, risk, and budget control.",
    queryStyle: "quantitative",
    contextTemplate:
      "We are evaluating vendors with strict budget governance. Focus on total cost of ownership, ROI evidence, contractual risk, and financial controls.",
  },
  {
    code: "cmo",
    name: "CMO",
    description:
      "Marketing leader focused on brand, demand, and channel performance.",
    queryStyle: "strategic",
    contextTemplate:
      "We need options that improve pipeline quality and brand authority. Emphasise demand generation impact, attribution clarity, and channel fit.",
  },
  {
    code: "student",
    name: "Student",
    description:
      "Learner seeking accessible explanations and affordable options.",
    queryStyle: "exploratory",
    contextTemplate:
      "I am learning this space and need clear, affordable recommendations with plain-language explanations.",
  },
  {
    code: "enterprise_buyer",
    name: "Enterprise buyer",
    description:
      "Procurement-oriented buyer evaluating vendors at scale.",
    queryStyle: "rigorous",
    contextTemplate:
      "We are a large organisation running a formal shortlist process. Require enterprise readiness, security posture, SLAs, and procurement fit.",
  },
  {
    code: "technical_evaluator",
    name: "Technical evaluator",
    description:
      "Specialist assessing architecture, integrations, and operational fit.",
    queryStyle: "precise",
    contextTemplate:
      "I am assessing architecture, APIs, data residency, integrations, and operational maintainability in detail.",
  },
  {
    code: "hnwi",
    name: "HNWI",
    description:
      "High-net-worth individual seeking premium, trusted solutions.",
    queryStyle: "discerning",
    contextTemplate:
      "I want premium, highly trusted options with white-glove support and proven outcomes for sophisticated buyers.",
  },
  {
    code: "small_business_owner",
    name: "Small business owner",
    description:
      "Owner-operator balancing cost, simplicity, and speed to value.",
    queryStyle: "pragmatic",
    contextTemplate:
      "I run a small business and need something practical, affordable, and quick to implement without a large team.",
  },
  {
    code: "developer",
    name: "Developer",
    description:
      "Builder focused on APIs, docs, DX, and technical constraints.",
    queryStyle: "technical",
    contextTemplate:
      "I care about API quality, documentation, extensibility, and engineering time-to-integrate.",
  },
  {
    code: "parent",
    name: "Parent",
    description:
      "Household decision-maker prioritising safety, clarity, and value.",
    queryStyle: "cautious",
    contextTemplate:
      "I need safe, clear, and reliable recommendations that are easy to understand for a household decision.",
  },
  {
    code: "healthcare_professional",
    name: "Healthcare professional",
    description:
      "Clinical or care professional needing compliance-aware, evidence-based answers.",
    queryStyle: "careful",
    contextTemplate:
      "Recommendations must be compliance-aware, evidence-oriented, and suitable for regulated healthcare contexts.",
  },
];

const TYPE_TO_FUNNEL: Record<PromptType, FunnelStage> = {
  discovery: "awareness",
  recommendation: "consideration",
  comparison: "consideration",
  problem_solving: "consideration",
  purchase: "decision",
  research: "awareness",
  validation: "decision",
  alternative: "consideration",
  pricing: "decision",
  trust: "decision",
  risk: "decision",
  technical: "consideration",
  educational: "awareness",
  transactional: "decision",
};

const TYPE_TO_INTENT: Record<PromptType, string> = {
  discovery: "informational",
  recommendation: "commercial",
  comparison: "commercial",
  problem_solving: "informational",
  purchase: "transactional",
  research: "informational",
  validation: "commercial",
  alternative: "commercial",
  pricing: "commercial",
  trust: "commercial",
  risk: "commercial",
  technical: "informational",
  educational: "informational",
  transactional: "transactional",
};

const TYPE_COMMERCIAL: Record<PromptType, number> = {
  discovery: 0.35,
  recommendation: 0.75,
  comparison: 0.8,
  problem_solving: 0.55,
  purchase: 0.95,
  research: 0.4,
  validation: 0.7,
  alternative: 0.72,
  pricing: 0.88,
  trust: 0.65,
  risk: 0.6,
  technical: 0.58,
  educational: 0.3,
  transactional: 0.92,
};

export type SourceSignal = {
  sourceKind: PromptSourceKind;
  signalText: string;
  weight?: number;
  locationCode?: string;
  productName?: string;
  topicHint?: string;
};

export type UniversePrompt = {
  promptText: string;
  promptHash: string;
  topic: string;
  subtopic: string | null;
  intent: string;
  persona: string;
  funnelStage: FunnelStage;
  location: string;
  product: string | null;
  problem: string | null;
  commercialValue: number;
  brandRelevance: number;
  promptType: PromptType;
  sourceKind: PromptSourceKind;
  complexity: "simple" | "contextual";
  familySlug: string;
  familyName: string;
};

export type ExpandOptions = {
  brandName: string;
  industry?: string;
  location?: string;
  signals: SourceSignal[];
  personaCodes?: string[];
  includePersonaVariants?: boolean;
  maxPrompts?: number;
};

function promptHash(text: string): string {
  return createHash("sha256").update(text.trim()).digest("hex");
}

function slugify(text: string, maxLen = 140): string {
  const s = text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
  return (s || "family").slice(0, maxLen);
}

function clamp01(n: number): number {
  return Math.max(0, Math.min(1, n));
}

function brandRelevance(kind: PromptSourceKind, weight: number): number {
  const base: Partial<Record<PromptSourceKind, number>> = {
    product: 0.9,
    service: 0.88,
    keyword: 0.7,
    search_console_query: 0.85,
    competitor_ranking: 0.75,
    forum: 0.55,
    serp: 0.65,
    people_also_ask: 0.6,
    ai_query_pattern: 0.8,
  };
  return clamp01((base[kind] ?? 0.55) * (0.75 + 0.25 * Math.min(weight, 2)));
}

function typesForSource(kind: PromptSourceKind): PromptType[] {
  const core: PromptType[] = [
    "discovery",
    "recommendation",
    "comparison",
    "pricing",
    "alternative",
    "trust",
    "technical",
    "purchase",
  ];
  if (kind === "people_also_ask" || kind === "forum") {
    return [
      ...core,
      "problem_solving",
      "research",
      "educational",
      "validation",
      "risk",
    ];
  }
  if (
    kind === "search_console_query" ||
    kind === "ai_query_pattern" ||
    kind === "keyword" ||
    kind === "serp"
  ) {
    return [...core, "research", "educational", "validation"];
  }
  if (
    kind === "competitor_ranking" ||
    kind === "product" ||
    kind === "service"
  ) {
    return [...core, "transactional", "validation", "risk"];
  }
  return core;
}

function simpleTemplate(
  type: PromptType,
  subject: string,
  brand: string,
  location: string,
): string {
  const loc =
    location === "global" || !location ? "" : ` in ${location.toUpperCase()}`;
  const map: Record<PromptType, string> = {
    discovery: `what is ${subject}${loc}`,
    recommendation: `best ${subject}${loc}`,
    comparison: `${subject} vs alternatives${loc}`,
    problem_solving: `how to solve ${subject} problems${loc}`,
    purchase: `buy ${subject}${loc}`,
    research: `${subject} overview and key considerations${loc}`,
    validation: `is ${brand} a good ${subject}${loc}`,
    alternative: `alternatives to ${subject}${loc}`,
    pricing: `${subject} pricing${loc}`,
    trust: `is ${subject} trustworthy${loc}`,
    risk: `risks of choosing ${subject}${loc}`,
    technical: `${subject} technical requirements and integrations${loc}`,
    educational: `explain ${subject} for beginners${loc}`,
    transactional: `get a demo of ${subject}${loc}`,
  };
  return map[type];
}

function contextualTemplate(
  type: PromptType,
  subject: string,
  brand: string,
  location: string,
  persona: SyntheticPersona,
  industry?: string,
  problem?: string | null,
): string {
  const locClause =
    location && location !== "global"
      ? ` Prefer vendors with presence or data residency suitable for ${location.toUpperCase()}.`
      : "";
  const industryClause = industry ? ` Industry context: ${industry}.` : "";
  const problemClause = problem ? ` Core problem: ${problem}.` : "";
  const asks: Record<PromptType, string> = {
    discovery: `Explain what ${subject} is and when organisations should use it.`,
    recommendation: `Which ${subject} platforms should we shortlist and why?`,
    comparison: `Compare leading ${subject} options against each other and against ${brand}.`,
    problem_solving: `How should we approach solving ${problem ?? subject} with the right platform?`,
    purchase: `What is the recommended buying process and shortlist for ${subject}?`,
    research: `Provide a structured research brief on ${subject} for our evaluation committee.`,
    validation: `Validate whether ${brand} belongs on a serious shortlist for ${subject}.`,
    alternative: `What credible alternatives to ${subject} / ${brand} should we evaluate?`,
    pricing: `How should we compare pricing models and TCO for ${subject} vendors?`,
    trust: `Which trust, security, and reputation signals matter most when choosing ${subject}?`,
    risk: `What are the main risks of selecting the wrong ${subject} vendor, and how do we mitigate them?`,
    technical: `What technical evaluation criteria should we use for ${subject} platforms?`,
    educational: `Educate our stakeholders on ${subject} fundamentals before vendor demos.`,
    transactional: `What next steps and proof points should we request before purchasing ${subject}?`,
  };
  return `${persona.contextTemplate}${industryClause}${problemClause}${locClause}\n\n${asks[type]}`;
}

export function expandPromptUniverse(options: ExpandOptions): {
  prompts: UniversePrompt[];
  familyCount: number;
  simpleCount: number;
  contextualCount: number;
} {
  const location = options.location ?? "global";
  const includeVariants = options.includePersonaVariants !== false;
  const maxPrompts = options.maxPrompts ?? 500;
  const personas = (
    options.personaCodes?.length
      ? SYNTHETIC_PERSONAS.filter((p) => options.personaCodes!.includes(p.code))
      : SYNTHETIC_PERSONAS
  ) as SyntheticPersona[];

  const prompts: UniversePrompt[] = [];
  const seen = new Set<string>();
  const families = new Set<string>();

  for (const signal of options.signals) {
    const weight = signal.weight ?? 1;
    const subject = (signal.productName ?? signal.signalText).trim();
    const topic = (signal.topicHint ?? subject).trim();
    const familySlug = slugify(`${signal.sourceKind}-${topic}`);
    const familyName = `${topic} intent family`;
    const problem =
      signal.sourceKind === "people_also_ask" || signal.sourceKind === "forum"
        ? signal.signalText
        : null;
    const loc = signal.locationCode ?? location;
    const brandRel = brandRelevance(signal.sourceKind, weight);
    families.add(familySlug);

    for (const promptType of typesForSource(signal.sourceKind)) {
      const cv = clamp01(
        TYPE_COMMERCIAL[promptType] * (0.7 + 0.3 * Math.min(weight, 2)),
      );
      const simpleText = simpleTemplate(
        promptType,
        subject,
        options.brandName,
        loc,
      );
      const simpleKey = `${promptHash(simpleText)}|general`;
      if (!seen.has(simpleKey) && prompts.length < maxPrompts) {
        seen.add(simpleKey);
        prompts.push({
          promptText: simpleText,
          promptHash: promptHash(simpleText),
          topic,
          subtopic: promptType.replace(/_/g, " "),
          intent: TYPE_TO_INTENT[promptType],
          persona: "general",
          funnelStage: TYPE_TO_FUNNEL[promptType],
          location: loc,
          product:
            signal.productName ??
            (signal.sourceKind === "product" || signal.sourceKind === "service"
              ? subject
              : null),
          problem,
          commercialValue: cv,
          brandRelevance: brandRel,
          promptType,
          sourceKind: signal.sourceKind,
          complexity: "simple",
          familySlug,
          familyName,
        });
      }

      if (!includeVariants) continue;

      for (const persona of personas) {
        if (
          promptType === "educational" &&
          (persona.code === "hnwi" || persona.code === "cfo")
        ) {
          continue;
        }
        const contextual = contextualTemplate(
          promptType,
          subject,
          options.brandName,
          loc,
          persona,
          options.industry,
          problem,
        );
        const key = `${promptHash(contextual)}|${persona.code}`;
        if (seen.has(key) || prompts.length >= maxPrompts) continue;
        seen.add(key);

        let personaCv = cv;
        if (
          ["cfo", "enterprise_buyer", "technical_evaluator"].includes(
            persona.code,
          ) &&
          ["purchase", "pricing", "comparison", "recommendation"].includes(
            promptType,
          )
        ) {
          personaCv = Math.min(1, cv + 0.08);
        }

        prompts.push({
          promptText: contextual,
          promptHash: promptHash(contextual),
          topic,
          subtopic: `${promptType.replace(/_/g, " ")} · ${persona.name}`,
          intent: TYPE_TO_INTENT[promptType],
          persona: persona.code,
          funnelStage: TYPE_TO_FUNNEL[promptType],
          location: loc,
          product:
            signal.productName ??
            (signal.sourceKind === "product" || signal.sourceKind === "service"
              ? subject
              : null),
          problem,
          commercialValue: personaCv,
          brandRelevance: brandRel,
          promptType,
          sourceKind: signal.sourceKind,
          complexity: "contextual",
          familySlug,
          familyName,
        });
      }
    }
    if (prompts.length >= maxPrompts) break;
  }

  return {
    prompts,
    familyCount: families.size,
    simpleCount: prompts.filter((p) => p.complexity === "simple").length,
    contextualCount: prompts.filter((p) => p.complexity === "contextual")
      .length,
  };
}

export function promptUniverseCatalog() {
  return {
    promptTypes: [...PROMPT_TYPES],
    sourceKinds: [...PROMPT_SOURCE_KINDS],
    funnelStages: [...FUNNEL_STAGES],
    syntheticPersonas: SYNTHETIC_PERSONAS.map((p) => ({
      code: p.code,
      name: p.name,
      description: p.description,
      queryStyle: p.queryStyle,
    })),
  };
}
