import { describe, expect, it } from "vitest";

import { DEMO_EXECUTIVE_BRIEF } from "@/lib/executive-brain";

describe("executive brain demo brief", () => {
  it("covers the eight executive questions", () => {
    expect(DEMO_EXECUTIVE_BRIEF.answers.map((a) => a.question_label)).toEqual([
      "Where are we winning?",
      "Where are we losing?",
      "Why?",
      "What changed?",
      "What is worth doing?",
      "What will it cost?",
      "What could it return?",
      "What happens if we do nothing?",
    ]);
  });

  it("includes CEO and CMO ready summaries", () => {
    const roles = DEMO_EXECUTIVE_BRIEF.role_summaries.map((r) => r.role);
    expect(roles).toContain("ceo");
    expect(roles).toContain("cmo");
    expect(DEMO_EXECUTIVE_BRIEF.role_summaries.every((r) => r.call_to_action)).toBe(
      true,
    );
  });
});
