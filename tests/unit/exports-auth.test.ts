import { describe, expect, it } from "vitest";

import {
  canRequestExport,
  exportRequiresApproval,
  filterExportColumns,
  isExportDownloadExpired,
} from "@/modules/exports/policy";
import type { SessionUser } from "@/permissions/types";

const financeUser: SessionUser = {
  id: "u1",
  email: "finance@example.com",
  organizationId: "org1",
  role: "FINANCE",
  status: "ACTIVE",
};

const salesUser: SessionUser = {
  id: "u2",
  email: "sales@example.com",
  organizationId: "org1",
  role: "SALES",
  status: "ACTIVE",
};

const hrUser: SessionUser = {
  id: "u3",
  email: "hr@example.com",
  organizationId: "org1",
  role: "HR",
  status: "ACTIVE",
};

const employeeUser: SessionUser = {
  id: "u4",
  email: "emp@example.com",
  organizationId: "org1",
  role: "EMPLOYEE",
  status: "ACTIVE",
};

describe("export authorization", () => {
  it("allows domain exports for roles with domain permission", () => {
    expect(canRequestExport(salesUser, "crm")).toBe(true);
    expect(canRequestExport(financeUser, "invoices")).toBe(true);
    expect(canRequestExport(hrUser, "employees")).toBe(true);
  });

  it("denies exports without permission", () => {
    expect(canRequestExport(employeeUser, "crm")).toBe(false);
    expect(canRequestExport(salesUser, "finance")).toBe(false);
    expect(canRequestExport(salesUser, "reports")).toBe(false);
  });

  it("strips sensitive columns without elevated permission", () => {
    const hrWithoutComp: SessionUser = {
      ...hrUser,
      role: "MANAGER",
    };
    const columns = filterExportColumns(hrWithoutComp, "employees", [
      "employeeCode",
      "name",
      "compensation",
    ]);
    expect(columns).toEqual(["employeeCode", "name"]);
    expect(columns).not.toContain("compensation");

    const financeCols = filterExportColumns(financeUser, "finance", [
      "period",
      "revenue",
      "margin",
    ]);
    expect(financeCols).toContain("margin");

    const salesCrm = filterExportColumns(salesUser, "crm", [
      "type",
      "name",
      "email",
    ]);
    expect(salesCrm).toEqual(["type", "name", "email"]);
  });

  it("requires approval for sensitive employee/finance exports for non-admins", () => {
    expect(exportRequiresApproval(hrUser, "employees")).toBe(true);
    expect(exportRequiresApproval(financeUser, "finance")).toBe(true);
    expect(exportRequiresApproval(salesUser, "crm")).toBe(false);
  });

  it("detects expired download links", () => {
    const past = new Date(Date.now() - 60_000);
    const future = new Date(Date.now() + 60_000);
    expect(isExportDownloadExpired(past)).toBe(true);
    expect(isExportDownloadExpired(future)).toBe(false);
    expect(isExportDownloadExpired(null)).toBe(false);
  });
});
