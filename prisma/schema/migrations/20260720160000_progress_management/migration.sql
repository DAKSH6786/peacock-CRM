-- Extend MetricType / HealthStatus enums
DO $$ BEGIN
  ALTER TYPE "MetricType" ADD VALUE IF NOT EXISTS 'MILESTONE';
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  ALTER TYPE "MetricType" ADD VALUE IF NOT EXISTS 'CUSTOM';
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  ALTER TYPE "HealthStatus" ADD VALUE IF NOT EXISTS 'GREY';
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Objectives enhancements
ALTER TABLE "objectives" ADD COLUMN IF NOT EXISTS "parentId" TEXT;
ALTER TABLE "objectives" ADD COLUMN IF NOT EXISTS "primaryOwnerId" TEXT;
ALTER TABLE "objectives" ADD COLUMN IF NOT EXISTS "financialYearId" TEXT;
ALTER TABLE "objectives" ADD COLUMN IF NOT EXISTS "quarter" TEXT;
ALTER TABLE "objectives" ADD COLUMN IF NOT EXISTS "priority" "Priority" NOT NULL DEFAULT 'MEDIUM';
ALTER TABLE "objectives" ADD COLUMN IF NOT EXISTS "health" "HealthStatus" NOT NULL DEFAULT 'GREY';
ALTER TABLE "objectives" ADD COLUMN IF NOT EXISTS "healthOverridden" BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE "objectives" ADD COLUMN IF NOT EXISTS "healthOverrideReason" TEXT;
ALTER TABLE "objectives" ADD COLUMN IF NOT EXISTS "visibility" TEXT NOT NULL DEFAULT 'ORGANIZATION';
ALTER TABLE "objectives" ADD COLUMN IF NOT EXISTS "tags" TEXT[] DEFAULT ARRAY[]::TEXT[];

CREATE INDEX IF NOT EXISTS "objectives_organizationId_parentId_idx" ON "objectives"("organizationId", "parentId");
CREATE INDEX IF NOT EXISTS "objectives_organizationId_health_idx" ON "objectives"("organizationId", "health");

DO $$ BEGIN
  ALTER TABLE "objectives" ADD CONSTRAINT "objectives_parentId_fkey"
    FOREIGN KEY ("parentId") REFERENCES "objectives"("id") ON DELETE SET NULL ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE "objectives" ADD CONSTRAINT "objectives_primaryOwnerId_fkey"
    FOREIGN KEY ("primaryOwnerId") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE "objectives" ADD CONSTRAINT "objectives_financialYearId_fkey"
    FOREIGN KEY ("financialYearId") REFERENCES "financial_years"("id") ON DELETE SET NULL ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Key results enhancements
ALTER TABLE "key_results" ADD COLUMN IF NOT EXISTS "ownerUserId" TEXT;
ALTER TABLE "key_results" ADD COLUMN IF NOT EXISTS "updateFrequency" TEXT NOT NULL DEFAULT 'WEEKLY';
ALTER TABLE "key_results" ADD COLUMN IF NOT EXISTS "confidenceScore" INTEGER;
ALTER TABLE "key_results" ADD COLUMN IF NOT EXISTS "dueDate" DATE;
ALTER TABLE "key_results" ADD COLUMN IF NOT EXISTS "evidence" TEXT;

DO $$ BEGIN
  ALTER TABLE "key_results" ADD CONSTRAINT "key_results_ownerUserId_fkey"
    FOREIGN KEY ("ownerUserId") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

ALTER TABLE "objective_owners" ADD COLUMN IF NOT EXISTS "role" TEXT NOT NULL DEFAULT 'OWNER';

-- KPI department binding
ALTER TABLE "kpis" ADD COLUMN IF NOT EXISTS "departmentId" TEXT;
ALTER TABLE "kpis" ADD COLUMN IF NOT EXISTS "category" TEXT;
ALTER TABLE "kpis" ADD COLUMN IF NOT EXISTS "isActive" BOOLEAN NOT NULL DEFAULT true;
CREATE INDEX IF NOT EXISTS "kpis_organizationId_departmentId_idx" ON "kpis"("organizationId", "departmentId");
DO $$ BEGIN
  ALTER TABLE "kpis" ADD CONSTRAINT "kpis_departmentId_fkey"
    FOREIGN KEY ("departmentId") REFERENCES "departments"("id") ON DELETE SET NULL ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Business review enhancements
