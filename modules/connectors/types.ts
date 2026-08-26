import { createHash } from "node:crypto";

export type ConnectorProviderId =
  "OPENAI" | "GEMINI" | "ANTHROPIC" | "PERPLEXITY" | "DEEPSEEK";

export type ConnectorRoleId =
  | "WEB_RESEARCH"
  | "CITATION_HUNT"
  | "STRUCTURAL_CRITIQUE"
  | "CONTENT_QUALITY"
  | "VERIFY_ADVERSARIAL"
  | "SYNTHESIS"
  | "STRATEGY_FRAME"
  | "WRITER_BRIEF"
  | "ENTITY_EXTRACTION"
  | "MULTIMODAL_PAGE"
  | "KNOWLEDGE_LINK"
  | "SECOND_OPINION"
  | "COST_SWEEP"
  | "VERIFY_CONSENSUS"
  | "VISIBILITY_PROBE";

export type PromptTemplateId =
  | "observe.web_research"
  | "observe.citation_hunt"
  | "think.structural_critique"
  | "think.content_quality"
  | "think.entity_extraction"
  | "think.knowledge_link"
  | "think.synthesis"
  | "think.strategy_frame"
  | "think.second_opinion"
  | "think.cost_sweep"
  | "verify.adversarial"
  | "verify.consensus"
  | "execute.writer_brief"
  | "measure.visibility_probe"
  | "observe.multimodal_page";

/**
 * Role-bound request. Callers ask for a *role* + template, never “ask all models the same thing”.
 */
export type ConnectorRequest = {
  role: ConnectorRoleId;
  templateId: PromptTemplateId;
  /** Structured evidence / context — never free-form “do everything” blobs */
  evidence: Record<string, unknown>;
  /** Variables interpolated into the role-specific template */
  variables: Record<string, string | number | boolean>;
  /** Optional temperature / max tokens overrides */
  options?: {
    temperature?: number;
    maxTokens?: number;
  };
};

export type ConnectorResponse = {
  provider: ConnectorProviderId;
  role: ConnectorRoleId;
  model: string;
  promptHash: string;
  templateId: PromptTemplateId;
  content: string;
  structured?: Record<string, unknown>;
  latencyMs: number;
  tokenIn?: number;
  tokenOut?: number;
  simulated: boolean;
};

export interface LlmConnector {
  readonly provider: ConnectorProviderId;
  readonly supportedRoles: readonly ConnectorRoleId[];
  complete(request: ConnectorRequest): Promise<ConnectorResponse>;
}

export function hashPrompt(
  templateId: PromptTemplateId,
  role: ConnectorRoleId,
  variables: Record<string, string | number | boolean>,
  evidenceKeys: string[],
): string {
  const payload = JSON.stringify({
    templateId,
    role,
    variables,
    evidenceKeys: [...evidenceKeys].sort(),
  });
  return createHash("sha256").update(payload).digest("hex").slice(0, 24);
}

export function assertRoleSupported(
  connector: LlmConnector,
  role: ConnectorRoleId,
): void {
  if (!connector.supportedRoles.includes(role)) {
    throw new Error(
      `Provider ${connector.provider} does not support role ${role}`,
    );
  }
}
