import { describe, expect, it } from "vitest";

import { hasPermission } from "@/permissions/types";

describe("universal search permission gates", () => {
  it("allows CRM categories for sales roles", () => {
    expect(hasPermission("SALES", "crm:view")).toBe(true);
    expect(hasPermission("SALES", "finance:view")).toBe(false);
  });

  it("allows finance categories only for finance/admin", () => {
    expect(hasPermission("FINANCE", "finance:view")).toBe(true);
    expect(hasPermission("EMPLOYEE", "finance:view")).toBe(false);
    expect(hasPermission("SUPER_ADMIN", "finance:view")).toBe(true);
  });

  it("keeps employee documents permission scoped", () => {
    expect(hasPermission("EMPLOYEE", "documents:view")).toBe(true);
    expect(hasPermission("VIEWER", "documents:view")).toBe(false);
  });

  it("does not grant compensation visibility to sales by default", () => {
    expect(hasPermission("SALES", "employees:view_compensation")).toBe(false);
    expect(hasPermission("SUPER_ADMIN", "employees:view_compensation")).toBe(
      true,
    );
  });
});
