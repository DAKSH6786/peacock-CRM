import { NextResponse } from "next/server";

import { auth } from "@/auth";
import { toSessionUser } from "@/lib/session-user";
import {
  listAccessibleDocuments,
  recordDocumentDownload,
} from "@/modules/documents";
import { requirePermission } from "@/permissions";
import { prisma } from "@/database";
import { createObjectStorage } from "@/lib/storage";
import { createAuditLog } from "@/modules/audit/service";

export async function GET(request: Request) {
  try {
    const session = await auth();
    const user = toSessionUser(session);
    requirePermission(user, "documents:view");
    if (!user?.organizationId) {
      return NextResponse.json({ error: "No organization" }, { status: 400 });
    }

    const url = new URL(request.url);
    const documents = await listAccessibleDocuments({
      user,
      organizationId: user.organizationId,
      query: url.searchParams.get("q") ?? undefined,
      category: url.searchParams.get("category") ?? undefined,
      folderId: url.searchParams.get("folderId"),
      tag: url.searchParams.get("tag") ?? undefined,
    });

    const folders = await prisma.documentFolder.findMany({
      where: { organizationId: user.organizationId, deletedAt: null },
      orderBy: { name: "asc" },
    });

    return NextResponse.json({ documents, folders });
  } catch {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
}

export async function POST(request: Request) {
  try {
    const session = await auth();
    const user = toSessionUser(session);
    requirePermission(user, "documents:manage");
    if (!user?.organizationId) {
      return NextResponse.json({ error: "No organization" }, { status: 400 });
    }

    const body = (await request.json()) as {
      action?: "upload" | "download" | "folder";
      title?: string;
      category?: string;
      visibility?: string;
      folderId?: string | null;
      fileName?: string;
      contentType?: string;
      contentBase64?: string;
      tags?: string[];
      links?: Array<{ entityType: string; entityId: string }>;
      expiresAt?: string | null;
      documentId?: string;
      folderName?: string;
      parentId?: string | null;
    };

    if (body.action === "download" && body.documentId) {
      const result = await recordDocumentDownload({
        user,
        organizationId: user.organizationId,
        documentId: body.documentId,
      });
      if (!result.ok) {
        return NextResponse.json({ error: result.reason }, { status: 403 });
      }
      return NextResponse.json(result);
    }

    if (body.action === "folder" && body.folderName) {
      const folder = await prisma.documentFolder.create({
        data: {
          organizationId: user.organizationId,
          name: body.folderName,
          parentId: body.parentId ?? null,
          category: body.category ?? null,
          createdById: user.id,
        },
      });
      return NextResponse.json({ folder });
    }

    if (!body.title || !body.fileName || !body.contentBase64) {
      return NextResponse.json({ error: "Missing upload fields" }, { status: 400 });
    }

    const storage = createObjectStorage();
    const storageKey = `documents/${user.organizationId}/${Date.now()}-${body.fileName}`;
    const buffer = Buffer.from(body.contentBase64, "base64");
    await storage.putObject({
      key: storageKey,
      body: buffer,
      contentType: body.contentType ?? "application/octet-stream",
    });

    const document = await prisma.managedDocument.create({
      data: {
        organizationId: user.organizationId,
        title: body.title,
        category: body.category ?? "general",
        visibility: body.visibility ?? "ORGANIZATION",
        folderId: body.folderId ?? null,
        expiresAt: body.expiresAt ? new Date(body.expiresAt) : null,
        createdById: user.id,
      },
    });

    const version = await prisma.documentVersion.create({
      data: {
        organizationId: user.organizationId,
        documentId: document.id,
        version: 1,
        storageKey,
        fileName: body.fileName,
        contentType: body.contentType ?? "application/octet-stream",
        sizeBytes: buffer.byteLength,
        createdById: user.id,
      },
    });

    await prisma.managedDocument.update({
      where: { id: document.id },
      data: { currentVersionId: version.id },
    });

    if (body.tags?.length) {
      for (const tagName of body.tags) {
        const tag = await prisma.documentTag.upsert({
          where: {
            organizationId_name: {
              organizationId: user.organizationId,
              name: tagName,
            },
          },
          create: { organizationId: user.organizationId, name: tagName },
          update: {},
        });
        await prisma.documentTagLink.create({
          data: { documentId: document.id, tagId: tag.id },
        });
      }
    }

    if (body.links?.length) {
      await prisma.documentRecordLink.createMany({
        data: body.links.map((link) => ({
          organizationId: user.organizationId!,
          documentId: document.id,
          entityType: link.entityType,
          entityId: link.entityId,
        })),
      });
    }

    await createAuditLog({
      organizationId: user.organizationId,
      actorId: user.id,
      action: "CREATE",
      entityType: "ManagedDocument",
      entityId: document.id,
      metadata: { title: body.title },
    });

    return NextResponse.json({ documentId: document.id, versionId: version.id });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed";
    return NextResponse.json({ error: message }, { status: 400 });
  }
}
