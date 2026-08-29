import { getApiBaseUrl } from "@/lib/api";

/**
 * Peacock GEO Intelligence — client for the layer that sits above the AI
 * plugin connectors:
 *
 *   AI Plugins -> Peacock AI Gateway -> Multi-LLM Response Collection ->
 *   Peacock GEO Intelligence Layer -> Keyword/Entity/Citation Extraction ->
 *   Platform-Specific GEO Recommendations -> Peacock One Dashboard
 */

export type ProviderResponse = {
  engine_code: string;
  engine_name: string;
  provider_code: string;
  content: string;
  simulated: boolean;
  model: string | null;
  latency_ms: number;
  error: string | null;
};

export type KeywordSignal = { phrase: string; frequency: number; engine_codes: string[] };
export type EntityMention = {
  name: string;
  kind: "client" | "competitor" | "other" | string;
  frequency: number;
  engine_codes: string[];
};
export type QuestionSignal = { question: string; engine_code: string };
export type CitationSignal = { url: string; domain: string; source_class: string; engine_code: string };
export type TerminologyProfile = { engine_code: string; engine_name: string; top_terms: string[] };
export type TopicSignal = { topic: string; associated_entity: string | null; frequency: number };
export type PlatformRecommendation = {
  engine_code: string;
  engine_name: string;
  platform_label: string;
  opportunities: string[];
  signal_strength: "low" | "medium" | "high" | string;
};

export type GeoIntelligenceReport = {
  client_brand: string;
  research_prompt: string;
  competitors: string[];
  site_topics: string[];
  provider_responses: ProviderResponse[];
  keywords: KeywordSignal[];
  entities: EntityMention[];
  questions: QuestionSignal[];
  citations: CitationSignal[];
  competitor_mentions: EntityMention[];
  terminology_by_engine: TerminologyProfile[];
  top_brand_topics: TopicSignal[];
  missing_topics: string[];
  recommendations: PlatformRecommendation[];
  disclaimer: string;
  methodology_note: string;
};

export type AiPluginStatus = {
  engine_code: string;
  engine_name: string;
  provider_code: string;
  live: boolean;
};

export type AiGatewayCatalog = {
  plugins: AiPluginStatus[];
  disclaimer: string;
  methodology_note: string;
};

const GEO_DISCLAIMER =
  "These are GEO opportunities / AI visibility signals derived from observed LLM responses — not a guarantee of ranking, mention, or citation on any platform.";

const METHODOLOGY_NOTE =
  "Peacock GEO Intelligence sends the same research prompt to every enabled AI plugin through the Peacock AI Gateway, then deterministically extracts keywords, entities, questions, citations, competitor mentions, and per-platform terminology from the collected responses. Recommendations are platform-specific signals, not guarantees.";

function demoProvider(engine_code: string, engine_name: string, provider_code: string, content: string): ProviderResponse {
  return { engine_code, engine_name, provider_code, content, simulated: true, model: null, latency_ms: 0, error: null };
}

