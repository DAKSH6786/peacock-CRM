-- AlterEnum
DO $$ BEGIN
  ALTER TYPE "AuditAction" ADD VALUE IF NOT EXISTS 'IMPORT';
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  ALTER TYPE "AuditAction" ADD VALUE IF NOT EXISTS 'DOWNLOAD';
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- AlterTable import_jobs
ALTER TABLE "import_jobs" ADD COLUMN IF NOT EXISTS "entityType" TEXT;
UPDATE "import_jobs" SET "entityType" = COALESCE("entityType", "module", 'unknown') WHERE "entityType" IS NULL;
ALTER TABLE "import_jobs" ALTER COLUMN "entityType" SET NOT NULL;
ALTER TABLE "import_jobs" ALTER COLUMN "status" SET DEFAULT 'QUEUED';
ALTER TABLE "import_jobs" ADD COLUMN IF NOT EXISTS "fileName" TEXT;
ALTER TABLE "import_jobs" ADD COLUMN IF NOT EXISTS "storageKey" TEXT;
ALTER TABLE "import_jobs" ADD COLUMN IF NOT EXISTS "totalRows" INTEGER NOT NULL DEFAULT 0;
ALTER TABLE "import_jobs" ADD COLUMN IF NOT EXISTS "successRows" INTEGER NOT NULL DEFAULT 0;
ALTER TABLE "import_jobs" ADD COLUMN IF NOT EXISTS "failedRows" INTEGER NOT NULL DEFAULT 0;
ALTER TABLE "import_jobs" ADD COLUMN IF NOT EXISTS "skippedRows" INTEGER NOT NULL DEFAULT 0;
ALTER TABLE "import_jobs" ADD COLUMN IF NOT EXISTS "columnMapping" JSONB;
ALTER TABLE "import_jobs" ADD COLUMN IF NOT EXISTS "previewRows" JSONB;
ALTER TABLE "import_jobs" ADD COLUMN IF NOT EXISTS "validationErrors" JSONB;
ALTER TABLE "import_jobs" ADD COLUMN IF NOT EXISTS "errorReport" JSONB;
ALTER TABLE "import_jobs" ADD COLUMN IF NOT EXISTS "errorFileKey" TEXT;
ALTER TABLE "import_jobs" ADD COLUMN IF NOT EXISTS "duplicatePolicy" TEXT NOT NULL DEFAULT 'SKIP';
ALTER TABLE "import_jobs" ADD COLUMN IF NOT EXISTS "partialPolicy" TEXT NOT NULL DEFAULT 'COMMIT_VALID';
ALTER TABLE "import_jobs" ADD COLUMN IF NOT EXISTS "startedAt" TIMESTAMP(3);
ALTER TABLE "import_jobs" ADD COLUMN IF NOT EXISTS "completedAt" TIMESTAMP(3);
ALTER TABLE "import_jobs" DROP COLUMN IF EXISTS "module";
ALTER TABLE "import_jobs" DROP COLUMN IF EXISTS "rowCount";
ALTER TABLE "import_jobs" DROP COLUMN IF EXISTS "errorCount";
ALTER TABLE "import_jobs" DROP COLUMN IF EXISTS "result";

CREATE INDEX IF NOT EXISTS "import_jobs_organizationId_entityType_createdAt_idx"
  ON "import_jobs"("organizationId", "entityType", "createdAt");

DO $$ BEGIN
  ALTER TABLE "import_jobs" ADD CONSTRAINT "import_jobs_createdById_fkey"
    FOREIGN KEY ("createdById") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- AlterTable export_jobs