ALTER TABLE "business_reviews" ADD COLUMN IF NOT EXISTS "reviewType" TEXT NOT NULL DEFAULT 'MONTHLY';
ALTER TABLE "business_reviews" ADD COLUMN IF NOT EXISTS "majorWins" TEXT;
ALTER TABLE "business_reviews" ADD COLUMN IF NOT EXISTS "missedTargets" TEXT;
ALTER TABLE "business_reviews" ADD COLUMN IF NOT EXISTS "snapshot" JSONB;
ALTER TABLE "business_reviews" ADD COLUMN IF NOT EXISTS "createdById" TEXT;
CREATE INDEX IF NOT EXISTS "business_reviews_organizationId_reviewType_idx" ON "business_reviews"("organizationId", "reviewType");
DO $$ BEGIN
  ALTER TABLE "business_reviews" ADD CONSTRAINT "business_reviews_createdById_fkey"
    FOREIGN KEY ("createdById") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS "key_result_updates" (
    "id" TEXT NOT NULL,
    "organizationId" TEXT NOT NULL,
    "keyResultId" TEXT NOT NULL,
    "previousValue" DECIMAL(18,4),
    "newValue" DECIMAL(18,4) NOT NULL,
    "previousProgressPct" INTEGER,
    "progressPct" INTEGER,
    "confidenceScore" INTEGER,
    "note" TEXT,
    "evidence" TEXT,
    "createdById" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "key_result_updates_pkey" PRIMARY KEY ("id")
);
CREATE INDEX IF NOT EXISTS "key_result_updates_keyResultId_createdAt_idx" ON "key_result_updates"("keyResultId", "createdAt");
CREATE INDEX IF NOT EXISTS "key_result_updates_organizationId_idx" ON "key_result_updates"("organizationId");
DO $$ BEGIN
  ALTER TABLE "key_result_updates" ADD CONSTRAINT "key_result_updates_keyResultId_fkey"
    FOREIGN KEY ("keyResultId") REFERENCES "key_results"("id") ON DELETE CASCADE ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE "key_result_updates" ADD CONSTRAINT "key_result_updates_createdById_fkey"
    FOREIGN KEY ("createdById") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS "key_result_comments" (
    "id" TEXT NOT NULL,
    "organizationId" TEXT NOT NULL,
    "keyResultId" TEXT NOT NULL,
    "body" TEXT NOT NULL,
    "createdById" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),
    CONSTRAINT "key_result_comments_pkey" PRIMARY KEY ("id")
);
CREATE INDEX IF NOT EXISTS "key_result_comments_keyResultId_createdAt_idx" ON "key_result_comments"("keyResultId", "createdAt");
DO $$ BEGIN
  ALTER TABLE "key_result_comments" ADD CONSTRAINT "key_result_comments_keyResultId_fkey"
    FOREIGN KEY ("keyResultId") REFERENCES "key_results"("id") ON DELETE CASCADE ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE "key_result_comments" ADD CONSTRAINT "key_result_comments_createdById_fkey"
    FOREIGN KEY ("createdById") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS "progress_updates" (
    "id" TEXT NOT NULL,
    "organizationId" TEXT NOT NULL,
    "objectiveId" TEXT,
    "cadence" TEXT NOT NULL DEFAULT 'WEEKLY',
    "periodStart" DATE NOT NULL,
    "periodEnd" DATE NOT NULL,
    "body" TEXT NOT NULL,
    "progressPct" INTEGER,
    "confidenceScore" INTEGER,
    "health" "HealthStatus",
    "riskFlag" BOOLEAN NOT NULL DEFAULT false,
    "blocker" TEXT,
    "evidence" TEXT,
    "reviewStatus" TEXT NOT NULL DEFAULT 'SUBMITTED',
    "reviewedById" TEXT,
    "reviewedAt" TIMESTAMP(3),
    "reviewNote" TEXT,
    "createdById" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    CONSTRAINT "progress_updates_pkey" PRIMARY KEY ("id")
);
CREATE INDEX IF NOT EXISTS "progress_updates_organizationId_cadence_periodStart_idx"
  ON "progress_updates"("organizationId", "cadence", "periodStart");
CREATE INDEX IF NOT EXISTS "progress_updates_objectiveId_createdAt_idx"
  ON "progress_updates"("objectiveId", "createdAt");
