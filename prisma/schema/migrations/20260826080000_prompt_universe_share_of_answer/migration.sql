-- CreateEnum
CREATE TYPE "PromptType" AS ENUM ('DISCOVERY', 'RECOMMENDATION', 'COMPARISON', 'PROBLEM_SOLVING', 'PURCHASE', 'RESEARCH', 'VALIDATION', 'ALTERNATIVE', 'PRICING', 'TRUST', 'RISK', 'TECHNICAL', 'EDUCATIONAL', 'TRANSACTIONAL');

-- CreateEnum
CREATE TYPE "PromptSourceKind" AS ENUM ('PRODUCT', 'SERVICE', 'KEYWORD', 'SEARCH_CONSOLE_QUERY', 'COMPETITOR_RANKING', 'FORUM', 'SERP', 'PEOPLE_ALSO_ASK', 'CUSTOMER_PERSONA', 'FUNNEL_STAGE', 'LOCATION', 'INDUSTRY_CONCEPT', 'AI_QUERY_PATTERN', 'PROMPT_TAXONOMY', 'MANUAL');

-- CreateEnum
CREATE TYPE "PromptComplexity" AS ENUM ('SIMPLE', 'CONTEXTUAL');

-- CreateEnum
CREATE TYPE "FunnelStage" AS ENUM ('AWARENESS', 'CONSIDERATION', 'DECISION', 'RETENTION', 'ADVOCACY');

-- CreateEnum
CREATE TYPE "ComparisonOutcome" AS ENUM ('WIN', 'LOSE', 'TIE', 'ABSENT', 'MIXED');

