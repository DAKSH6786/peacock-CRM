import { BaseConnector } from "../base";
import { defaultSimulator } from "../simulate";
import type { ConnectorRoleId } from "../types";

export class OpenAIConnector extends BaseConnector {
  readonly provider = "OPENAI" as const;
  readonly defaultModel = "gpt-4.1";
  readonly supportedRoles: readonly ConnectorRoleId[] = [
    "SYNTHESIS",
    "STRATEGY_FRAME",
    "WRITER_BRIEF",
    "VISIBILITY_PROBE",
  ];

  constructor() {
    super(defaultSimulator);
  }
}
