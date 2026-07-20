import { describe, expect, it } from "vitest";

import {
  canDownloadDocument,
  canViewDocument,
  isDocumentExpired,
  isPreviewableContentType,
} from "@/modules/documents/access";
import type { SessionUser } from "@/permissions/types";

const employee: SessionUser = {
  id: "emp-1",
  email: "emp@example.com",
  organizationId: "org1",
  role: "EMPLOYEE",
  status: "ACTIVE",
};

const outsider: SessionUser = {
  id: "emp-2",
  email: "other@example.com",
  organizationId: "org1",
  role: "EMPLOYEE",
  status: "ACTIVE",
};

const hr: SessionUser = {
  id: "hr-1",
  email: "hr@example.com",
  organizationId: "org1",
  role: "HR",
  status: "ACTIVE",
};

describe("document access", () => {
  it("allows organization-visible documents to viewers", () => {
    expect(
      canViewDocument(employee, {
        visibility: "ORGANIZATION",
        createdById: "someone",
      }),
    ).toBe(true);
  });

  it("blocks restricted documents without grant", () => {
    expect(
      canViewDocument(outsider, {
        visibility: "RESTRICTED",
        createdById: employee.id,
      }),
    ).toBe(false);
  });

  it("allows restricted docs via USER grant and respects download flag", () => {
    const doc = {
      visibility: "RESTRICTED" as const,
      createdById: "owner",
      grants: [
        {
          granteeType: "USER",
          granteeId: outsider.id,
          canDownload: false,
        },
      ],
    };
    expect(canViewDocument(outsider, doc)).toBe(true);
    expect(canDownloadDocument(outsider, doc)).toBe(false);
  });

  it("allows managers of documents module to access restricted files", () => {
    expect(
      canDownloadDocument(hr, {
        visibility: "RESTRICTED",
        createdById: "owner",
      }),
    ).toBe(true);
  });

  it("treats expired documents as inaccessible", () => {
    const expiresAt = new Date(Date.now() - 1000);
    expect(isDocumentExpired(expiresAt)).toBe(true);
    expect(
      canViewDocument(employee, {
        visibility: "ORGANIZATION",
        expiresAt,
      }),
    ).toBe(false);
  });

  it("detects previewable content types", () => {
    expect(isPreviewableContentType("application/pdf")).toBe(true);
    expect(isPreviewableContentType("image/png")).toBe(true);
    expect(isPreviewableContentType("application/zip")).toBe(false);
  });
});
