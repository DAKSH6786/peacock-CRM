import type { ConnectorResponse } from "@/modules/connectors";
import type { AeoFinding } from "@/modules/aeo/analyze";
import type { CrawlPageArtifact } from "@/modules/crawl/analyze";
import type { GeoFinding } from "@/modules/geo/analyze";
import type { KnowledgeGraph } from "@/modules/knowledge/graph";
import type { TechnicalSeoFinding } from "@/modules/seo/technical";
import type { NinetyDayPlan } from "@/modules/strategy/ninety-day";
import type { VisibilityScorecard } from "@/modules/visibility/score";

export const PIPELINE_STAGES = [
  "OBSERVE",
  "THINK",
  "VERIFY",
  "DECIDE",
  "EXECUTE",
  "MEASURE",
  "LEARN",
] as const;

export type PipelineStageName = (typeof PIPELINE_STAGES)[number];

export type PipelineProperty = {
  id: string;
  organizationId: string;
  name: string;
  brand: string;
  domain: string;
  rootUrl: string;
  competitors?: Array<{ name: string; domain: string }>;
  keywords?: string[];
};

export type ObserveArtifacts = {
  pages: CrawlPageArtifact[];
  technicalSummary: Record<string, number>;
  technicalFindings: TechnicalSeoFinding[];
  aeo: { score: number; findings: AeoFinding[] };
  geo: { score: number; findings: GeoFinding[] };
  research?: ConnectorResponse;
  citations?: ConnectorResponse;
};

export type ThinkArtifacts = {
  structural?: ConnectorResponse;
  contentQuality?: ConnectorResponse;
  entities?: ConnectorResponse;
  knowledgeLinks?: ConnectorResponse;
  synthesis?: ConnectorResponse;
  secondOpinion?: ConnectorResponse;
  costSweep?: ConnectorResponse;
  graph: KnowledgeGraph;
};

export type VerifyArtifacts = {
  deterministicPass: boolean;
  adversarial?: ConnectorResponse;
  consensus?: ConnectorResponse;
  acceptedClaims: string[];
  rejectedClaims: string[];
  consensusScore: number;
  blocked: boolean;
  reasons: string[];
};

export type DecidedRecommendation = {
  kind:
    | "TECHNICAL_SEO"
    | "CONTENT"
    | "AEO"
    | "GEO"
    | "ENTITY"
    | "BACKLINK"
    | "KEYWORD"
    | "WRITER"
    | "STRATEGY"
    | "MONITORING";
  title: string;
  summary: string;
  rationale: string;
  impactScore: number;
  effortScore: number;
  confidence: number;
  evidenceRefs: string[];
  features: Record<string, number>;
};

export type DecideArtifacts = {
  recommendations: DecidedRecommendation[];
  priorities: string[];
};

export type ExecuteArtifacts = {
  writerBriefs: ConnectorResponse[];
  strategy: NinetyDayPlan;
  strategyFrame?: ConnectorResponse;
};

export type MeasureArtifacts = {
  probes: ConnectorResponse[];
  scorecard: VisibilityScorecard;
};

export type LearnArtifacts = {
  weightUpdates: Array<{
    kind: DecidedRecommendation["kind"];
    featureKey: string;
    delta: number;
  }>;
  signals: Array<{ key: string; value: number }>;
};

export type StageResult<T> = {
  stage: PipelineStageName;
  status: "SUCCEEDED" | "FAILED" | "BLOCKED" | "SKIPPED";
  confidence: number;
  output: T;
  traces: ConnectorResponse[];
  errorSummary?: string;
};

export type PipelineRunResult = {
  property: PipelineProperty;
  status: "COMPLETED" | "BLOCKED_ON_VERIFY" | "FAILED";
  stages: Partial<Record<PipelineStageName, StageResult<unknown>>>;
  observe?: ObserveArtifacts;
  think?: ThinkArtifacts;
  verify?: VerifyArtifacts;
  decide?: DecideArtifacts;
  execute?: ExecuteArtifacts;
  measure?: MeasureArtifacts;
  learn?: LearnArtifacts;
  summary: string;
  confidence: number;
};

export type RecommendationWeights = Record<string, number>;
