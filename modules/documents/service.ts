import "server-only";

import { prisma } from "@/database";
import { createAuditLog } from "@/modules/audit/service";
import { createObjectStorage } from "@/lib/storage";
import type { SessionUser } from "@/permissions/types";

import {
  canDownloadDocument,
  canViewDocument,
  type DocumentVisibility,
} from "./access";

export async function listAccessibleDocuments(input: {
  user: SessionUser;
  organizationId: string;
  query?: string;
  category?: string;
  folderId?: string | null;
  tag?: string;
}) {
  const documents = await prisma.managedDocument.findMany({
    where: {
      organizationId: input.organizationId,
      deletedAt: null,
      ...(input.category ? { category: input.category } : {}),
      ...(input.folderId !== undefined
        ? { folderId: input.folderId }
        : {}),
      ...(input.query
        ? {
            OR: [
              { title: { contains: input.query, mode: "insensitive" } },
              { category: { contains: input.query, mode: "insensitive" } },
            ],
          }
        : {}),
      ...(input.tag
        ? { tags: { some: { tag: { name: input.tag } } } }
        : {}),
    },
    include: {
      accessGrants: true,
      tags: { include: { tag: true } },
      currentVersion: true,
      links: true,
      folder: true,
    },
    orderBy: { updatedAt: "desc" },
    take: 200,
  });

  return documents.filter((doc) =>
    canViewDocument(input.user, {
      visibility: doc.visibility as DocumentVisibility,
      createdById: doc.createdById,
      expiresAt: doc.expiresAt,
      grants: doc.accessGrants,
    }),
  );
}

export async function recordDocumentDownload(input: {
  user: SessionUser;
  organizationId: string;
  documentId: string;
  ipAddress?: string | null;
  userAgent?: string | null;
}) {
  const doc = await prisma.managedDocument.findFirst({
    where: {
      id: input.documentId,
      organizationId: input.organizationId,
      deletedAt: null,
    },
    include: { accessGrants: true, currentVersion: true },
  });

  if (!doc) {
    return { ok: false as const, reason: "NOT_FOUND" };
  }

  const allowed = canDownloadDocument(input.user, {
    visibility: doc.visibility as DocumentVisibility,
    createdById: doc.createdById,
    expiresAt: doc.expiresAt,
    grants: doc.accessGrants,
  });

  if (!allowed) {
    return { ok: false as const, reason: "FORBIDDEN" };
  }

  await prisma.documentDownloadLog.create({
    data: {
      organizationId: input.organizationId,
      documentId: doc.id,
      userId: input.user.id,
      ipAddress: input.ipAddress ?? null,
      userAgent: input.userAgent ?? null,
    },
  });

  await createAuditLog({
    organizationId: input.organizationId,
    actorId: input.user.id,
    action: "DOWNLOAD",
    entityType: "ManagedDocument",
    entityId: doc.id,
    metadata: { title: doc.title },
    ipAddress: input.ipAddress,
    userAgent: input.userAgent,
  });

  const storage = createObjectStorage();
  const version = doc.currentVersion;
  if (!version) {
    return { ok: false as const, reason: "NO_VERSION" };
  }

  const url = await storage.getSignedDownloadUrl(version.storageKey, {
    expiresInSeconds: 3600,
  });

  return {
    ok: true as const,
    url,
    fileName: version.fileName,
    contentType: version.contentType,
  };
}
