export type HealthResponse = {
  status: string;
  app: string;
  env: string;
  database: string;
  redis: string;
  job_backend: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
  organisation_id: string;
  workspace_id?: string | null;
};

/** Coarse product loop stages */
export type CognitiveStage =
  | "OBSERVE"
  | "THINK"
  | "VERIFY"
  | "DECIDE"
  | "EXECUTE"
  | "MEASURE"
  | "LEARN";

/** Fine-grained strategic decomposition layers */
export type StrategicLayer =
  | "L0_REQUEST_CLASSIFICATION"
  | "L1_CONTEXT_ASSEMBLY"
  | "L2_DETERMINISTIC_EVIDENCE"
  | "L3_RESEARCH"
  | "L4_SPECIALIST_REASONING"
  | "L5_ADVERSARIAL_ANALYSIS"
  | "L6_VERIFICATION"
  | "L7_DECISION"
  | "L8_SIMULATION"
  | "L9_EXECUTION_PLAN"
  | "L10_LEARNING";

export const STRATEGIC_LAYERS: StrategicLayer[] = [
  "L0_REQUEST_CLASSIFICATION",
  "L1_CONTEXT_ASSEMBLY",
  "L2_DETERMINISTIC_EVIDENCE",
  "L3_RESEARCH",
  "L4_SPECIALIST_REASONING",
  "L5_ADVERSARIAL_ANALYSIS",
  "L6_VERIFICATION",
  "L7_DECISION",
  "L8_SIMULATION",
  "L9_EXECUTION_PLAN",
  "L10_LEARNING",
];
