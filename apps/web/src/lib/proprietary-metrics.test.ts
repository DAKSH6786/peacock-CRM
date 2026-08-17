import { describe, expect, it } from "vitest";

import { DEMO_METRICS } from "@/lib/proprietary-metrics";

describe("proprietary metrics demo scorecard", () => {
  it("rejects official platform ranking-factor representation", () => {
    for (const name of ["Google", "OpenAI", "Anthropic", "Perplexity"]) {
      expect(DEMO_METRICS.proprietary_disclaimer).toContain(name);
      expect(DEMO_METRICS.not_official_platforms).toContain(name);
    }
  });

  it("exposes formula ids on metrics", () => {
    expect(DEMO_METRICS.metrics[0]?.formula_id).toBe("PVI-1");
    expect(DEMO_METRICS.metrics[0]?.formula_text.length).toBeGreaterThan(10);
  });
});