ALTER TABLE "export_jobs" ADD COLUMN IF NOT EXISTS "exportType" TEXT;
UPDATE "export_jobs" SET "exportType" = COALESCE("exportType", "module", 'tables') WHERE "exportType" IS NULL;
ALTER TABLE "export_jobs" ALTER COLUMN "exportType" SET NOT NULL;
ALTER TABLE "export_jobs" ALTER COLUMN "status" SET DEFAULT 'QUEUED';
ALTER TABLE "export_jobs" ADD COLUMN IF NOT EXISTS "columns" TEXT[] DEFAULT ARRAY[]::TEXT[];
ALTER TABLE "export_jobs" ADD COLUMN IF NOT EXISTS "dateFrom" TIMESTAMP(3);
ALTER TABLE "export_jobs" ADD COLUMN IF NOT EXISTS "dateTo" TIMESTAMP(3);
ALTER TABLE "export_jobs" ADD COLUMN IF NOT EXISTS "rowCount" INTEGER;
ALTER TABLE "export_jobs" ADD COLUMN IF NOT EXISTS "fileUrl" TEXT;
ALTER TABLE "export_jobs" ADD COLUMN IF NOT EXISTS "storageKey" TEXT;
ALTER TABLE "export_jobs" ADD COLUMN IF NOT EXISTS "expiresAt" TIMESTAMP(3);
ALTER TABLE "export_jobs" ADD COLUMN IF NOT EXISTS "requiresApproval" BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE "export_jobs" ADD COLUMN IF NOT EXISTS "approvedAt" TIMESTAMP(3);
ALTER TABLE "export_jobs" ADD COLUMN IF NOT EXISTS "approvedById" TEXT;
ALTER TABLE "export_jobs" ADD COLUMN IF NOT EXISTS "rejectionReason" TEXT;
ALTER TABLE "export_jobs" ADD COLUMN IF NOT EXISTS "startedAt" TIMESTAMP(3);
ALTER TABLE "export_jobs" ADD COLUMN IF NOT EXISTS "completedAt" TIMESTAMP(3);
ALTER TABLE "export_jobs" DROP COLUMN IF EXISTS "module";

CREATE INDEX IF NOT EXISTS "export_jobs_organizationId_exportType_createdAt_idx"
  ON "export_jobs"("organizationId", "exportType", "createdAt");

DO $$ BEGIN
  ALTER TABLE "export_jobs" ADD CONSTRAINT "export_jobs_createdById_fkey"
    FOREIGN KEY ("createdById") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  ALTER TABLE "export_jobs" ADD CONSTRAINT "export_jobs_approvedById_fkey"
    FOREIGN KEY ("approvedById") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- AlterTable webhook_endpoints
ALTER TABLE "webhook_endpoints" ADD COLUMN IF NOT EXISTS "name" TEXT;
UPDATE "webhook_endpoints" SET "name" = COALESCE("name", 'Webhook') WHERE "name" IS NULL;
ALTER TABLE "webhook_endpoints" ALTER COLUMN "name" SET NOT NULL;
ALTER TABLE "webhook_endpoints" ADD COLUMN IF NOT EXISTS "secretHash" TEXT;
UPDATE "webhook_endpoints"
  SET "secretHash" = COALESCE("secretHash", encode(sha256(convert_to(COALESCE("secretEnc", id), 'UTF8')), 'hex'))
  WHERE "secretHash" IS NULL;
ALTER TABLE "webhook_endpoints" ALTER COLUMN "secretHash" SET NOT NULL;
ALTER TABLE "webhook_endpoints" ADD COLUMN IF NOT EXISTS "failureCount" INTEGER NOT NULL DEFAULT 0;
ALTER TABLE "webhook_endpoints" ADD COLUMN IF NOT EXISTS "lastDeliveredAt" TIMESTAMP(3);

-- Convert events JSONB to TEXT[] when needed
ALTER TABLE "webhook_endpoints"
  ALTER COLUMN "events" DROP DEFAULT;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_name = 'webhook_endpoints'
      AND column_name = 'events'
      AND data_type = 'jsonb'
  ) THEN
    ALTER TABLE "webhook_endpoints"
      ALTER COLUMN "events" TYPE TEXT[]
      USING COALESCE(
        ARRAY(SELECT jsonb_array_elements_text("events")),
        ARRAY[]::TEXT[]
      );
  END IF;
END $$;

ALTER TABLE "webhook_endpoints" DROP COLUMN IF EXISTS "secretEnc";

-- CreateTable api_keys
CREATE TABLE IF NOT EXISTS "api_keys" (
    "id" TEXT NOT NULL,
    "organizationId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "keyPrefix" TEXT NOT NULL,
    "keyHash" TEXT NOT NULL,
    "scopes" TEXT[] DEFAULT ARRAY[]::TEXT[],
    "expiresAt" TIMESTAMP(3),
    "revokedAt" TIMESTAMP(3),
    "revokedById" TEXT,
    "lastUsedAt" TIMESTAMP(3),
    "createdById" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "api_keys_pkey" PRIMARY KEY ("id")
);

