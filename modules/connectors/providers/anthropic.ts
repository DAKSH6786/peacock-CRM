import { BaseConnector } from "../base";
import { defaultSimulator } from "../simulate";
import type { ConnectorRoleId } from "../types";

export class AnthropicConnector extends BaseConnector {
  readonly provider = "ANTHROPIC" as const;
  readonly defaultModel = "claude-sonnet-4";
  readonly supportedRoles: readonly ConnectorRoleId[] = [
    "STRUCTURAL_CRITIQUE",
    "CONTENT_QUALITY",
    "VERIFY_ADVERSARIAL",
    "VISIBILITY_PROBE",
  ];

  constructor() {
    super(defaultSimulator);
  }
}
