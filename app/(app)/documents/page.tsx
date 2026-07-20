import type { Metadata } from "next";

import { auth } from "@/auth";
import { PageHeader } from "@/components/shared/page-header";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { toSessionUser } from "@/lib/session-user";
import {
  DOCUMENT_CATEGORIES,
  DOCUMENT_LINK_ENTITY_TYPES,
  listAccessibleDocuments,
} from "@/modules/documents";
import { requirePermission } from "@/permissions";
import { prisma } from "@/database";

import { hasPermission } from "@/permissions/types";
import type { MembershipRole } from "@prisma/client";

import { DocumentsBrowser } from "@/components/documents/documents-browser";

export const metadata: Metadata = {
  title: "Documents",
};

export default async function DocumentsPage() {
  const session = await auth();
  const user = toSessionUser(session);
  requirePermission(user, "documents:view");

  const organizationId = user!.organizationId!;
  const documents = await listAccessibleDocuments({
    user: user!,
    organizationId,
  });
  const folders = await prisma.documentFolder.findMany({
    where: { organizationId, deletedAt: null },
    orderBy: { name: "asc" },
  });

  const canManage = hasPermission(
    user!.role as MembershipRole | null,
    "documents:manage",
  );

  return (
    <div>
      <PageHeader
        title="Document centre"
        description="Folders, categories, tags, record linkage, version history, expiry, restricted access, and download audit — backed by storage abstraction."
      />

      <div className="mb-6 grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Library</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-semibold">{documents.length}</CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Folders</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-semibold">{folders.length}</CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Linkable records</CardTitle>
            <CardDescription>
              {DOCUMENT_LINK_ENTITY_TYPES.length} entity types
            </CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-[var(--muted)]">
            {DOCUMENT_CATEGORIES.join(" · ")}
          </CardContent>
        </Card>
      </div>

      <DocumentsBrowser
        initialDocuments={documents.map((doc) => ({
          id: doc.id,
          title: doc.title,
          category: doc.category,
          visibility: doc.visibility,
          folderName: doc.folder?.name ?? null,
          tags: doc.tags.map((t) => t.tag.name),
          updatedAt: doc.updatedAt.toISOString(),
          expiresAt: doc.expiresAt?.toISOString() ?? null,
          fileName: doc.currentVersion?.fileName ?? null,
          contentType: doc.currentVersion?.contentType ?? null,
        }))}
        folders={folders.map((f) => ({ id: f.id, name: f.name, category: f.category }))}
        canManage={canManage}
      />
    </div>
  );
}
