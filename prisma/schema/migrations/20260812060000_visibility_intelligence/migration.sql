-- CreateEnum
CREATE TYPE "IntelligenceRunStatus" AS ENUM ('PENDING', 'OBSERVING', 'THINKING', 'VERIFYING', 'DECIDING', 'EXECUTING', 'MEASURING', 'LEARNING', 'COMPLETED', 'FAILED', 'CANCELLED', 'BLOCKED_ON_VERIFY');

-- CreateEnum
CREATE TYPE "IntelligenceStageName" AS ENUM ('OBSERVE', 'THINK', 'VERIFY', 'DECIDE', 'EXECUTE', 'MEASURE', 'LEARN');

-- CreateEnum
CREATE TYPE "IntelligenceStageStatus" AS ENUM ('PENDING', 'RUNNING', 'SUCCEEDED', 'FAILED', 'SKIPPED', 'BLOCKED');

-- CreateEnum
CREATE TYPE "ConnectorProvider" AS ENUM ('OPENAI', 'GEMINI', 'ANTHROPIC', 'PERPLEXITY', 'DEEPSEEK');

-- CreateEnum
CREATE TYPE "ConnectorRole" AS ENUM ('WEB_RESEARCH', 'CITATION_HUNT', 'STRUCTURAL_CRITIQUE', 'CONTENT_QUALITY', 'VERIFY_ADVERSARIAL', 'SYNTHESIS', 'STRATEGY_FRAME', 'WRITER_BRIEF', 'ENTITY_EXTRACTION', 'MULTIMODAL_PAGE', 'KNOWLEDGE_LINK', 'SECOND_OPINION', 'COST_SWEEP', 'VERIFY_CONSENSUS', 'VISIBILITY_PROBE');

-- CreateEnum
CREATE TYPE "VisibilitySurface" AS ENUM ('CHATGPT', 'GEMINI', 'CLAUDE', 'PERPLEXITY', 'DEEPSEEK', 'GOOGLE_AI_OVERVIEW', 'OTHER');

-- CreateEnum
CREATE TYPE "RecommendationKind" AS ENUM ('TECHNICAL_SEO', 'CONTENT', 'AEO', 'GEO', 'ENTITY', 'BACKLINK', 'KEYWORD', 'WRITER', 'STRATEGY', 'MONITORING');

-- CreateEnum
CREATE TYPE "RecommendationStatus" AS ENUM ('PROPOSED', 'APPROVED', 'IN_PROGRESS', 'DONE', 'DISMISSED', 'SUPERSEDED');