CREATE INDEX IF NOT EXISTS "api_keys_organizationId_keyPrefix_idx" ON "api_keys"("organizationId", "keyPrefix");
CREATE INDEX IF NOT EXISTS "api_keys_organizationId_revokedAt_idx" ON "api_keys"("organizationId", "revokedAt");

DO $$ BEGIN
  ALTER TABLE "api_keys" ADD CONSTRAINT "api_keys_organizationId_fkey"
    FOREIGN KEY ("organizationId") REFERENCES "organizations"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE "api_keys" ADD CONSTRAINT "api_keys_createdById_fkey"
    FOREIGN KEY ("createdById") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE "api_keys" ADD CONSTRAINT "api_keys_revokedById_fkey"
    FOREIGN KEY ("revokedById") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- CreateTable webhook_deliveries
CREATE TABLE IF NOT EXISTS "webhook_deliveries" (
    "id" TEXT NOT NULL,
    "organizationId" TEXT NOT NULL,
    "endpointId" TEXT NOT NULL,
    "event" TEXT NOT NULL,
    "payload" JSONB NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'PENDING',
    "attempts" INTEGER NOT NULL DEFAULT 0,
    "responseCode" INTEGER,
    "responseBody" TEXT,
    "errorMessage" TEXT,
    "nextRetryAt" TIMESTAMP(3),
    "deliveredAt" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "webhook_deliveries_pkey" PRIMARY KEY ("id")
);

CREATE INDEX IF NOT EXISTS "webhook_deliveries_organizationId_status_idx" ON "webhook_deliveries"("organizationId", "status");
CREATE INDEX IF NOT EXISTS "webhook_deliveries_endpointId_createdAt_idx" ON "webhook_deliveries"("endpointId", "createdAt");
CREATE INDEX IF NOT EXISTS "webhook_deliveries_nextRetryAt_idx" ON "webhook_deliveries"("nextRetryAt");

DO $$ BEGIN
  ALTER TABLE "webhook_deliveries" ADD CONSTRAINT "webhook_deliveries_endpointId_fkey"
    FOREIGN KEY ("endpointId") REFERENCES "webhook_endpoints"("id") ON DELETE CASCADE ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Document centre tables
CREATE TABLE IF NOT EXISTS "document_folders" (
    "id" TEXT NOT NULL,
    "organizationId" TEXT NOT NULL,
    "parentId" TEXT,
    "name" TEXT NOT NULL,
    "category" TEXT,
    "createdById" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "document_folders_pkey" PRIMARY KEY ("id")
);

CREATE INDEX IF NOT EXISTS "document_folders_organizationId_parentId_idx" ON "document_folders"("organizationId", "parentId");
CREATE INDEX IF NOT EXISTS "document_folders_deletedAt_idx" ON "document_folders"("deletedAt");

DO $$ BEGIN
  ALTER TABLE "document_folders" ADD CONSTRAINT "document_folders_organizationId_fkey"
    FOREIGN KEY ("organizationId") REFERENCES "organizations"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE "document_folders" ADD CONSTRAINT "document_folders_createdById_fkey"
    FOREIGN KEY ("createdById") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE "document_folders" ADD CONSTRAINT "document_folders_parentId_fkey"
    FOREIGN KEY ("parentId") REFERENCES "document_folders"("id") ON DELETE SET NULL ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS "document_versions" (
    "id" TEXT NOT NULL,
    "organizationId" TEXT NOT NULL,
    "documentId" TEXT NOT NULL,
    "version" INTEGER NOT NULL,
    "storageKey" TEXT NOT NULL,
    "fileName" TEXT NOT NULL,
    "contentType" TEXT,
    "sizeBytes" INTEGER,
    "changeNote" TEXT,
    "createdById" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "document_versions_pkey" PRIMARY KEY ("id")
);

