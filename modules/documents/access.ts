import type { MembershipRole } from "@prisma/client";

import type { SessionUser } from "@/permissions/types";
import { hasPermission } from "@/permissions/types";

export type DocumentVisibility = "ORGANIZATION" | "RESTRICTED" | "PRIVATE";

export type DocumentRecordEntityType =
  | "employees"
  | "leads"
  | "clients"
  | "deals"
  | "projects"
  | "tasks"
  | "invoices"
  | "expenses"
  | "vendors"
  | "xyme_goals"
  | "policies";

export const DOCUMENT_LINK_ENTITY_TYPES: DocumentRecordEntityType[] = [
  "employees",
  "leads",
  "clients",
  "deals",
  "projects",
  "tasks",
  "invoices",
  "expenses",
  "vendors",
  "xyme_goals",
  "policies",
];

export const DOCUMENT_CATEGORIES = [
  "general",
  "hr",
  "finance",
  "legal",
  "project",
  "policy",
  "sales",
] as const;

export type DocumentAccessContext = {
  visibility: DocumentVisibility;
  createdById?: string | null;
  expiresAt?: Date | null;
  grants?: Array<{
    granteeType: string;
    granteeId: string;
    canDownload: boolean;
    expiresAt?: Date | null;
  }>;
};

export function isDocumentExpired(
  expiresAt: Date | null | undefined,
  now = new Date(),
): boolean {
  if (!expiresAt) return false;
  return expiresAt.getTime() < now.getTime();
}

export function canViewDocument(
  user: SessionUser,
  doc: DocumentAccessContext,
  now = new Date(),
): boolean {
  if (!hasPermission(user.role as MembershipRole | null, "documents:view")) {
    return false;
  }
  if (isDocumentExpired(doc.expiresAt, now)) return false;

  if (doc.visibility === "ORGANIZATION") return true;
  if (doc.createdById && doc.createdById === user.id) return true;
  if (hasPermission(user.role as MembershipRole | null, "documents:manage")) {
    return true;
  }

  return Boolean(findActiveGrant(user, doc, now));
}

export function canDownloadDocument(
  user: SessionUser,
  doc: DocumentAccessContext,
  now = new Date(),
): boolean {
  if (!canViewDocument(user, doc, now)) return false;
  if (doc.visibility === "ORGANIZATION") return true;
  if (doc.createdById && doc.createdById === user.id) return true;
  if (hasPermission(user.role as MembershipRole | null, "documents:manage")) {
    return true;
  }

  const grant = findActiveGrant(user, doc, now);
  return Boolean(grant?.canDownload);
}

function findActiveGrant(
  user: SessionUser,
  doc: DocumentAccessContext,
  now: Date,
) {
  const grants = doc.grants ?? [];
  return grants.find((grant) => {
    if (grant.expiresAt && grant.expiresAt.getTime() < now.getTime()) {
      return false;
    }
    if (grant.granteeType === "USER" && grant.granteeId === user.id) {
      return true;
    }
    if (
      grant.granteeType === "ROLE" &&
      user.role &&
      grant.granteeId === user.role
    ) {
      return true;
    }
    return false;
  });
}

export function isPreviewableContentType(contentType?: string | null): boolean {
  if (!contentType) return false;
  return (
    contentType.startsWith("image/") ||
    contentType === "application/pdf" ||
    contentType.startsWith("text/")
  );
}
