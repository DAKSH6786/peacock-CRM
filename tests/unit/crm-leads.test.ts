import { describe, expect, it } from "vitest";

import {
  findDuplicateHits,
  validateStageEntry,
  isStale,
} from "@/modules/crm/duplicates";
import {
  normalizeCompanyName,
  normalizeDomain,
  normalizeEmail,
  normalizePhone,
  splitPersonName,
} from "@/modules/crm/normalize";
import { scoreLead, DEFAULT_SCORING_RULES } from "@/modules/crm/scoring";
import { convertLeadSchema, leadCreateSchema } from "@/modules/crm/schemas";

describe("CRM normalize + duplicates", () => {
  it("normalizes identity fields", () => {
    expect(normalizeEmail(" Ada@Example.COM ")).toBe("ada@example.com");
    expect(normalizePhone("+91 (987) 654-3210")).toBe("919876543210");
    expect(normalizeCompanyName("Northstar Retail Pvt. Ltd.")).toBe(
      "northstar retail",
    );
    expect(normalizeDomain("https://www.northstar.example/about")).toBe(
      "northstar.example",
    );
    expect(normalizeDomain("ceo@northstar.example")).toBe("northstar.example");
  });

  it("finds duplicate candidates without merging", () => {
    const hits = findDuplicateHits(
      {
        id: "a",
        email: "same@example.com",
        phone: "9991112222",
        companyName: "Acme Inc",
        website: "https://acme.example",
      },
      [
        {
          id: "b",
          email: "same@example.com",
          phone: "000",
          companyName: "Other",
        },
        {
          id: "c",
          email: "other@x.com",
          phone: "9991112222",
          companyName: "Acme Limited",
          website: "acme.example",
        },
      ],
    );

    expect(hits.some((h) => h.matchType === "EMAIL" && h.matchLeadId === "b")).toBe(
      true,
    );
    expect(hits.some((h) => h.matchType === "PHONE" && h.matchLeadId === "c")).toBe(
      true,
    );
    expect(
      hits.some((h) => h.matchType === "COMPANY" && h.matchLeadId === "c"),
    ).toBe(true);
    expect(
      hits.some((h) => h.matchType === "DOMAIN" && h.matchLeadId === "c"),
    ).toBe(true);
  });
});

describe("CRM scoring + stage gates", () => {
  it("produces a transparent score breakdown", () => {
    const result = scoreLead(
      {
        companySize: "enterprise",
        country: "IN",
        sourceCode: "WEB",
        budgetMinor: 600_000_00,
        interestedServices: ["Brand"],
        engagementScore: 60,
        activityCount: 4,
        daysSinceContact: 2,
        decisionTimeline: "30 days",
        existingRelationship: true,
        websiteQuality: 8,
        ageDays: 5,
      },
      DEFAULT_SCORING_RULES,
    );

    expect(result.score).toBeGreaterThan(0);
    expect(result.score).toBeLessThanOrEqual(100);
    expect(result.breakdown.length).toBeGreaterThan(3);
    expect(result.breakdown.every((b) => b.points > 0 && b.label)).toBe(true);
  });

  it("blocks stage entry when required fields missing", () => {
    const gate = validateStageEntry(
      { personName: "Ada", email: "", companyName: null },
      ["email", "companyName"],
    );
    expect(gate.ok).toBe(false);
    if (!gate.ok) {
      expect(gate.missingFields).toEqual(["email", "companyName"]);
    }
  });

  it("detects stale deals", () => {
    const entered = new Date(Date.now() - 20 * 86_400_000);
    expect(isStale(entered, 14)).toBe(true);
    expect(isStale(entered, 30)).toBe(false);
  });
});

describe("lead-to-client workflow contracts", () => {
  it("validates lead create payloads", () => {
    const parsed = leadCreateSchema.parse({
      personName: "Anika Shah",
      email: "anika@example.com",
      companyName: "Northstar",
      estimatedValueMinor: 25000000,
      interestedServices: ["Web"],
    });
    expect(parsed.personName).toBe("Anika Shah");
  });

  it("requires explicit conversion options and supports full conversion set", () => {
    const parsed = convertLeadSchema.parse({
      createContact: true,
      createCompany: true,
      createDeal: true,
      createClientAccount: true,
      createProjectPlaceholder: true,
      dealName: "Northstar retainer",
      projectName: "Kickoff",
    });
    expect(parsed.createDeal).toBe(true);
    expect(parsed.createProjectPlaceholder).toBe(true);
  });

  it("splits person names for contact conversion", () => {
    expect(splitPersonName("Ada Lovelace")).toEqual({
      firstName: "Ada",
      lastName: "Lovelace",
    });
  });
});
