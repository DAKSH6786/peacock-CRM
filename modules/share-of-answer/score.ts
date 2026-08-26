/**
 * Share of Answer — multi-indicator generative influence.
 * Token count alone is never treated as influence.
 */

export const SOA_INDICATORS = [
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
] as const;

export type SoaIndicator = (typeof SOA_INDICATORS)[number];

export const DEFAULT_INDICATOR_WEIGHTS: Record<string, number> = {
  mention: 0.12,
  position: 0.14,
  recommendation_strength: 0.18,
  answer_space: 0.1,
  citation_ownership: 0.14,
  semantic_prominence: 0.12,
  claim_balance: 0.1,
  comparison_outcome: 0.1,
};

const COMPARISON_SCORES: Record<string, number> = {
  win: 1,
  tie: 0.55,
  mixed: 0.45,
  lose: 0.15,
  absent: 0,
};

export type EntityIndicatorReading = {
  entityName: string;
  isClient?: boolean;
  mention: boolean;
  mentionCount?: number;
  position?: number | null;
  recommendationStrength: number;
  answerSpace: number;
  citationOwnership: number;
  semanticProminence: number;
  positiveClaims: number;
  negativeClaims: number;
  neutralClaims: number;
  comparisonOutcome: string;
  /** Diagnostic only — never sole influence. */
  tokenSpanRatio: number;
};

export type BrandShare = {
  entityName: string;
  isClient: boolean;
  shareOfAnswer: number;
  mentionRate: number;
  avgPositionScore: number;
  avgRecommendationStrength: number;
  avgAnswerSpace: number;
  avgCitationOwnership: number;
  avgSemanticProminence: number;
  avgClaimBalance: number;
  avgComparisonScore: number;
  avgTokenSpanRatio: number;
  tokenOnlyShare: number;
  tokenVsInfluenceGap: number;
  positiveClaimsTotal: number;
  negativeClaimsTotal: number;
  neutralClaimsTotal: number;
  observationSampleSize: number;
  meanInfluence: number;
};

function clamp01(n: number): number {
  return Math.max(0, Math.min(1, n));
}

export function positionToScore(
  position: number | null | undefined,
  maxRank = 10,
): number {
  if (position == null || position < 1) return 0;
  return clamp01((maxRank - position + 1) / maxRank);
}

export function claimBalanceScore(
  positive: number,
  negative: number,
  neutral: number,
): number {
  const total = positive + negative + neutral;
  if (total <= 0) return 0;
  const signed = (positive - negative) / total;
  const neutralBoost = 0.1 * (neutral / total);
  return clamp01(0.5 + 0.5 * signed + neutralBoost);
}

export function computeInfluence(
  reading: EntityIndicatorReading,
  weights: Record<string, number> = DEFAULT_INDICATOR_WEIGHTS,
): {
  influence: number;
  claimBalance: number;
  positionScore: number;
  comparisonScore: number;
  tokenSpanUsedAsSoleSignal: boolean;
} {
  const totalW = Object.values(weights).reduce((a, b) => a + b, 0) || 1;
  const w = Object.fromEntries(
    Object.entries(weights).map(([k, v]) => [k, v / totalW]),
  );

  const positionScore = positionToScore(reading.position);
  const claimBalance = claimBalanceScore(
    reading.positiveClaims,
    reading.negativeClaims,
    reading.neutralClaims,
  );
  const comparisonScore =
    COMPARISON_SCORES[reading.comparisonOutcome.toLowerCase()] ?? 0;

  const components: Record<string, number> = {
    mention: reading.mention ? 1 : 0,
    position: positionScore,
    recommendation_strength: clamp01(reading.recommendationStrength),
    answer_space: clamp01(reading.answerSpace),
    citation_ownership: clamp01(reading.citationOwnership),
    semantic_prominence: clamp01(reading.semanticProminence),
    claim_balance: claimBalance,
    comparison_outcome: comparisonScore,
  };

  let influence = Object.entries(components).reduce(
    (sum, [k, v]) => sum + (w[k] ?? 0) * v,
    0,
  );

  const nonToken = Object.values(components).reduce((a, b) => a + b, 0);
  const tokenOnly =
    nonToken <= 1e-9 && reading.tokenSpanRatio > 0;
  if (tokenOnly) {
    influence = 0;
  }

  return {
    influence: clamp01(influence),
    claimBalance,
    positionScore,
    comparisonScore,
    tokenSpanUsedAsSoleSignal: tokenOnly,
  };
}

export function normaliseShareOfAnswer(
  influences: Record<string, number>,
): Record<string, number> {
  const total = Object.values(influences).reduce(
    (a, b) => a + Math.max(0, b),
    0,
  );
  if (total <= 0) {
    return Object.fromEntries(Object.keys(influences).map((k) => [k, 0]));
  }
  return Object.fromEntries(
    Object.entries(influences).map(([k, v]) => [
      k,
      (100 * Math.max(0, v)) / total,
    ]),
  );
}