-- CreateTable
CREATE TABLE "prompt_universes" (
    "id" TEXT NOT NULL,
    "organizationId" TEXT NOT NULL,
    "propertyId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "brandName" TEXT NOT NULL,
    "industry" TEXT,
    "primaryLocation" TEXT NOT NULL DEFAULT 'global',
    "description" TEXT,
    "generationStatus" TEXT NOT NULL DEFAULT 'draft',
    "promptCount" INTEGER NOT NULL DEFAULT 0,
    "familyCount" INTEGER NOT NULL DEFAULT 0,
    "signalCount" INTEGER NOT NULL DEFAULT 0,
    "notes" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "prompt_universes_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "synthetic_personas" (
    "id" TEXT NOT NULL,
    "universeId" TEXT NOT NULL,
    "code" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "queryStyle" TEXT NOT NULL DEFAULT 'pragmatic',
    "isSystemSeed" BOOLEAN NOT NULL DEFAULT true,
    "contextTemplate" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "synthetic_personas_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "prompt_source_signals" (
    "id" TEXT NOT NULL,
    "universeId" TEXT NOT NULL,
    "sourceKind" "PromptSourceKind" NOT NULL,
    "signalText" TEXT NOT NULL,
    "signalKey" TEXT NOT NULL,
    "weight" DOUBLE PRECISION NOT NULL DEFAULT 1,
    "locationCode" TEXT,
    "productName" TEXT,
    "topicHint" TEXT,
    "externalRef" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "prompt_source_signals_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "prompt_families" (
    "id" TEXT NOT NULL,
    "universeId" TEXT NOT NULL,
    "seedSignalId" TEXT,
    "name" TEXT NOT NULL,
    "slug" TEXT NOT NULL,
    "topic" TEXT NOT NULL,
    "summary" TEXT,
    "memberCount" INTEGER NOT NULL DEFAULT 0,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "prompt_families_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "universe_prompts" (
    "id" TEXT NOT NULL,
    "universeId" TEXT NOT NULL,
    "familyId" TEXT,
    "personaId" TEXT,
    "promptText" TEXT NOT NULL,
    "promptHash" TEXT NOT NULL,
    "topic" TEXT NOT NULL,
    "subtopic" TEXT,
    "intent" TEXT NOT NULL,
    "personaCode" TEXT NOT NULL DEFAULT 'general',
    "funnelStage" "FunnelStage" NOT NULL,
    "location" TEXT NOT NULL DEFAULT 'global',
    "product" TEXT,
    "problem" TEXT,
    "commercialValue" DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    "brandRelevance" DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    "promptType" "PromptType" NOT NULL,
    "sourceKind" "PromptSourceKind" NOT NULL,
    "complexity" "PromptComplexity" NOT NULL DEFAULT 'SIMPLE',
    "isTracked" BOOLEAN NOT NULL DEFAULT false,
    "priority" "Priority" NOT NULL DEFAULT 'MEDIUM',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "universe_prompts_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "share_of_answer_analyses" (
    "id" TEXT NOT NULL,
    "organizationId" TEXT NOT NULL,
    "propertyId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "queryCluster" TEXT NOT NULL,
    "clientBrand" TEXT NOT NULL,
    "analysisStatus" TEXT NOT NULL DEFAULT 'draft',
    "observationCount" INTEGER NOT NULL DEFAULT 0,
    "entityCount" INTEGER NOT NULL DEFAULT 0,
    "methodology" TEXT NOT NULL DEFAULT 'multi_indicator',
    "tokenCountAloneRejected" BOOLEAN NOT NULL DEFAULT true,
    "notes" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "share_of_answer_analyses_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "soa_answer_observations" (
    "id" TEXT NOT NULL,
    "analysisId" TEXT NOT NULL,
    "promptText" TEXT NOT NULL,
    "engineCode" TEXT NOT NULL,
    "modelCode" TEXT,
    "observedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "rawExcerpt" TEXT,
    "structuredSummary" TEXT,
    "answerTokenCount" INTEGER,
    "probeSource" TEXT NOT NULL DEFAULT 'mock',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "soa_answer_observations_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "soa_entity_indicators" (
    "id" TEXT NOT NULL,
    "observationId" TEXT NOT NULL,
    "entityName" TEXT NOT NULL,
    "isClient" BOOLEAN NOT NULL DEFAULT false,
    "mention" BOOLEAN NOT NULL DEFAULT false,
    "mentionCount" INTEGER NOT NULL DEFAULT 0,
    "position" INTEGER,
    "recommendationStrength" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "answerSpace" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "citationOwnership" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "semanticProminence" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "positiveClaims" INTEGER NOT NULL DEFAULT 0,
    "negativeClaims" INTEGER NOT NULL DEFAULT 0,
    "neutralClaims" INTEGER NOT NULL DEFAULT 0,
    "comparisonOutcome" "ComparisonOutcome" NOT NULL DEFAULT 'ABSENT',
    "tokenSpanRatio" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "influenceScore" DOUBLE PRECISION NOT NULL DEFAULT 0,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "soa_entity_indicators_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "soa_brand_scores" (
    "id" TEXT NOT NULL,
    "analysisId" TEXT NOT NULL,
    "entityName" TEXT NOT NULL,
    "isClient" BOOLEAN NOT NULL DEFAULT false,
    "shareOfAnswer" DOUBLE PRECISION NOT NULL,
    "mentionRate" DOUBLE PRECISION NOT NULL,
    "avgPositionScore" DOUBLE PRECISION NOT NULL,
    "avgRecommendationStrength" DOUBLE PRECISION NOT NULL,
    "avgAnswerSpace" DOUBLE PRECISION NOT NULL,
    "avgCitationOwnership" DOUBLE PRECISION NOT NULL,
    "avgSemanticProminence" DOUBLE PRECISION NOT NULL,
    "avgClaimBalance" DOUBLE PRECISION NOT NULL,
    "avgComparisonScore" DOUBLE PRECISION NOT NULL,
    "avgTokenSpanRatio" DOUBLE PRECISION NOT NULL,
    "tokenOnlyShare" DOUBLE PRECISION NOT NULL,
    "tokenVsInfluenceGap" DOUBLE PRECISION NOT NULL,
    "positiveClaimsTotal" INTEGER NOT NULL DEFAULT 0,
    "negativeClaimsTotal" INTEGER NOT NULL DEFAULT 0,
    "neutralClaimsTotal" INTEGER NOT NULL DEFAULT 0,
    "observationSampleSize" INTEGER NOT NULL,
    "meanInfluence" DOUBLE PRECISION NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "soa_brand_scores_pkey" PRIMARY KEY ("id")
);

