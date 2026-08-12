import { BaseConnector } from "../base";
import { defaultSimulator } from "../simulate";
import type { ConnectorRoleId } from "../types";

export class DeepSeekConnector extends BaseConnector {
  readonly provider = "DEEPSEEK" as const;
  readonly defaultModel = "deepseek-chat";
  readonly supportedRoles: readonly ConnectorRoleId[] = [
    "SECOND_OPINION",
    "COST_SWEEP",
    "VERIFY_CONSENSUS",
    "VISIBILITY_PROBE",
  ];

  constructor() {
    super(defaultSimulator);
  }
}
