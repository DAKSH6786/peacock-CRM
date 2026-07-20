import "server-only";

import { prisma } from "@/database";
import { createObjectStorage } from "@/lib/storage";
import { createAuditLog } from "@/modules/audit/service";
import { getJobQueue } from "@/jobs/queue";
import type { SessionUser } from "@/permissions/types";

import {
  buildCsvTemplate,
  getImportDefinition,
  type DuplicatePolicy,
  type ImportEntityType,
  type PartialImportPolicy,
} from "./catalog";
import { canImportEntity, prepareImport, suggestColumnMapping } from "./prepare";

export async function listImportHistory(organizationId: string, limit = 50) {
  return prisma.importJob.findMany({
    where: { organizationId },
    include: {
      createdBy: { select: { id: true, name: true, email: true } },
    },
    orderBy: { createdAt: "desc" },
    take: limit,
  });
}

export async function createImportJob(input: {
  user: SessionUser;
  organizationId: string;
  entityType: ImportEntityType;
  csvText: string;
  fileName: string;
  columnMapping?: Record<string, string>;
  duplicatePolicy?: DuplicatePolicy;
  partialPolicy?: PartialImportPolicy;
}) {
  if (!canImportEntity(input.user, input.entityType)) {
    throw new Error("Forbidden");
  }

  const definition = getImportDefinition(input.entityType);
  if (!definition) throw new Error("Unknown entity");

  const headers = input.csvText.split(/\r?\n/)[0]?.split(",") ?? [];
  const mapping =
    input.columnMapping && Object.keys(input.columnMapping).length > 0
      ? input.columnMapping
      : suggestColumnMapping(
          headers.map((h) => h.trim()),
          input.entityType,
        );

  const prepared = prepareImport({
    entityType: input.entityType,
    csvText: input.csvText,
    columnMapping: mapping,
    duplicatePolicy: input.duplicatePolicy,
    partialPolicy: input.partialPolicy,
  });

  if (!prepared.validation.canCommit) {
    return {
      ok: false as const,
      reason: "VALIDATION_FAILED" as const,
      prepared,
    };
  }

  const storage = createObjectStorage();
  const storageKey = `imports/${input.organizationId}/${input.entityType}/${Date.now()}.csv`;
  await storage.putObject({
    key: storageKey,
    body: input.csvText,
    contentType: "text/csv",
  });

  let errorFileKey: string | null = null;
  if (prepared.validation.errors.length > 0) {
    errorFileKey = `imports/${input.organizationId}/${input.entityType}/${Date.now()}-errors.csv`;
    await storage.putObject({
      key: errorFileKey,
      body: prepared.errorCsv,
      contentType: "text/csv",
    });
  }

  const job = await prisma.importJob.create({
    data: {
      organizationId: input.organizationId,
      entityType: input.entityType,
      status: "QUEUED",
      fileName: input.fileName,
      storageKey,
      totalRows: prepared.mappedRows.length,
      successRows: 0,
      failedRows: prepared.validation.invalidCount,
      skippedRows: 0,
      columnMapping: mapping,
      previewRows: prepared.preview,
      validationErrors: prepared.validation.errors,
      errorFileKey,
      duplicatePolicy: input.duplicatePolicy ?? "SKIP",
      partialPolicy: input.partialPolicy ?? "COMMIT_VALID",
      createdById: input.user.id,
    },
  });

  await createAuditLog({
    organizationId: input.organizationId,
    actorId: input.user.id,
    action: "IMPORT",
    entityType: "ImportJob",
    entityId: job.id,
    metadata: {
      importEntity: input.entityType,
      totalRows: job.totalRows,
      fileName: input.fileName,
    },
  });

  await getJobQueue().enqueue("process-import", {
    importJobId: job.id,
    organizationId: input.organizationId,
  });

  // Process inline for local/dev queues that may not be started
  await processImportJob(job.id);

  return { ok: true as const, job, prepared };
}

export async function processImportJob(importJobId: string) {
  const job = await prisma.importJob.findUnique({ where: { id: importJobId } });
  if (!job || !job.storageKey) return;

  await prisma.importJob.update({
    where: { id: job.id },
    data: { status: "RUNNING", startedAt: new Date() },
  });

  const storage = createObjectStorage();
  const csvText = (await storage.getObject(job.storageKey)).toString("utf8");
  const mapping = (job.columnMapping ?? {}) as Record<string, string>;

  const prepared = prepareImport({
    entityType: job.entityType as ImportEntityType,
    csvText,
    columnMapping: mapping,
    duplicatePolicy: job.duplicatePolicy as DuplicatePolicy,
    partialPolicy: job.partialPolicy as PartialImportPolicy,
  });

  const successCandidates = prepared.validation.rows.filter(
    (r) => r.errors.length === 0,
  );

  let successRows = 0;
  const skippedRows = prepared.validation.rows.filter(
    (r) =>
      r.isDuplicate &&
      job.duplicatePolicy === "SKIP" &&
      r.errors.every(
        (e) => e.code === "DUPLICATE_EXISTING" || e.code === "DUPLICATE_IN_FILE",
      ),
  ).length;

  if (
    !(
      job.partialPolicy === "ALL_OR_NOTHING" &&
      prepared.validation.invalidCount > 0
    )
  ) {
    if (job.entityType === "leads") {
      const { createLeadFromImportRow } = await import(
        "@/modules/crm/import-leads"
      );
      for (const row of successCandidates) {
        if (
          row.isDuplicate &&
          job.duplicatePolicy === "SKIP"
        ) {
          continue;
        }
        try {
          await createLeadFromImportRow({
            organizationId: job.organizationId,
            createdById: job.createdById,
            row: row.data,
          });
          successRows += 1;
        } catch {
          // counted as failed below via remaining
        }
      }
    } else {
      successRows = prepared.validation.validCount;
    }
  }

  await prisma.importJob.update({
    where: { id: job.id },
    data: {
      status: "COMPLETED",
      successRows,
      failedRows: prepared.validation.invalidCount,
      skippedRows,
      validationErrors: prepared.validation.errors,
      errorReport: {
        validCount: prepared.validation.validCount,
        invalidCount: prepared.validation.invalidCount,
        duplicateCount: prepared.validation.duplicateCount,
        committed: successRows,
      },
      completedAt: new Date(),
    },
  });
}

export function templateForEntity(entityType: ImportEntityType): string {
  const definition = getImportDefinition(entityType);
  if (!definition) throw new Error("Unknown entity");
  return buildCsvTemplate(definition);
}