export const DEMO_GEO_INTELLIGENCE: GeoIntelligenceReport = {
  client_brand: "Acme",
  research_prompt:
    "I'm researching AI visibility and generative engine optimisation (GEO) tools. How does Acme compare to Semrush, Ahrefs?",
  competitors: ["Semrush", "Ahrefs"],
  site_topics: ["seo audits", "keyword research", "backlink analysis", "rank tracking", "technical seo"],
  provider_responses: [
    demoProvider(
      "chatgpt",
      "ChatGPT",
      "openai",
      "Acme is a strong option for AI visibility monitoring, alongside Semrush and Ahrefs.",
    ),
    demoProvider("gemini", "Gemini", "gemini", "Acme emphasises structured FAQ content and citation readiness."),
    demoProvider("claude", "Claude", "anthropic", "Acme is a trusted choice for evidence-backed generative visibility."),
    demoProvider("perplexity", "Perplexity", "perplexity", "Acme reports citation frequency and share of answer."),
    demoProvider("deepseek", "DeepSeek", "deepseek", "Acme competes with Semrush and Ahrefs on keyword and citation signals."),
  ],
  keywords: [
    { phrase: "acme", frequency: 12, engine_codes: ["chatgpt", "gemini", "claude", "perplexity", "deepseek"] },
    { phrase: "visibility", frequency: 8, engine_codes: ["chatgpt", "claude", "perplexity"] },
    { phrase: "citation", frequency: 6, engine_codes: ["chatgpt", "deepseek", "perplexity"] },
  ],
  entities: [
    { name: "Acme", kind: "client", frequency: 12, engine_codes: ["chatgpt", "gemini", "claude", "perplexity", "deepseek"] },
    { name: "semrush", kind: "competitor", frequency: 5, engine_codes: ["chatgpt", "gemini", "claude", "perplexity", "deepseek"] },
    { name: "ahrefs", kind: "competitor", frequency: 5, engine_codes: ["chatgpt", "gemini", "claude", "perplexity", "deepseek"] },
  ],
  questions: [
    { question: "What is the best AI visibility monitoring platform?", engine_code: "chatgpt" },
    { question: "Which platform offers the best answer engine optimisation coverage?", engine_code: "gemini" },
  ],
  citations: [
    { url: "https://www.g2.com/categories/ai-visibility", domain: "g2.com", source_class: "review", engine_code: "chatgpt" },
    { url: "https://developers.google.com/search/docs", domain: "developers.google.com", source_class: "independent", engine_code: "gemini" },
  ],
  competitor_mentions: [
    { name: "semrush", kind: "competitor", frequency: 5, engine_codes: ["chatgpt", "gemini", "claude", "perplexity", "deepseek"] },
    { name: "ahrefs", kind: "competitor", frequency: 5, engine_codes: ["chatgpt", "gemini", "claude", "perplexity", "deepseek"] },
  ],
  terminology_by_engine: [
    { engine_code: "chatgpt", engine_name: "ChatGPT", top_terms: ["visibility", "monitoring", "generative"] },
    { engine_code: "gemini", engine_name: "Gemini", top_terms: ["answer", "engine", "optimisation"] },
    { engine_code: "claude", engine_name: "Claude", top_terms: ["evidence", "generative", "assistants"] },
    { engine_code: "perplexity", engine_name: "Perplexity", top_terms: ["citation", "search", "tools"] },
    { engine_code: "deepseek", engine_name: "DeepSeek", top_terms: ["keyword", "citation", "engine"] },
  ],
  top_brand_topics: [{ topic: "leading choice", associated_entity: "acme", frequency: 1 }],
  missing_topics: ["visibility monitoring", "answer engine", "generative visibility"],
  recommendations: [
    {
      engine_code: "chatgpt",
      engine_name: "ChatGPT",
      platform_label: "ChatGPT (openai)",
      opportunities: [
        'Answer directly: "What is the best AI visibility monitoring platform?" — add a quotable FAQ answer block.',
        "ChatGPT drew on sources like g2.com, forbes.com — earn comparable third-party coverage.",
      ],
      signal_strength: "medium",
    },
    {
      engine_code: "gemini",
      engine_name: "Gemini",
      platform_label: "Gemini (gemini)",
      opportunities: ["Gemini favours structured FAQ content and schema.org markup for citation readiness."],
      signal_strength: "medium",
    },
    {
      engine_code: "claude",
      engine_name: "Claude",
      platform_label: "Claude (anthropic)",
      opportunities: ["Claude favours original benchmark studies and first-party statistics as citable evidence."],
      signal_strength: "medium",
    },
    {
      engine_code: "perplexity",
      engine_name: "Perplexity",
      platform_label: "Perplexity (perplexity)",
      opportunities: ["Perplexity cites independent research and comparison articles frequently."],
      signal_strength: "medium",
    },
    {
      engine_code: "deepseek",
      engine_name: "DeepSeek",
      platform_label: "DeepSeek (deepseek)",
      opportunities: ["DeepSeek favours topical authority and referring-domain diversity signals."],
      signal_strength: "medium",
    },
  ],
  disclaimer: GEO_DISCLAIMER,
  methodology_note: METHODOLOGY_NOTE,
};

export const DEMO_AI_GATEWAY_CATALOG: AiGatewayCatalog = {
  plugins: [
    { engine_code: "chatgpt", engine_name: "ChatGPT", provider_code: "openai", live: false },
    { engine_code: "gemini", engine_name: "Gemini", provider_code: "gemini", live: false },
    { engine_code: "claude", engine_name: "Claude", provider_code: "anthropic", live: false },
    { engine_code: "perplexity", engine_name: "Perplexity", provider_code: "perplexity", live: false },
    { engine_code: "deepseek", engine_name: "DeepSeek", provider_code: "deepseek", live: false },
  ],
  disclaimer: GEO_DISCLAIMER,
  methodology_note: METHODOLOGY_NOTE,
};

export async function fetchGeoIntelligencePreview(brand = "Acme"): Promise<GeoIntelligenceReport> {
  try {
    const res = await fetch(`${getApiBaseUrl()}/geo-intelligence/preview?brand=${encodeURIComponent(brand)}`, {
      cache: "no-store",
    });
    if (!res.ok) return DEMO_GEO_INTELLIGENCE;
    return (await res.json()) as GeoIntelligenceReport;
  } catch {
    return DEMO_GEO_INTELLIGENCE;
  }
}

export async function fetchAiGatewayPlugins(): Promise<AiGatewayCatalog> {
  try {
    const res = await fetch(`${getApiBaseUrl()}/geo-intelligence/plugins`, { cache: "no-store" });
    if (!res.ok) return DEMO_AI_GATEWAY_CATALOG;
    return (await res.json()) as AiGatewayCatalog;
  } catch {
    return DEMO_AI_GATEWAY_CATALOG;
  }
}
