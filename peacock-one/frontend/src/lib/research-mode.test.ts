import { describe, expect, it } from "vitest";

import { DEMO_RESEARCH_STUDY } from "@/lib/research-mode";

describe("research mode demo study", () => {
  it("covers the laboratory pipeline phases", () => {
    expect(DEMO_RESEARCH_STUDY.completed_phases).toEqual([
      "hypothesis",
      "metric",
      "pages",
      "prompts",
      "baseline",
      "treatment",
      "repeat_observations",
      "uncertainty",
      "findings",
    ]);
  });

  it("asks the proprietary statistics citation question", () => {
    expect(DEMO_RESEARCH_STUDY.research_question.toLowerCase()).toContain(
      "proprietary statistics",
    );
    expect(DEMO_RESEARCH_STUDY.findings[0]?.auto_causal_conclusion_rejected).toBe(
      true,
    );
  });
});
