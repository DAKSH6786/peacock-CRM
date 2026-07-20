import "server-only";

import type { Prisma } from "@prisma/client";

import { prisma } from "@/database";
import { createObjectStorage } from "@/lib/storage";
import { createAuditLog } from "@/modules/audit/service";
import { getJobQueue } from "@/jobs/queue";
import type { SessionUser } from "@/permissions/types";

import {
  buildExportCsv,
  canRequestExport,
  computeExpiryDate,
  exportRequiresApproval,
  filterExportColumns,
  getExportDefinition,
  isExportDownloadExpired,
  type ExportType,
} from "./policy";

export async function listExportHistory(organizationId: string, limit = 50) {
  return prisma.exportJob.findMany({
    where: { organizationId },
    include: {
      createdBy: { select: { id: true, name: true, email: true } },
      approvedBy: { select: { id: true, name: true, email: true } },
    },
    orderBy: { createdAt: "desc" },
    take: limit,
  });
}

export async function createExportJob(input: {
  user: SessionUser;
  organizationId: string;
  exportType: ExportType;
  columns?: string[];
  dateFrom?: string | null;
  dateTo?: string | null;
  filters?: Record<string, unknown>;
}) {
  if (!canRequestExport(input.user, input.exportType)) {
    throw new Error("Forbidden");
  }

  const columns = filterExportColumns(
    input.user,
    input.exportType,
    input.columns ?? [],
  );
  if (columns.length === 0) {
    throw new Error("No exportable columns for this role");
  }

  const requiresApproval = exportRequiresApproval(input.user, input.exportType);

  const job = await prisma.exportJob.create({
    data: {
      organizationId: input.organizationId,
      exportType: input.exportType,
      status: requiresApproval ? "PENDING_APPROVAL" : "QUEUED",
      columns,
      filters: (input.filters ?? {}) as Prisma.InputJsonValue,
      dateFrom: input.dateFrom ? new Date(input.dateFrom) : null,
      dateTo: input.dateTo ? new Date(input.dateTo) : null,
      requiresApproval,
      createdById: input.user.id,
      expiresAt: computeExpiryDate(input.exportType),
    },
  });

  await createAuditLog({
    organizationId: input.organizationId,
    actorId: input.user.id,
    action: "EXPORT",
    entityType: "ExportJob",
    entityId: job.id,
    metadata: {
      exportType: input.exportType,
      columns,
      requiresApproval,
    },
  });

  if (!requiresApproval) {
    await getJobQueue().enqueue("process-export", {
      exportJobId: job.id,
      organizationId: input.organizationId,
    });
    await processExportJob(job.id);
  }

  return job;
}

export async function approveExportJob(input: {
  user: SessionUser;
  organizationId: string;
  exportJobId: string;
  approve: boolean;
  reason?: string;
}) {
  const job = await prisma.exportJob.findFirst({
    where: { id: input.exportJobId, organizationId: input.organizationId },
  });
  if (!job) throw new Error("Not found");

  if (!input.approve) {
    return prisma.exportJob.update({
      where: { id: job.id },
      data: {
        status: "REJECTED",
        rejectionReason: input.reason ?? "Rejected",
        approvedById: input.user.id,
      },
    });
  }

  const updated = await prisma.exportJob.update({
    where: { id: job.id },
    data: {
      status: "QUEUED",
      approvedAt: new Date(),
      approvedById: input.user.id,
    },
  });

  await processExportJob(updated.id);
  return updated;
}

export async function processExportJob(exportJobId: string) {
  const job = await prisma.exportJob.findUnique({ where: { id: exportJobId } });
  if (!job) return;

  await prisma.exportJob.update({
    where: { id: job.id },
    data: { status: "RUNNING", startedAt: new Date() },
  });

  // Placeholder dataset — real exporters plug in per exportType
  const sampleRows: Record<string, unknown>[] = [
    Object.fromEntries(job.columns.map((col, index) => [col, `sample-${index}`])),
  ];

  const csv = buildExportCsv(job.columns, sampleRows);
  const storage = createObjectStorage();
  const storageKey = `exports/${job.organizationId}/${job.exportType}/${job.id}.csv`;
  await storage.putObject({
    key: storageKey,
    body: csv,
    contentType: "text/csv",
  });
  const fileUrl = await storage.getSignedDownloadUrl(storageKey, {
    expiresInSeconds: 60 * 60 * 12,
  });

  await prisma.exportJob.update({
    where: { id: job.id },
    data: {
      status: "COMPLETED",
      storageKey,
      fileUrl,
      rowCount: sampleRows.length,
      completedAt: new Date(),
      expiresAt: job.expiresAt ?? computeExpiryDate(job.exportType),
    },
  });
}

export async function getExportDownload(input: {
  user: SessionUser;
  organizationId: string;
  exportJobId: string;
}) {
  const job = await prisma.exportJob.findFirst({
    where: { id: input.exportJobId, organizationId: input.organizationId },
  });
  if (!job) return { ok: false as const, reason: "NOT_FOUND" as const };
  if (job.status !== "COMPLETED" || !job.storageKey) {
    return { ok: false as const, reason: "NOT_READY" as const };
  }
  if (isExportDownloadExpired(job.expiresAt)) {
    return { ok: false as const, reason: "EXPIRED" as const };
  }
  if (!canRequestExport(input.user, job.exportType)) {
    return { ok: false as const, reason: "FORBIDDEN" as const };
  }

  const storage = createObjectStorage();
  const url = await storage.getSignedDownloadUrl(job.storageKey, {
    expiresInSeconds: 600,
  });

  await createAuditLog({
    organizationId: input.organizationId,
    actorId: input.user.id,
    action: "DOWNLOAD",
    entityType: "ExportJob",
    entityId: job.id,
    metadata: { exportType: job.exportType },
  });

  return { ok: true as const, url, exportType: job.exportType };
}

export { getExportDefinition };
