import { describe, expect, it } from "vitest";

import {
  personaLabel,
  resolveDashboardPersona,
} from "@/modules/dashboard/persona";

describe("resolveDashboardPersona", () => {
  it("maps executive roles to founder", () => {
    expect(resolveDashboardPersona("SUPER_ADMIN")).toBe("founder");
    expect(resolveDashboardPersona("ADMIN")).toBe("founder");
  });

  it("maps specialized roles", () => {
    expect(resolveDashboardPersona("SALES")).toBe("sales_leader");
    expect(resolveDashboardPersona("MANAGER")).toBe("manager");
    expect(resolveDashboardPersona("DEPARTMENT_HEAD")).toBe("manager");
    expect(resolveDashboardPersona("FINANCE")).toBe("finance");
    expect(resolveDashboardPersona("HR")).toBe("hr");
  });

  it("defaults remaining roles to employee", () => {
    expect(resolveDashboardPersona("EMPLOYEE")).toBe("employee");
    expect(resolveDashboardPersona("VIEWER")).toBe("employee");
    expect(resolveDashboardPersona(null)).toBe("employee");
  });

  it("returns readable labels", () => {
    expect(personaLabel("founder")).toContain("Founder");
    expect(personaLabel("sales_leader")).toContain("Sales");
  });
});
