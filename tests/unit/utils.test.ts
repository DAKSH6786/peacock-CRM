import { describe, expect, it } from "vitest";

import { formatMoney, toMinorUnits } from "@/lib/utils";
import { hasPermission, permissionsForRole } from "@/permissions/types";

describe("money helpers", () => {
  it("converts major units to minor units", () => {
    expect(toMinorUnits(12.34)).toBe(1234);
    expect(toMinorUnits(0.1)).toBe(10);
  });

  it("formats minor units as currency", () => {
    expect(formatMoney(1234, "USD", "en-US")).toContain("12.34");
  });
});

describe("permissions", () => {
  it("grants finance profitability only to finance-capable roles", () => {
    expect(hasPermission("FINANCE", "finance:view_profitability")).toBe(true);
    expect(hasPermission("EMPLOYEE", "finance:view_profitability")).toBe(false);
    expect(permissionsForRole("VIEWER")).toContain("dashboard:view");
  });
});
