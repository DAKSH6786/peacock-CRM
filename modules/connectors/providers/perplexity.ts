import { BaseConnector } from "../base";
import { defaultSimulator } from "../simulate";
import type { ConnectorRoleId } from "../types";

export class PerplexityConnector extends BaseConnector {
  readonly provider = "PERPLEXITY" as const;
  readonly defaultModel = "sonar-pro";
  readonly supportedRoles: readonly ConnectorRoleId[] = [
    "WEB_RESEARCH",
    "CITATION_HUNT",
    "VISIBILITY_PROBE",
  ];

  constructor() {
    super(defaultSimulator);
  }
}