DO $$ BEGIN
  ALTER TABLE "progress_updates" ADD CONSTRAINT "progress_updates_objectiveId_fkey"
    FOREIGN KEY ("objectiveId") REFERENCES "objectives"("id") ON DELETE CASCADE ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE "progress_updates" ADD CONSTRAINT "progress_updates_createdById_fkey"
    FOREIGN KEY ("createdById") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE "progress_updates" ADD CONSTRAINT "progress_updates_reviewedById_fkey"
    FOREIGN KEY ("reviewedById") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS "business_review_items" (
    "id" TEXT NOT NULL,
    "organizationId" TEXT NOT NULL,
    "reviewId" TEXT NOT NULL,
    "itemType" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "body" TEXT,
    "ownerUserId" TEXT,
    "dueDate" DATE,
    "status" TEXT NOT NULL DEFAULT 'OPEN',
    "sortOrder" INTEGER NOT NULL DEFAULT 0,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    CONSTRAINT "business_review_items_pkey" PRIMARY KEY ("id")
);
CREATE INDEX IF NOT EXISTS "business_review_items_reviewId_itemType_idx" ON "business_review_items"("reviewId", "itemType");
DO $$ BEGIN
  ALTER TABLE "business_review_items" ADD CONSTRAINT "business_review_items_reviewId_fkey"
    FOREIGN KEY ("reviewId") REFERENCES "business_reviews"("id") ON DELETE CASCADE ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE "business_review_items" ADD CONSTRAINT "business_review_items_ownerUserId_fkey"
    FOREIGN KEY ("ownerUserId") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS "department_scorecards" (
    "id" TEXT NOT NULL,
    "organizationId" TEXT NOT NULL,
    "departmentId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),
    CONSTRAINT "department_scorecards_pkey" PRIMARY KEY ("id")
);
CREATE UNIQUE INDEX IF NOT EXISTS "department_scorecards_organizationId_departmentId_name_key"
  ON "department_scorecards"("organizationId", "departmentId", "name");
CREATE INDEX IF NOT EXISTS "department_scorecards_organizationId_departmentId_idx"
  ON "department_scorecards"("organizationId", "departmentId");
DO $$ BEGIN
  ALTER TABLE "department_scorecards" ADD CONSTRAINT "department_scorecards_organizationId_fkey"
    FOREIGN KEY ("organizationId") REFERENCES "organizations"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE "department_scorecards" ADD CONSTRAINT "department_scorecards_departmentId_fkey"
    FOREIGN KEY ("departmentId") REFERENCES "departments"("id") ON DELETE CASCADE ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS "scorecard_kpis" (
    "id" TEXT NOT NULL,
    "scorecardId" TEXT NOT NULL,
    "kpiId" TEXT NOT NULL,
    "sortOrder" INTEGER NOT NULL DEFAULT 0,
    "targetValue" DECIMAL(18,4),
    CONSTRAINT "scorecard_kpis_pkey" PRIMARY KEY ("id")
);
CREATE UNIQUE INDEX IF NOT EXISTS "scorecard_kpis_scorecardId_kpiId_key" ON "scorecard_kpis"("scorecardId", "kpiId");
DO $$ BEGIN
  ALTER TABLE "scorecard_kpis" ADD CONSTRAINT "scorecard_kpis_scorecardId_fkey"
    FOREIGN KEY ("scorecardId") REFERENCES "department_scorecards"("id") ON DELETE CASCADE ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE "scorecard_kpis" ADD CONSTRAINT "scorecard_kpis_kpiId_fkey"
    FOREIGN KEY ("kpiId") REFERENCES "kpis"("id") ON DELETE CASCADE ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS "progress_health_rules" (
    "id" TEXT NOT NULL,
    "organizationId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "health" "HealthStatus" NOT NULL,
    "match" JSONB NOT NULL,
    "sortOrder" INTEGER NOT NULL DEFAULT 0,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    CONSTRAINT "progress_health_rules_pkey" PRIMARY KEY ("id")
);
CREATE INDEX IF NOT EXISTS "progress_health_rules_organizationId_isActive_idx"
  ON "progress_health_rules"("organizationId", "isActive");
DO $$ BEGIN
  ALTER TABLE "progress_health_rules" ADD CONSTRAINT "progress_health_rules_organizationId_fkey"
    FOREIGN KEY ("organizationId") REFERENCES "organizations"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
