import { ROLE_PROMPTS, renderUserPrompt, systemDirectiveFor } from "./roles";
import {
  assertRoleSupported,
  hashPrompt,
  type ConnectorProviderId,
  type ConnectorRequest,
  type ConnectorResponse,
  type ConnectorRoleId,
  type LlmConnector,
} from "./types";

export type SimulatedCompleter = (input: {
  provider: ConnectorProviderId;
  role: ConnectorRoleId;
  system: string;
  user: string;
  evidence: Record<string, unknown>;
}) => { content: string; structured?: Record<string, unknown> };

/**
 * Shared connector base. Live HTTP adapters can override `callProvider`.
 * Default path is deterministic simulation so the product works without API keys
 * and still exercises role-differentiated prompts.
 */
export abstract class BaseConnector implements LlmConnector {
  abstract readonly provider: ConnectorProviderId;
  abstract readonly supportedRoles: readonly ConnectorRoleId[];
  abstract readonly defaultModel: string;

  constructor(private readonly simulate: SimulatedCompleter) {}

  async complete(request: ConnectorRequest): Promise<ConnectorResponse> {
    assertRoleSupported(this, request.role);

    const expectedTemplate = ROLE_PROMPTS[request.role].templateId;
    if (request.templateId !== expectedTemplate) {
      throw new Error(
        `Role ${request.role} expects template ${expectedTemplate}, got ${request.templateId}`,
      );
    }

    const system = systemDirectiveFor(request.role);
    const user = renderUserPrompt(request.role, request.variables);
    const promptHash = hashPrompt(
      request.templateId,
      request.role,
      request.variables,
      Object.keys(request.evidence),
    );

    const started = Date.now();
    const result = this.simulate({
      provider: this.provider,
      role: request.role,
      system,
      user,
      evidence: request.evidence,
    });

    return {
      provider: this.provider,
      role: request.role,
      model: this.defaultModel,
      promptHash,
      templateId: request.templateId,
      content: result.content,
      structured: result.structured,
      latencyMs: Date.now() - started,
      tokenIn: Math.ceil((system.length + user.length) / 4),
      tokenOut: Math.ceil(result.content.length / 4),
      simulated: true,
    };
  }
}
