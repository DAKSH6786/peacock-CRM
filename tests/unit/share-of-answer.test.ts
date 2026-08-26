import { describe, expect, it } from "vitest";

import {
  SOA_INDICATORS,
  aggregateBrandScores,
  assertNotTokenOnlyWeights,
  computeInfluence,
  normaliseShareOfAnswer,
  type EntityIndicatorReading,
} from "@/modules/share-of-answer";

describe("share of answer", () => {
  it("tracks the full multi-indicator set", () => {
    expect(SOA_INDICATORS).toEqual(
      expect.arrayContaining([
        "mention",
        "position",
        "recommendation_strength",
        "answer_space",
        "citation_ownership",
        "semantic_prominence",
        "positive_claims",
        "negative_claims",
        "neutral_claims",
        "comparison_outcome",
      ]),
    );
  });

  it("rejects token span alone as influence", () => {
    const tokenHeavy: EntityIndicatorReading = {
      entityName: "VerboseCo",
      mention: false,
      recommendationStrength: 0,
      answerSpace: 0,
      citationOwnership: 0,
      semanticProminence: 0,
      positiveClaims: 0,
      negativeClaims: 0,
      neutralClaims: 0,
      comparisonOutcome: "absent",
      tokenSpanRatio: 0.9,
    };
    const breakdown = computeInfluence(tokenHeavy);
    expect(breakdown.influence).toBe(0);
    expect(breakdown.tokenSpanUsedAsSoleSignal).toBe(true);

    expect(() =>
      assertNotTokenOnlyWeights({ token_span: 1 }),
    ).toThrow(/Token count alone/);
  });

  it("ranks Brand A above Brand B even when Brand B has more tokens", () => {
    const obs: EntityIndicatorReading[][] = [
      [
        {
          entityName: "Brand A",
          mention: true,
          position: 1,
          recommendationStrength: 0.9,
          answerSpace: 0.35,
          citationOwnership: 0.7,
          semanticProminence: 0.8,
          positiveClaims: 5,
          negativeClaims: 0,
          neutralClaims: 1,
          comparisonOutcome: "win",
          tokenSpanRatio: 0.25,
        },
        {
          entityName: "Brand B",
          mention: true,
          position: 2,
          recommendationStrength: 0.75,
          answerSpace: 0.3,
          citationOwnership: 0.55,
          semanticProminence: 0.65,
          positiveClaims: 3,
          negativeClaims: 1,
          neutralClaims: 1,
          comparisonOutcome: "tie",
          tokenSpanRatio: 0.4,
        },
        {
          entityName: "Client",
          isClient: true,
          mention: true,
          position: 4,
          recommendationStrength: 0.35,
          answerSpace: 0.12,
          citationOwnership: 0.2,
          semanticProminence: 0.3,
          positiveClaims: 1,
          negativeClaims: 1,
          neutralClaims: 2,
          comparisonOutcome: "lose",
          tokenSpanRatio: 0.35,
        },
      ],
    ];

    const brands = aggregateBrandScores(obs);
    const byName = Object.fromEntries(brands.map((b) => [b.entityName, b]));

    expect(byName["Brand A"].shareOfAnswer).toBeGreaterThan(
      byName["Brand B"].shareOfAnswer,
    );
    expect(byName.Client.shareOfAnswer).toBeLessThan(
      byName["Brand B"].shareOfAnswer,
    );
    expect(
      Math.abs(brands.reduce((s, b) => s + b.shareOfAnswer, 0) - 100),
    ).toBeLessThan(0.1);

    // Token-only would favour Brand B; multi-indicator favours Brand A
    expect(byName["Brand B"].tokenOnlyShare).toBeGreaterThan(
      byName["Brand A"].tokenOnlyShare,
    );
    expect(byName["Brand A"].tokenVsInfluenceGap).not.toBe(0);
  });

  it("normalises cluster shares like Enterprise CRM example", () => {
    const shares = normaliseShareOfAnswer({
      A: 0.34,
      B: 0.28,
      Client: 0.11,
    });
    expect(Math.abs(Object.values(shares).reduce((a, b) => a + b, 0) - 100)).toBeLessThan(
      1e-6,
    );
    expect(shares.A).toBeGreaterThan(shares.B);
    expect(shares.B).toBeGreaterThan(shares.Client);
  });
});
