import { describe, expect, it } from "vitest";

import { DEMO_SNAPSHOT } from "@/lib/command-centre";

describe("command centre demo snapshot", () => {
  it("exposes visibility index dimensions", () => {
    expect(DEMO_SNAPSHOT.signals).toHaveLength(7);
    expect(DEMO_SNAPSHOT.signals.map((s) => s.label)).toEqual([
      "Search Visibility",
      "AI Visibility",
      "Share of Answer",
      "Entity Authority",
      "Citation Authority",
      "Content Opportunity",
      "Agent Readiness",
    ]);
  });

  it("includes situation layer and peacock detected feed", () => {
    expect(DEMO_SNAPSHOT.situations.map((s) => s.label)).toContain("Biggest Opportunity");
    expect(DEMO_SNAPSHOT.situations.map((s) => s.label)).toContain("Biggest Threat");
    expect(DEMO_SNAPSHOT.feed_items[0]?.detection_label).toBe("PEACOCK DETECTED");
    expect(DEMO_SNAPSHOT.feed_items[0]?.body).toContain("18% → 31%");
    expect(DEMO_SNAPSHOT.feed_items[0]?.confidence_pct).toBe(87);
  });
});
