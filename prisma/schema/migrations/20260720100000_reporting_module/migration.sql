-- AlterTable
ALTER TABLE "organization_settings" ADD COLUMN IF NOT EXISTS "salesPerformanceVisibility" JSONB;

-- CreateTable
CREATE TABLE IF NOT EXISTS "saved_reports" (
    "id" TEXT NOT NULL,
    "organizationId" TEXT NOT NULL,
    "ownerUserId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "source" TEXT NOT NULL DEFAULT 'builder',
    "reportKey" TEXT,
    "definition" JSONB NOT NULL,
    "chartType" TEXT,
    "currencyCode" CHAR(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "saved_reports_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE IF NOT EXISTS "report_shares" (
    "id" TEXT NOT NULL,
    "organizationId" TEXT NOT NULL,
    "savedReportId" TEXT NOT NULL,
    "roleCode" TEXT NOT NULL,
    "canExport" BOOLEAN NOT NULL DEFAULT false,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "report_shares_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE IF NOT EXISTS "report_schedules" (
    "id" TEXT NOT NULL,
    "organizationId" TEXT NOT NULL,
    "savedReportId" TEXT NOT NULL,
    "cadence" TEXT NOT NULL,
    "format" TEXT NOT NULL DEFAULT 'csv',
    "nextRunAt" TIMESTAMP(3),
    "lastRunAt" TIMESTAMP(3),
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "createdById" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "report_schedules_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX IF NOT EXISTS "saved_reports_organizationId_ownerUserId_idx" ON "saved_reports"("organizationId", "ownerUserId");
CREATE INDEX IF NOT EXISTS "saved_reports_organizationId_reportKey_idx" ON "saved_reports"("organizationId", "reportKey");
CREATE INDEX IF NOT EXISTS "saved_reports_deletedAt_idx" ON "saved_reports"("deletedAt");
CREATE INDEX IF NOT EXISTS "report_shares_organizationId_roleCode_idx" ON "report_shares"("organizationId", "roleCode");
CREATE UNIQUE INDEX IF NOT EXISTS "report_shares_savedReportId_roleCode_key" ON "report_shares"("savedReportId", "roleCode");
CREATE INDEX IF NOT EXISTS "report_schedules_organizationId_nextRunAt_isActive_idx" ON "report_schedules"("organizationId", "nextRunAt", "isActive");

-- AddForeignKey
DO $$ BEGIN
  ALTER TABLE "saved_reports" ADD CONSTRAINT "saved_reports_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "organizations"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  ALTER TABLE "saved_reports" ADD CONSTRAINT "saved_reports_ownerUserId_fkey" FOREIGN KEY ("ownerUserId") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  ALTER TABLE "report_shares" ADD CONSTRAINT "report_shares_savedReportId_fkey" FOREIGN KEY ("savedReportId") REFERENCES "saved_reports"("id") ON DELETE CASCADE ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  ALTER TABLE "report_schedules" ADD CONSTRAINT "report_schedules_savedReportId_fkey" FOREIGN KEY ("savedReportId") REFERENCES "saved_reports"("id") ON DELETE CASCADE ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
