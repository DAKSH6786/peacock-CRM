-- Pipeline stage kanban config
ALTER TABLE "pipeline_stages" ADD COLUMN IF NOT EXISTS "color" TEXT;
ALTER TABLE "pipeline_stages" ADD COLUMN IF NOT EXISTS "requiredFields" TEXT[] DEFAULT ARRAY[]::TEXT[];
ALTER TABLE "pipeline_stages" ADD COLUMN IF NOT EXISTS "staleAfterDays" INTEGER;

-- Lead qualification / scoring inputs
ALTER TABLE "leads" ADD COLUMN IF NOT EXISTS "scoreBreakdown" JSONB;
ALTER TABLE "leads" ADD COLUMN IF NOT EXISTS "companySize" TEXT;
ALTER TABLE "leads" ADD COLUMN IF NOT EXISTS "budgetMinor" INTEGER;
ALTER TABLE "leads" ADD COLUMN IF NOT EXISTS "decisionTimeline" TEXT;
ALTER TABLE "leads" ADD COLUMN IF NOT EXISTS "websiteQuality" INTEGER;
ALTER TABLE "leads" ADD COLUMN IF NOT EXISTS "existingRelationship" BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE "leads" ADD COLUMN IF NOT EXISTS "engagementScore" INTEGER NOT NULL DEFAULT 0;
ALTER TABLE "leads" ADD COLUMN IF NOT EXISTS "normalizedDomain" TEXT;

CREATE INDEX IF NOT EXISTS "leads_organizationId_normalizedPhone_idx" ON "leads"("organizationId", "normalizedPhone");
CREATE INDEX IF NOT EXISTS "leads_organizationId_normalizedCompany_idx" ON "leads"("organizationId", "normalizedCompany");

CREATE TABLE IF NOT EXISTS "lead_scoring_rules" (
    "id" TEXT NOT NULL,
    "organizationId" TEXT NOT NULL,
    "factor" TEXT NOT NULL,
    "label" TEXT NOT NULL,
    "match" JSONB,
    "points" INTEGER NOT NULL,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "sortOrder" INTEGER NOT NULL DEFAULT 0,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "lead_scoring_rules_pkey" PRIMARY KEY ("id")
);

CREATE INDEX IF NOT EXISTS "lead_scoring_rules_organizationId_isActive_idx"
  ON "lead_scoring_rules"("organizationId", "isActive");

DO $$ BEGIN
  ALTER TABLE "lead_scoring_rules" ADD CONSTRAINT "lead_scoring_rules_organizationId_fkey"
    FOREIGN KEY ("organizationId") REFERENCES "organizations"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS "lead_duplicate_candidates" (
    "id" TEXT NOT NULL,
    "organizationId" TEXT NOT NULL,
    "leadId" TEXT NOT NULL,
    "matchLeadId" TEXT NOT NULL,
    "matchType" TEXT NOT NULL,
    "matchValue" TEXT NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'PENDING',
    "reviewedById" TEXT,
    "reviewedAt" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "lead_duplicate_candidates_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX IF NOT EXISTS "lead_duplicate_candidates_leadId_matchLeadId_matchType_key"
  ON "lead_duplicate_candidates"("leadId", "matchLeadId", "matchType");
CREATE INDEX IF NOT EXISTS "lead_duplicate_candidates_organizationId_status_idx"
  ON "lead_duplicate_candidates"("organizationId", "status");

DO $$ BEGIN
  ALTER TABLE "lead_duplicate_candidates" ADD CONSTRAINT "lead_duplicate_candidates_leadId_fkey"
    FOREIGN KEY ("leadId") REFERENCES "leads"("id") ON DELETE CASCADE ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE "lead_duplicate_candidates" ADD CONSTRAINT "lead_duplicate_candidates_matchLeadId_fkey"
    FOREIGN KEY ("matchLeadId") REFERENCES "leads"("id") ON DELETE CASCADE ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
