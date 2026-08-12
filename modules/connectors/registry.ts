import {
  DEFAULT_ROLE_PROVIDER,
  ROLE_PROMPTS,
  VISIBILITY_PROBE_SURFACE_PROVIDER,
} from "./roles";
import { AnthropicConnector } from "./providers/anthropic";
import { DeepSeekConnector } from "./providers/deepseek";
import { GeminiConnector } from "./providers/gemini";
import { OpenAIConnector } from "./providers/openai";
import { PerplexityConnector } from "./providers/perplexity";
import type {
  ConnectorProviderId,
  ConnectorRequest,
  ConnectorResponse,
  ConnectorRoleId,
  LlmConnector,
} from "./types";

export class ConnectorRegistry {
  private readonly byProvider: Map<ConnectorProviderId, LlmConnector>;

  constructor(connectors?: LlmConnector[]) {
    const list = connectors ?? [
      new OpenAIConnector(),
      new AnthropicConnector(),
      new GeminiConnector(),
      new PerplexityConnector(),
      new DeepSeekConnector(),
    ];
    this.byProvider = new Map(list.map((c) => [c.provider, c]));
  }

  providerForRole(role: ConnectorRoleId): ConnectorProviderId {
    return DEFAULT_ROLE_PROVIDER[role];
  }

  get(provider: ConnectorProviderId): LlmConnector {
    const connector = this.byProvider.get(provider);
    if (!connector) {
      throw new Error(`Connector not registered: ${provider}`);
    }
    return connector;
  }

  /**
   * Execute a role-bound request. Refuses ambiguous “broadcast” patterns.
   */
  async runRole(request: ConnectorRequest): Promise<ConnectorResponse> {
    const provider = this.providerForRole(request.role);
    const connector = this.get(provider);
    return connector.complete(request);
  }

  /**
   * Visibility measurement across surfaces — each surface gets its own
   * provider and the dedicated VISIBILITY_PROBE template (not THINK prompts).
   */
  async runVisibilityProbes(input: {
    brand: string;
    domain: string;
    probeQuestion: string;
    surfaces?: string[];
  }): Promise<ConnectorResponse[]> {
    const surfaces =
      input.surfaces ?? Object.keys(VISIBILITY_PROBE_SURFACE_PROVIDER);

    const results: ConnectorResponse[] = [];
    for (const surface of surfaces) {
      const provider =
        VISIBILITY_PROBE_SURFACE_PROVIDER[surface] ??
        this.providerForRole("VISIBILITY_PROBE");
      const connector = this.get(provider);
      const response = await connector.complete({
        role: "VISIBILITY_PROBE",
        templateId: ROLE_PROMPTS.VISIBILITY_PROBE.templateId,
        evidence: {
          brand: input.brand,
          domain: input.domain,
          surface,
          measurementOnly: true,
        },
        variables: {
          probeQuestion: input.probeQuestion,
          brand: input.brand,
          domain: input.domain,
        },
      });
      results.push(response);
    }
    return results;
  }

  /**
   * Safety: detect accidental identical prompt fan-out attempts.
   */
  assertNotIdenticalFanout(
    requests: Array<{ role: ConnectorRoleId; templateId: string }>,
  ): void {
    if (requests.length < 2) return;
    const first = requests[0]!;
    const allSame = requests.every(
      (r) => r.role === first.role && r.templateId === first.templateId,
    );
    if (allSame && new Set(requests.map((r) => r.role)).size === 1) {
      // Same role repeated is OK for retries; fan-out of one role to many providers is not exposed here.
      return;
    }
    const templates = new Set(requests.map((r) => r.templateId));
    const roles = new Set(requests.map((r) => r.role));
    if (templates.size === 1 && roles.size > 1) {
      throw new Error(
        "Refusing identical template across different roles — use role-specific prompts",
      );
    }
  }
}

let defaultRegistry: ConnectorRegistry | null = null;

export function getConnectorRegistry(): ConnectorRegistry {
  if (!defaultRegistry) {
    defaultRegistry = new ConnectorRegistry();
  }
  return defaultRegistry;
}
