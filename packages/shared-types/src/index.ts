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

export type CognitiveStage =
  | "OBSERVE"
  | "THINK"
  | "VERIFY"
  | "DECIDE"
  | "EXECUTE"
  | "MEASURE"
  | "LEARN";
