import { describe, expect, it } from "vitest";

import {
  PROMPT_TYPES,
  SYNTHETIC_PERSONAS,
  expandPromptUniverse,
  promptUniverseCatalog,
} from "@/modules/prompt-universe";

describe("prompt universe intelligence", () => {
  it("covers all product prompt types and synthetic personas", () => {
    expect(PROMPT_TYPES).toHaveLength(14);
    expect(PROMPT_TYPES).toContain("problem_solving");
    expect(SYNTHETIC_PERSONAS.map((p) => p.code)).toEqual(
      expect.arrayContaining([
        "cfo",
        "cmo",
        "student",
        "enterprise_buyer",
        "technical_evaluator",
        "hnwi",
        "small_business_owner",
        "developer",
        "parent",
        "healthcare_professional",
      ]),
    );
    const catalog = promptUniverseCatalog();
    expect(catalog.sourceKinds).toContain("search_console_query");
    expect(catalog.sourceKinds).toContain("people_also_ask");
  });

  it("tracks both simple and contextual prompts for the same family", () => {
    const result = expandPromptUniverse({
      brandName: "Peacock CRM",
      industry: "SaaS",
      location: "eu",
      personaCodes: ["enterprise_buyer", "technical_evaluator"],
      signals: [
        {
          sourceKind: "product",
          signalText: "CRM",
          productName: "CRM",
          weight: 1.2,
        },
      ],
    });

    expect(result.simpleCount).toBeGreaterThan(0);
    expect(result.contextualCount).toBeGreaterThan(0);
    expect(result.familyCount).toBe(1);

    const simples = result.prompts.filter((p) => p.complexity === "simple");
    const contextual = result.prompts.filter(
      (p) => p.complexity === "contextual",
    );
    expect(simples.some((p) => p.promptText.startsWith("best CRM"))).toBe(true);
    expect(
      contextual.some(
        (p) =>
          p.persona === "enterprise_buyer" &&
          p.promptText.toLowerCase().includes("shortlist"),
      ),
    ).toBe(true);

    for (const prompt of result.prompts) {
      expect(prompt.topic).toBeTruthy();
      expect(prompt.intent).toBeTruthy();
      expect(prompt.persona).toBeTruthy();
      expect(prompt.funnelStage).toBeTruthy();
      expect(prompt.location).toBeTruthy();
      expect(prompt.commercialValue).toBeGreaterThanOrEqual(0);
      expect(prompt.commercialValue).toBeLessThanOrEqual(1);
      expect(prompt.brandRelevance).toBeGreaterThanOrEqual(0);
      expect(PROMPT_TYPES).toContain(prompt.promptType);
    }
  });
});
