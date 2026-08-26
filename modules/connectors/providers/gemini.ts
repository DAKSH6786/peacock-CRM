import { BaseConnector } from "../base";
import { defaultSimulator } from "../simulate";
import type { ConnectorRoleId } from "../types";

export class GeminiConnector extends BaseConnector {
  readonly provider = "GEMINI" as const;
  readonly defaultModel = "gemini-2.5-pro";
  readonly supportedRoles: readonly ConnectorRoleId[] = [
    "ENTITY_EXTRACTION",
    "MULTIMODAL_PAGE",
    "KNOWLEDGE_LINK",
    "VISIBILITY_PROBE",
  ];

  constructor() {
    super(defaultSimulator);
  }
}
