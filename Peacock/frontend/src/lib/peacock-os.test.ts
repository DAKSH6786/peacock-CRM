import { describe, expect, it } from "vitest";

import {
  DEMO_ARCHITECTURE,
  DEMO_COST,
  DEMO_MOAT,
  DEMO_QUALITY,
  DEMO_RELIABILITY,
  DEMO_SECURITY,
  SUBSYSTEM_LINKS,
} from "@/lib/peacock-os";

describe("peacock-os demos", () => {
  it("positions beyond visibility-only", () => {
    expect(DEMO_ARCHITECTURE.not_only_visibility_note).toMatch(/How visible are we/);
    expect(DEMO_ARCHITECTURE.not_only_visibility).toBe(true);
    expect(DEMO_COST.selected_method_kind).toBe("deterministic");
    expect(DEMO_RELIABILITY.partial_result_summary).toMatch(/4\/5/);
    expect(DEMO_SECURITY.crawler_treated_as_data).toBe(true);
    expect(DEMO_QUALITY.completeness_verdict).toBe("incomplete");
    expect(DEMO_MOAT.pathways_count).toBe(7);
  });

  it("lists subsystem surfaces", () => {
    const hrefs = SUBSYSTEM_LINKS.map((s) => s.href);
    expect(hrefs).toContain("/architecture");
    expect(hrefs).toContain("/security");
    expect(hrefs).toContain("/research");
  });
});