export function aggregateBrandScores(
  observations: EntityIndicatorReading[][],
  weights: Record<string, number> = DEFAULT_INDICATOR_WEIGHTS,
): BrandShare[] {
  if (!observations.length) return [];

  const names = new Set<string>();
  const clientFlags = new Map<string, boolean>();
  for (const obs of observations) {
    for (const r of obs) {
      names.add(r.entityName);
      clientFlags.set(
        r.entityName,
        Boolean(clientFlags.get(r.entityName) || r.isClient),
      );
    }
  }

  const nObs = observations.length;
  const sumInf = new Map<string, number>();
  const sumMention = new Map<string, number>();
  const sumPos = new Map<string, number>();
  const sumRec = new Map<string, number>();
  const sumSpace = new Map<string, number>();
  const sumCite = new Map<string, number>();
  const sumSem = new Map<string, number>();
  const sumClaim = new Map<string, number>();
  const sumCmp = new Map<string, number>();
  const sumTok = new Map<string, number>();
  const posC = new Map<string, number>();
  const negC = new Map<string, number>();
  const neuC = new Map<string, number>();

  for (const name of names) {
    sumInf.set(name, 0);
    sumMention.set(name, 0);
    sumPos.set(name, 0);
    sumRec.set(name, 0);
    sumSpace.set(name, 0);
    sumCite.set(name, 0);
    sumSem.set(name, 0);
    sumClaim.set(name, 0);
    sumCmp.set(name, 0);
    sumTok.set(name, 0);
    posC.set(name, 0);
    negC.set(name, 0);
    neuC.set(name, 0);
  }

  for (const obs of observations) {
    const byName = new Map(obs.map((r) => [r.entityName, r]));
    for (const name of names) {
      const reading: EntityIndicatorReading = byName.get(name) ?? {
        entityName: name,
        isClient: clientFlags.get(name),
        mention: false,
        recommendationStrength: 0,
        answerSpace: 0,
        citationOwnership: 0,
        semanticProminence: 0,
        positiveClaims: 0,
        negativeClaims: 0,
        neutralClaims: 0,
        comparisonOutcome: "absent",
        tokenSpanRatio: 0,
      };
      const b = computeInfluence(reading, weights);
      sumInf.set(name, (sumInf.get(name) ?? 0) + b.influence);
      sumMention.set(
        name,
        (sumMention.get(name) ?? 0) + (reading.mention ? 1 : 0),
      );
      sumPos.set(name, (sumPos.get(name) ?? 0) + b.positionScore);
      sumRec.set(
        name,
        (sumRec.get(name) ?? 0) + clamp01(reading.recommendationStrength),
      );
      sumSpace.set(
        name,
        (sumSpace.get(name) ?? 0) + clamp01(reading.answerSpace),
      );
      sumCite.set(
        name,
        (sumCite.get(name) ?? 0) + clamp01(reading.citationOwnership),
      );
      sumSem.set(
        name,
        (sumSem.get(name) ?? 0) + clamp01(reading.semanticProminence),
      );
      sumClaim.set(name, (sumClaim.get(name) ?? 0) + b.claimBalance);
      sumCmp.set(name, (sumCmp.get(name) ?? 0) + b.comparisonScore);
      sumTok.set(
        name,
        (sumTok.get(name) ?? 0) + clamp01(reading.tokenSpanRatio),
      );
      posC.set(name, (posC.get(name) ?? 0) + reading.positiveClaims);
      negC.set(name, (negC.get(name) ?? 0) + reading.negativeClaims);
      neuC.set(name, (neuC.get(name) ?? 0) + reading.neutralClaims);
    }
  }

  const meanInf: Record<string, number> = {};
  const meanTok: Record<string, number> = {};
  for (const name of names) {
    meanInf[name] = (sumInf.get(name) ?? 0) / nObs;
    meanTok[name] = (sumTok.get(name) ?? 0) / nObs;
  }
  const shares = normaliseShareOfAnswer(meanInf);
  const tokenShares = normaliseShareOfAnswer(meanTok);

  const out: BrandShare[] = [...names].map((name) => {
    const soa = shares[name] ?? 0;
    const tok = tokenShares[name] ?? 0;
    return {
      entityName: name,
      isClient: Boolean(clientFlags.get(name)),
      shareOfAnswer: Math.round(soa * 10000) / 10000,
      mentionRate: (sumMention.get(name) ?? 0) / nObs,
      avgPositionScore: (sumPos.get(name) ?? 0) / nObs,
      avgRecommendationStrength: (sumRec.get(name) ?? 0) / nObs,
      avgAnswerSpace: (sumSpace.get(name) ?? 0) / nObs,
      avgCitationOwnership: (sumCite.get(name) ?? 0) / nObs,
      avgSemanticProminence: (sumSem.get(name) ?? 0) / nObs,
      avgClaimBalance: (sumClaim.get(name) ?? 0) / nObs,
      avgComparisonScore: (sumCmp.get(name) ?? 0) / nObs,
      avgTokenSpanRatio: (sumTok.get(name) ?? 0) / nObs,
      tokenOnlyShare: Math.round(tok * 10000) / 10000,
      tokenVsInfluenceGap: Math.round((soa - tok) * 10000) / 10000,
      positiveClaimsTotal: posC.get(name) ?? 0,
      negativeClaimsTotal: negC.get(name) ?? 0,
      neutralClaimsTotal: neuC.get(name) ?? 0,
      observationSampleSize: nObs,
      meanInfluence: meanInf[name] ?? 0,
    };
  });

  return out.sort((a, b) => b.shareOfAnswer - a.shareOfAnswer);
}

export function assertNotTokenOnlyWeights(
  weights: Record<string, number>,
): void {
  const keys = Object.keys(weights);
  if (
    keys.length > 0 &&
    keys.every((k) =>
      ["token_span", "token_span_ratio", "tokens"].includes(k),
    )
  ) {
    throw new Error(
      "Token count alone is rejected as Share of Answer methodology; provide multiple indicators",
    );
  }
}

export function shareOfAnswerCatalog() {
  return {
    indicators: [...SOA_INDICATORS],
    defaultWeights: { ...DEFAULT_INDICATOR_WEIGHTS },
    comparisonOutcomes: Object.keys(COMPARISON_SCORES),
    methodologyNote:
      "Share of Answer uses multiple indicators. Token span is diagnostic only and never treated as influence by itself.",
  };
}