-- Indexes & FKs
CREATE INDEX "prompt_universes_organizationId_deletedAt_idx" ON "prompt_universes"("organizationId", "deletedAt");
CREATE INDEX "prompt_universes_propertyId_idx" ON "prompt_universes"("propertyId");
CREATE UNIQUE INDEX "synthetic_personas_universeId_code_key" ON "synthetic_personas"("universeId", "code");
CREATE INDEX "synthetic_personas_universeId_idx" ON "synthetic_personas"("universeId");
CREATE INDEX "prompt_source_signals_universeId_sourceKind_idx" ON "prompt_source_signals"("universeId", "sourceKind");
CREATE UNIQUE INDEX "prompt_families_universeId_slug_key" ON "prompt_families"("universeId", "slug");
CREATE INDEX "prompt_families_universeId_topic_idx" ON "prompt_families"("universeId", "topic");
CREATE UNIQUE INDEX "universe_prompts_universeId_promptHash_personaCode_key" ON "universe_prompts"("universeId", "promptHash", "personaCode");
CREATE INDEX "universe_prompts_universeId_promptType_idx" ON "universe_prompts"("universeId", "promptType");
CREATE INDEX "universe_prompts_universeId_complexity_idx" ON "universe_prompts"("universeId", "complexity");
CREATE INDEX "universe_prompts_personaCode_idx" ON "universe_prompts"("personaCode");
CREATE INDEX "share_of_answer_analyses_organizationId_queryCluster_idx" ON "share_of_answer_analyses"("organizationId", "queryCluster");
CREATE INDEX "share_of_answer_analyses_propertyId_idx" ON "share_of_answer_analyses"("propertyId");
CREATE INDEX "soa_answer_observations_analysisId_engineCode_idx" ON "soa_answer_observations"("analysisId", "engineCode");
CREATE UNIQUE INDEX "soa_entity_indicators_observationId_entityName_key" ON "soa_entity_indicators"("observationId", "entityName");
CREATE INDEX "soa_entity_indicators_observationId_idx" ON "soa_entity_indicators"("observationId");
CREATE UNIQUE INDEX "soa_brand_scores_analysisId_entityName_key" ON "soa_brand_scores"("analysisId", "entityName");
CREATE INDEX "soa_brand_scores_analysisId_idx" ON "soa_brand_scores"("analysisId");

ALTER TABLE "prompt_universes" ADD CONSTRAINT "prompt_universes_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "organizations"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
ALTER TABLE "prompt_universes" ADD CONSTRAINT "prompt_universes_propertyId_fkey" FOREIGN KEY ("propertyId") REFERENCES "visibility_properties"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "synthetic_personas" ADD CONSTRAINT "synthetic_personas_universeId_fkey" FOREIGN KEY ("universeId") REFERENCES "prompt_universes"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "prompt_source_signals" ADD CONSTRAINT "prompt_source_signals_universeId_fkey" FOREIGN KEY ("universeId") REFERENCES "prompt_universes"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "prompt_families" ADD CONSTRAINT "prompt_families_universeId_fkey" FOREIGN KEY ("universeId") REFERENCES "prompt_universes"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "prompt_families" ADD CONSTRAINT "prompt_families_seedSignalId_fkey" FOREIGN KEY ("seedSignalId") REFERENCES "prompt_source_signals"("id") ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE "universe_prompts" ADD CONSTRAINT "universe_prompts_universeId_fkey" FOREIGN KEY ("universeId") REFERENCES "prompt_universes"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "universe_prompts" ADD CONSTRAINT "universe_prompts_familyId_fkey" FOREIGN KEY ("familyId") REFERENCES "prompt_families"("id") ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE "universe_prompts" ADD CONSTRAINT "universe_prompts_personaId_fkey" FOREIGN KEY ("personaId") REFERENCES "synthetic_personas"("id") ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE "share_of_answer_analyses" ADD CONSTRAINT "share_of_answer_analyses_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "organizations"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
ALTER TABLE "share_of_answer_analyses" ADD CONSTRAINT "share_of_answer_analyses_propertyId_fkey" FOREIGN KEY ("propertyId") REFERENCES "visibility_properties"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "soa_answer_observations" ADD CONSTRAINT "soa_answer_observations_analysisId_fkey" FOREIGN KEY ("analysisId") REFERENCES "share_of_answer_analyses"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "soa_entity_indicators" ADD CONSTRAINT "soa_entity_indicators_observationId_fkey" FOREIGN KEY ("observationId") REFERENCES "soa_answer_observations"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "soa_brand_scores" ADD CONSTRAINT "soa_brand_scores_analysisId_fkey" FOREIGN KEY ("analysisId") REFERENCES "share_of_answer_analyses"("id") ON DELETE CASCADE ON UPDATE CASCADE;