-- CreateTable
CREATE TABLE "visibility_properties" (
    "id" TEXT NOT NULL,
    "organizationId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "primaryDomain" TEXT NOT NULL,
    "rootUrl" TEXT NOT NULL,
    "industry" TEXT,
    "locale" TEXT NOT NULL DEFAULT 'en-US',
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "metadata" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "visibility_properties_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "visibility_competitors" (
    "id" TEXT NOT NULL,
    "propertyId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "domain" TEXT NOT NULL,
    "rootUrl" TEXT,
    "notes" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "visibility_competitors_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "crawl_jobs" (
    "id" TEXT NOT NULL,
    "propertyId" TEXT NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'PENDING',
    "startedAt" TIMESTAMP(3),
    "completedAt" TIMESTAMP(3),
    "pageCount" INTEGER NOT NULL DEFAULT 0,
    "errorSummary" TEXT,
    "config" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "crawl_jobs_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "crawled_pages" (
    "id" TEXT NOT NULL,
    "crawlJobId" TEXT NOT NULL,
    "url" TEXT NOT NULL,
    "statusCode" INTEGER,
    "title" TEXT,
    "metaDescription" TEXT,
    "canonical" TEXT,
    "wordCount" INTEGER NOT NULL DEFAULT 0,
    "headings" JSONB,
    "schemaTypes" JSONB,
    "technicalFlags" JSONB,
    "contentHash" TEXT,
    "fetchedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "crawled_pages_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "intelligence_runs" (
    "id" TEXT NOT NULL,
    "organizationId" TEXT NOT NULL,
    "propertyId" TEXT NOT NULL,
    "status" "IntelligenceRunStatus" NOT NULL DEFAULT 'PENDING',
    "trigger" TEXT NOT NULL DEFAULT 'manual',
    "objective" TEXT,
    "config" JSONB,
    "currentStage" "IntelligenceStageName",
    "confidence" DOUBLE PRECISION,
    "summary" TEXT,
    "errorSummary" TEXT,
    "startedAt" TIMESTAMP(3),
    "completedAt" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "intelligence_runs_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "intelligence_stage_results" (
    "id" TEXT NOT NULL,
    "runId" TEXT NOT NULL,
    "stage" "IntelligenceStageName" NOT NULL,
    "status" "IntelligenceStageStatus" NOT NULL DEFAULT 'PENDING',
    "output" JSONB,
    "artifactRefs" JSONB,
    "confidence" DOUBLE PRECISION,
    "errorSummary" TEXT,
    "startedAt" TIMESTAMP(3),
    "completedAt" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "intelligence_stage_results_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "connector_traces" (
    "id" TEXT NOT NULL,
    "runId" TEXT NOT NULL,
    "stage" "IntelligenceStageName" NOT NULL,
    "provider" "ConnectorProvider" NOT NULL,
    "role" "ConnectorRole" NOT NULL,
    "promptHash" TEXT NOT NULL,
    "model" TEXT,
    "latencyMs" INTEGER,
    "tokenIn" INTEGER,
    "tokenOut" INTEGER,
    "success" BOOLEAN NOT NULL DEFAULT true,
    "errorSummary" TEXT,
    "responseMeta" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "connector_traces_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "keyword_targets" (
    "id" TEXT NOT NULL,
    "propertyId" TEXT NOT NULL,
    "phrase" TEXT NOT NULL,
    "locale" TEXT NOT NULL DEFAULT 'en-US',
    "intent" TEXT,
    "volume" INTEGER,
    "difficulty" DOUBLE PRECISION,
    "priority" "Priority" NOT NULL DEFAULT 'MEDIUM',
    "metadata" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "keyword_targets_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "knowledge_entities" (
    "id" TEXT NOT NULL,
    "propertyId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "entityType" TEXT NOT NULL,
    "description" TEXT,
    "sameAs" JSONB,
    "attributes" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "knowledge_entities_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "knowledge_edges" (
    "id" TEXT NOT NULL,
    "fromId" TEXT NOT NULL,
    "toId" TEXT NOT NULL,
    "relation" TEXT NOT NULL,
    "weight" DOUBLE PRECISION NOT NULL DEFAULT 1,
    "evidence" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "knowledge_edges_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ai_visibility_samples" (
    "id" TEXT NOT NULL,
    "propertyId" TEXT NOT NULL,
    "surface" "VisibilitySurface" NOT NULL,
    "prompt" TEXT NOT NULL,
    "promptHash" TEXT NOT NULL,
    "mentionedBrand" BOOLEAN NOT NULL DEFAULT false,
    "citedUrl" BOOLEAN NOT NULL DEFAULT false,
    "sentiment" DOUBLE PRECISION,
    "rawExcerpt" TEXT,
    "competitorHits" JSONB,
    "sampledAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "ai_visibility_samples_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "backlink_snapshots" (
    "id" TEXT NOT NULL,
    "propertyId" TEXT NOT NULL,
    "capturedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "referringDomains" INTEGER NOT NULL DEFAULT 0,
    "backlinks" INTEGER NOT NULL DEFAULT 0,
    "sampleLinks" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "backlink_snapshots_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "recommendations" (
    "id" TEXT NOT NULL,
    "organizationId" TEXT NOT NULL,
    "propertyId" TEXT NOT NULL,
    "runId" TEXT,
    "kind" "RecommendationKind" NOT NULL,
    "title" TEXT NOT NULL,
    "summary" TEXT NOT NULL,
    "rationale" TEXT,
    "impactScore" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "effortScore" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "confidence" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "priority" "Priority" NOT NULL DEFAULT 'MEDIUM',
    "status" "RecommendationStatus" NOT NULL DEFAULT 'PROPOSED',
    "payload" JSONB,
    "evidenceRefs" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "recommendations_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "strategy_plans" (
    "id" TEXT NOT NULL,
    "organizationId" TEXT NOT NULL,
    "propertyId" TEXT NOT NULL,
    "runId" TEXT,
    "title" TEXT NOT NULL,
    "horizonDays" INTEGER NOT NULL DEFAULT 90,
    "summary" TEXT,
    "weeks" JSONB,
    "status" TEXT NOT NULL DEFAULT 'DRAFT',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "strategy_plans_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "outcome_events" (
    "id" TEXT NOT NULL,
    "recommendationId" TEXT NOT NULL,
    "metricKey" TEXT NOT NULL,
    "metricValue" DOUBLE PRECISION NOT NULL,
    "notes" TEXT,
    "observedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "outcome_events_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "recommendation_weights" (
    "id" TEXT NOT NULL,
    "organizationId" TEXT NOT NULL,
    "kind" "RecommendationKind" NOT NULL,
    "featureKey" TEXT NOT NULL,
    "weight" DOUBLE PRECISION NOT NULL DEFAULT 1,
    "sampleSize" INTEGER NOT NULL DEFAULT 0,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "recommendation_weights_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "learning_signals" (
    "id" TEXT NOT NULL,
    "runId" TEXT NOT NULL,
    "signalKey" TEXT NOT NULL,
    "value" DOUBLE PRECISION NOT NULL,
    "meta" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "learning_signals_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "visibility_properties_organizationId_deletedAt_idx" ON "visibility_properties"("organizationId", "deletedAt");

-- CreateIndex
CREATE UNIQUE INDEX "visibility_properties_organizationId_primaryDomain_key" ON "visibility_properties"("organizationId", "primaryDomain");

-- CreateIndex
CREATE INDEX "visibility_competitors_propertyId_deletedAt_idx" ON "visibility_competitors"("propertyId", "deletedAt");

-- CreateIndex
CREATE UNIQUE INDEX "visibility_competitors_propertyId_domain_key" ON "visibility_competitors"("propertyId", "domain");

-- CreateIndex
CREATE INDEX "crawl_jobs_propertyId_createdAt_idx" ON "crawl_jobs"("propertyId", "createdAt");

-- CreateIndex
CREATE INDEX "crawled_pages_crawlJobId_idx" ON "crawled_pages"("crawlJobId");

-- CreateIndex
CREATE UNIQUE INDEX "crawled_pages_crawlJobId_url_key" ON "crawled_pages"("crawlJobId", "url");

-- CreateIndex
CREATE INDEX "intelligence_runs_organizationId_createdAt_idx" ON "intelligence_runs"("organizationId", "createdAt");

-- CreateIndex
CREATE INDEX "intelligence_runs_propertyId_status_idx" ON "intelligence_runs"("propertyId", "status");

-- CreateIndex
CREATE INDEX "intelligence_stage_results_runId_status_idx" ON "intelligence_stage_results"("runId", "status");

-- CreateIndex
CREATE UNIQUE INDEX "intelligence_stage_results_runId_stage_key" ON "intelligence_stage_results"("runId", "stage");

-- CreateIndex
CREATE INDEX "connector_traces_runId_stage_idx" ON "connector_traces"("runId", "stage");

-- CreateIndex
CREATE INDEX "connector_traces_provider_role_idx" ON "connector_traces"("provider", "role");

-- CreateIndex
CREATE INDEX "keyword_targets_propertyId_deletedAt_idx" ON "keyword_targets"("propertyId", "deletedAt");

-- CreateIndex
CREATE UNIQUE INDEX "keyword_targets_propertyId_phrase_locale_key" ON "keyword_targets"("propertyId", "phrase", "locale");

-- CreateIndex
CREATE INDEX "knowledge_entities_propertyId_entityType_idx" ON "knowledge_entities"("propertyId", "entityType");

-- CreateIndex
CREATE UNIQUE INDEX "knowledge_entities_propertyId_name_entityType_key" ON "knowledge_entities"("propertyId", "name", "entityType");

-- CreateIndex
CREATE INDEX "knowledge_edges_toId_idx" ON "knowledge_edges"("toId");

-- CreateIndex
CREATE UNIQUE INDEX "knowledge_edges_fromId_toId_relation_key" ON "knowledge_edges"("fromId", "toId", "relation");

-- CreateIndex
CREATE INDEX "ai_visibility_samples_propertyId_surface_sampledAt_idx" ON "ai_visibility_samples"("propertyId", "surface", "sampledAt");

-- CreateIndex
CREATE INDEX "backlink_snapshots_propertyId_capturedAt_idx" ON "backlink_snapshots"("propertyId", "capturedAt");

-- CreateIndex
CREATE INDEX "recommendations_organizationId_status_idx" ON "recommendations"("organizationId", "status");

-- CreateIndex
CREATE INDEX "recommendations_propertyId_kind_idx" ON "recommendations"("propertyId", "kind");

-- CreateIndex
CREATE INDEX "recommendations_runId_idx" ON "recommendations"("runId");

-- CreateIndex
CREATE INDEX "strategy_plans_organizationId_propertyId_idx" ON "strategy_plans"("organizationId", "propertyId");

-- CreateIndex
CREATE INDEX "outcome_events_recommendationId_observedAt_idx" ON "outcome_events"("recommendationId", "observedAt");

-- CreateIndex
CREATE UNIQUE INDEX "recommendation_weights_organizationId_kind_featureKey_key" ON "recommendation_weights"("organizationId", "kind", "featureKey");

-- CreateIndex
CREATE INDEX "learning_signals_runId_signalKey_idx" ON "learning_signals"("runId", "signalKey");

-- AddForeignKey
ALTER TABLE "visibility_properties" ADD CONSTRAINT "visibility_properties_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "organizations"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "visibility_competitors" ADD CONSTRAINT "visibility_competitors_propertyId_fkey" FOREIGN KEY ("propertyId") REFERENCES "visibility_properties"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "crawl_jobs" ADD CONSTRAINT "crawl_jobs_propertyId_fkey" FOREIGN KEY ("propertyId") REFERENCES "visibility_properties"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "crawled_pages" ADD CONSTRAINT "crawled_pages_crawlJobId_fkey" FOREIGN KEY ("crawlJobId") REFERENCES "crawl_jobs"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "intelligence_runs" ADD CONSTRAINT "intelligence_runs_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "organizations"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "intelligence_runs" ADD CONSTRAINT "intelligence_runs_propertyId_fkey" FOREIGN KEY ("propertyId") REFERENCES "visibility_properties"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "intelligence_stage_results" ADD CONSTRAINT "intelligence_stage_results_runId_fkey" FOREIGN KEY ("runId") REFERENCES "intelligence_runs"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "connector_traces" ADD CONSTRAINT "connector_traces_runId_fkey" FOREIGN KEY ("runId") REFERENCES "intelligence_runs"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "keyword_targets" ADD CONSTRAINT "keyword_targets_propertyId_fkey" FOREIGN KEY ("propertyId") REFERENCES "visibility_properties"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "knowledge_entities" ADD CONSTRAINT "knowledge_entities_propertyId_fkey" FOREIGN KEY ("propertyId") REFERENCES "visibility_properties"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "knowledge_edges" ADD CONSTRAINT "knowledge_edges_fromId_fkey" FOREIGN KEY ("fromId") REFERENCES "knowledge_entities"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "knowledge_edges" ADD CONSTRAINT "knowledge_edges_toId_fkey" FOREIGN KEY ("toId") REFERENCES "knowledge_entities"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ai_visibility_samples" ADD CONSTRAINT "ai_visibility_samples_propertyId_fkey" FOREIGN KEY ("propertyId") REFERENCES "visibility_properties"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "backlink_snapshots" ADD CONSTRAINT "backlink_snapshots_propertyId_fkey" FOREIGN KEY ("propertyId") REFERENCES "visibility_properties"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "recommendations" ADD CONSTRAINT "recommendations_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "organizations"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "recommendations" ADD CONSTRAINT "recommendations_propertyId_fkey" FOREIGN KEY ("propertyId") REFERENCES "visibility_properties"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "recommendations" ADD CONSTRAINT "recommendations_runId_fkey" FOREIGN KEY ("runId") REFERENCES "intelligence_runs"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "strategy_plans" ADD CONSTRAINT "strategy_plans_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "organizations"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "strategy_plans" ADD CONSTRAINT "strategy_plans_propertyId_fkey" FOREIGN KEY ("propertyId") REFERENCES "visibility_properties"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "strategy_plans" ADD CONSTRAINT "strategy_plans_runId_fkey" FOREIGN KEY ("runId") REFERENCES "intelligence_runs"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "outcome_events" ADD CONSTRAINT "outcome_events_recommendationId_fkey" FOREIGN KEY ("recommendationId") REFERENCES "recommendations"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "recommendation_weights" ADD CONSTRAINT "recommendation_weights_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "organizations"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "learning_signals" ADD CONSTRAINT "learning_signals_runId_fkey" FOREIGN KEY ("runId") REFERENCES "intelligence_runs"("id") ON DELETE CASCADE ON UPDATE CASCADE;
