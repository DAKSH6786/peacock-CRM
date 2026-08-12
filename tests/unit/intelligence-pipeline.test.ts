import { describe, expect, it } from "vitest";

import {
  ConnectorRegistry,
  DEFAULT_ROLE_PROVIDER,
  ROLE_PROMPTS,
  renderUserPrompt,
} from "@/modules/connectors";
import { analyzePage } from "@/modules/crawl";
import { evaluateAeo } from "@/modules/aeo";
import { evaluateGeo } from "@/modules/geo";
import {
  runIntelligencePipeline,
  PIPELINE_STAGES,
} from "@/modules/intelligence";
import { evaluateTechnicalSeo } from "@/modules/seo";

describe("connector role differentiation", () => {
  it("assigns distinct default providers per specialist role", () => {
    expect(DEFAULT_ROLE_PROVIDER.WEB_RESEARCH).toBe("PERPLEXITY");
    expect(DEFAULT_ROLE_PROVIDER.STRUCTURAL_CRITIQUE).toBe("ANTHROPIC");
    expect(DEFAULT_ROLE_PROVIDER.SYNTHESIS).toBe("OPENAI");
    expect(DEFAULT_ROLE_PROVIDER.ENTITY_EXTRACTION).toBe("GEMINI");
    expect(DEFAULT_ROLE_PROVIDER.SECOND_OPINION).toBe("DEEPSEEK");
  });

  it("uses different prompt templates across roles", () => {
    const templates = Object.values(ROLE_PROMPTS).map((p) => p.templateId);
    expect(new Set(templates).size).toBe(templates.length);
    expect(ROLE_PROMPTS.VISIBILITY_PROBE.templateId).toBe(
      "measure.visibility_probe",
    );
    expect(ROLE_PROMPTS.SYNTHESIS.templateId).not.toBe(
      ROLE_PROMPTS.VISIBILITY_PROBE.templateId,
    );
  });

  it("renders role-specific user prompts", () => {
    const research = renderUserPrompt("WEB_RESEARCH", {
      brand: "Acme",
      domain: "acme.test",
      topics: "AEO",
    });
    const probe = renderUserPrompt("VISIBILITY_PROBE", {
      probeQuestion: "Who leads generative visibility?",
    });
    expect(research).toContain("Acme");
    expect(research).not.toEqual(probe);
    expect(probe).toContain("Who leads generative visibility?");
  });

  it("refuses identical template fan-out across roles", () => {
    const registry = new ConnectorRegistry();
    expect(() =>
      registry.assertNotIdenticalFanout([
        { role: "SYNTHESIS", templateId: "same" },
        { role: "SECOND_OPINION", templateId: "same" },
      ]),
    ).toThrow(/identical template/);
  });
});

describe("deterministic observe engines", () => {
  it("flags missing technical SEO signals", () => {
    const page = analyzePage({
      url: "https://acme.test",
      html: "<html><head></head><body><p>Hi</p></body></html>",
    });
    const findings = evaluateTechnicalSeo([page]);
    expect(findings.some((f) => f.code === "missing_title")).toBe(true);
    expect(page.technicalFlags).toContain("thin_content");
  });

  it("scores AEO and GEO gaps", () => {
    const page = analyzePage({
      url: "https://acme.test",
      html: `<html><head><title>Home</title></head><body><h1>Home</h1>${"<p>word</p>".repeat(50)}</body></html>`,
    });
    const aeo = evaluateAeo([page]);
    const geo = evaluateGeo([page], "Acme");
    expect(aeo.score).toBeLessThan(1);
    expect(geo.findings.some((f) => f.code === "weak_brand_onpage")).toBe(true);
  });
});

describe("cognitive pipeline", () => {
  it("runs the full OBSERVE→LEARN loop with differentiated roles", async () => {
    const result = await runIntelligencePipeline({
      id: "p1",
      organizationId: "o1",
      name: "Acme",
      brand: "Acme",
      domain: "acme.test",
      rootUrl: "https://acme.test",
      keywords: ["AEO", "GEO"],
      competitors: [{ name: "Rival", domain: "rival.test" }],
    });

    expect(result.status).toBe("COMPLETED");
    for (const stage of PIPELINE_STAGES) {
      expect(result.stages[stage]?.status).toBe("SUCCEEDED");
    }

    const thinkTraces = result.stages.THINK?.traces ?? [];
    const roles = new Set(thinkTraces.map((t) => t.role));
    expect(roles.has("STRUCTURAL_CRITIQUE")).toBe(true);
    expect(roles.has("SYNTHESIS")).toBe(true);
    expect(roles.has("SECOND_OPINION")).toBe(true);
    expect(roles.has("ENTITY_EXTRACTION")).toBe(true);

    const templates = thinkTraces.map((t) => t.templateId);
    expect(new Set(templates).size).toBeGreaterThan(3);
    expect(templates.every((t) => t !== "measure.visibility_probe")).toBe(true);

    const measureTraces = result.stages.MEASURE?.traces ?? [];
    expect(measureTraces.length).toBeGreaterThanOrEqual(5);
    expect(
      measureTraces.every((t) => t.templateId === "measure.visibility_probe"),
    ).toBe(true);

    // Providers used in MEASURE should span the connector fabric
    const measureProviders = new Set(measureTraces.map((t) => t.provider));
    expect(measureProviders.size).toBeGreaterThanOrEqual(4);

    expect(result.decide?.recommendations.length).toBeGreaterThan(0);
    expect(result.execute?.strategy.horizonDays).toBe(90);
    expect(result.learn?.signals.some((s) => s.key === "mention_rate")).toBe(
      true,
    );
  });

  it("blocks EXECUTE when consensus threshold is not met", async () => {
    const result = await runIntelligencePipeline(
      {
        id: "p2",
        organizationId: "o1",
        name: "Acme",
        brand: "Acme",
        domain: "acme.test",
        rootUrl: "https://acme.test",
      },
      { minConsensus: 0.99 },
    );

    expect(result.status).toBe("BLOCKED_ON_VERIFY");
    expect(result.stages.EXECUTE).toBeUndefined();
    expect(result.verify?.blocked).toBe(true);
  });
});