CREATE TABLE IF NOT EXISTS "managed_documents" (
    "id" TEXT NOT NULL,
    "organizationId" TEXT NOT NULL,
    "folderId" TEXT,
    "title" TEXT NOT NULL,
    "category" TEXT,
    "visibility" TEXT NOT NULL DEFAULT 'ORGANIZATION',
    "expiresAt" TIMESTAMP(3),
    "currentVersionId" TEXT,
    "createdById" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "managed_documents_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX IF NOT EXISTS "managed_documents_currentVersionId_key" ON "managed_documents"("currentVersionId");
CREATE INDEX IF NOT EXISTS "managed_documents_organizationId_category_idx" ON "managed_documents"("organizationId", "category");
CREATE INDEX IF NOT EXISTS "managed_documents_organizationId_folderId_idx" ON "managed_documents"("organizationId", "folderId");
CREATE INDEX IF NOT EXISTS "managed_documents_deletedAt_idx" ON "managed_documents"("deletedAt");

CREATE UNIQUE INDEX IF NOT EXISTS "document_versions_documentId_version_key" ON "document_versions"("documentId", "version");
CREATE INDEX IF NOT EXISTS "document_versions_organizationId_documentId_idx" ON "document_versions"("organizationId", "documentId");

DO $$ BEGIN
  ALTER TABLE "managed_documents" ADD CONSTRAINT "managed_documents_organizationId_fkey"
    FOREIGN KEY ("organizationId") REFERENCES "organizations"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE "managed_documents" ADD CONSTRAINT "managed_documents_folderId_fkey"
    FOREIGN KEY ("folderId") REFERENCES "document_folders"("id") ON DELETE SET NULL ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE "managed_documents" ADD CONSTRAINT "managed_documents_createdById_fkey"
    FOREIGN KEY ("createdById") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE "managed_documents" ADD CONSTRAINT "managed_documents_currentVersionId_fkey"
    FOREIGN KEY ("currentVersionId") REFERENCES "document_versions"("id") ON DELETE SET NULL ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  ALTER TABLE "document_versions" ADD CONSTRAINT "document_versions_documentId_fkey"
    FOREIGN KEY ("documentId") REFERENCES "managed_documents"("id") ON DELETE CASCADE ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE "document_versions" ADD CONSTRAINT "document_versions_createdById_fkey"
    FOREIGN KEY ("createdById") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS "document_tags" (
    "id" TEXT NOT NULL,
    "organizationId" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "document_tags_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX IF NOT EXISTS "document_tags_organizationId_name_key" ON "document_tags"("organizationId", "name");

DO $$ BEGIN
  ALTER TABLE "document_tags" ADD CONSTRAINT "document_tags_organizationId_fkey"
    FOREIGN KEY ("organizationId") REFERENCES "organizations"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS "document_tag_links" (
    "id" TEXT NOT NULL,
    "documentId" TEXT NOT NULL,
    "tagId" TEXT NOT NULL,

    CONSTRAINT "document_tag_links_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX IF NOT EXISTS "document_tag_links_documentId_tagId_key" ON "document_tag_links"("documentId", "tagId");

DO $$ BEGIN
  ALTER TABLE "document_tag_links" ADD CONSTRAINT "document_tag_links_documentId_fkey"
    FOREIGN KEY ("documentId") REFERENCES "managed_documents"("id") ON DELETE CASCADE ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE "document_tag_links" ADD CONSTRAINT "document_tag_links_tagId_fkey"
    FOREIGN KEY ("tagId") REFERENCES "document_tags"("id") ON DELETE CASCADE ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS "document_record_links" (
    "id" TEXT NOT NULL,
    "organizationId" TEXT NOT NULL,
    "documentId" TEXT NOT NULL,
    "entityType" TEXT NOT NULL,
    "entityId" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "document_record_links_pkey" PRIMARY KEY ("id")
);

CREATE INDEX IF NOT EXISTS "document_record_links_organizationId_entityType_entityId_idx"
  ON "document_record_links"("organizationId", "entityType", "entityId");
CREATE INDEX IF NOT EXISTS "document_record_links_documentId_idx" ON "document_record_links"("documentId");

DO $$ BEGIN
  ALTER TABLE "document_record_links" ADD CONSTRAINT "document_record_links_documentId_fkey"
    FOREIGN KEY ("documentId") REFERENCES "managed_documents"("id") ON DELETE CASCADE ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS "document_access_grants" (
    "id" TEXT NOT NULL,
    "organizationId" TEXT NOT NULL,
    "documentId" TEXT NOT NULL,
    "granteeType" TEXT NOT NULL,
    "granteeId" TEXT NOT NULL,
    "canDownload" BOOLEAN NOT NULL DEFAULT true,
    "grantedById" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "expiresAt" TIMESTAMP(3),

    CONSTRAINT "document_access_grants_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX IF NOT EXISTS "document_access_grants_documentId_granteeType_granteeId_key"
  ON "document_access_grants"("documentId", "granteeType", "granteeId");

DO $$ BEGIN
  ALTER TABLE "document_access_grants" ADD CONSTRAINT "document_access_grants_documentId_fkey"
    FOREIGN KEY ("documentId") REFERENCES "managed_documents"("id") ON DELETE CASCADE ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE "document_access_grants" ADD CONSTRAINT "document_access_grants_grantedById_fkey"
    FOREIGN KEY ("grantedById") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS "document_download_logs" (
    "id" TEXT NOT NULL,
    "organizationId" TEXT NOT NULL,
    "documentId" TEXT NOT NULL,
    "userId" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "ipAddress" TEXT,
    "userAgent" TEXT,

    CONSTRAINT "document_download_logs_pkey" PRIMARY KEY ("id")
);

CREATE INDEX IF NOT EXISTS "document_download_logs_organizationId_documentId_createdAt_idx"
  ON "document_download_logs"("organizationId", "documentId", "createdAt");

DO $$ BEGIN
  ALTER TABLE "document_download_logs" ADD CONSTRAINT "document_download_logs_documentId_fkey"
    FOREIGN KEY ("documentId") REFERENCES "managed_documents"("id") ON DELETE CASCADE ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE "document_download_logs" ADD CONSTRAINT "document_download_logs_userId_fkey"
    FOREIGN KEY ("userId") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS "email_send_logs" (
    "id" TEXT NOT NULL,
    "organizationId" TEXT NOT NULL,
    "provider" TEXT NOT NULL,
    "templateKey" TEXT,
    "toAddress" TEXT NOT NULL,
    "subject" TEXT NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'QUEUED',
    "attempts" INTEGER NOT NULL DEFAULT 0,
    "providerMessageId" TEXT,
    "errorMessage" TEXT,
    "previewMode" BOOLEAN NOT NULL DEFAULT false,
    "payload" JSONB,
    "sentById" TEXT,
    "sentAt" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "email_send_logs_pkey" PRIMARY KEY ("id")
);

CREATE INDEX IF NOT EXISTS "email_send_logs_organizationId_status_idx" ON "email_send_logs"("organizationId", "status");
CREATE INDEX IF NOT EXISTS "email_send_logs_organizationId_createdAt_idx" ON "email_send_logs"("organizationId", "createdAt");

DO $$ BEGIN
  ALTER TABLE "email_send_logs" ADD CONSTRAINT "email_send_logs_organizationId_fkey"
    FOREIGN KEY ("organizationId") REFERENCES "organizations"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE "email_send_logs" ADD CONSTRAINT "email_send_logs_sentById_fkey"
    FOREIGN KEY ("sentById") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS "calendar_connections" (
    "id" TEXT NOT NULL,
    "organizationId" TEXT NOT NULL,
    "provider" TEXT NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'DISCONNECTED',
    "accountEmail" TEXT,
    "vaultRef" TEXT,
    "ownedById" TEXT,
    "lastSyncAt" TIMESTAMP(3),
    "lastError" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "calendar_connections_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX IF NOT EXISTS "calendar_connections_organizationId_provider_key"
  ON "calendar_connections"("organizationId", "provider");

DO $$ BEGIN
  ALTER TABLE "calendar_connections" ADD CONSTRAINT "calendar_connections_organizationId_fkey"
    FOREIGN KEY ("organizationId") REFERENCES "organizations"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  ALTER TABLE "calendar_connections" ADD CONSTRAINT "calendar_connections_ownedById_fkey"
    FOREIGN KEY ("ownedById") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS "calendar_sync_events" (
    "id" TEXT NOT NULL,
    "organizationId" TEXT NOT NULL,
    "provider" TEXT NOT NULL,
    "entityType" TEXT NOT NULL,
    "entityId" TEXT NOT NULL,
    "externalEventId" TEXT,
    "syncStatus" TEXT NOT NULL DEFAULT 'PENDING',
    "lastError" TEXT,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "calendar_sync_events_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX IF NOT EXISTS "calendar_sync_events_organizationId_provider_entityType_entityId_key"
  ON "calendar_sync_events"("organizationId", "provider", "entityType", "entityId");
CREATE INDEX IF NOT EXISTS "calendar_sync_events_organizationId_syncStatus_idx"
  ON "calendar_sync_events"("organizationId", "syncStatus");

DO $$ BEGIN
  ALTER TABLE "calendar_sync_events" ADD CONSTRAINT "calendar_sync_events_organizationId_fkey"
    FOREIGN KEY ("organizationId") REFERENCES "organizations"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
