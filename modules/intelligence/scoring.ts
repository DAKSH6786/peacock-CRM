import type { DecidedRecommendation, RecommendationWeights } from "./types";

export function scoreRecommendation(
  base: Omit<DecidedRecommendation, "confidence"> & { confidence?: number },
  weights: RecommendationWeights,
): DecidedRecommendation {
  let weightFactor = 1;
  for (const [feature, value] of Object.entries(base.features)) {
    const key = `${base.kind}:${feature}`;
    const w = weights[key] ?? 1;
    weightFactor *= 1 + (w - 1) * value;
  }

  const impact = clamp(base.impactScore * weightFactor, 0, 1);
  const effort = clamp(base.effortScore, 0, 1);
  const confidence = clamp(base.confidence ?? 0.7, 0, 1);
  const priorityScore = impact * confidence * (1 - effort * 0.5);

  return {
    ...base,
    impactScore: impact,
    effortScore: effort,
    confidence,
    // encode priority hint in impact already; keep fields explicit
    summary:
      priorityScore >= 0.55
        ? base.summary
        : `${base.summary} (lower urgency after weighting)`,
  };
}

export function rankRecommendations(
  items: DecidedRecommendation[],
): DecidedRecommendation[] {
  return [...items].sort((a, b) => {
    const sa = a.impactScore * a.confidence * (1 - a.effortScore * 0.5);
    const sb = b.impactScore * b.confidence * (1 - b.effortScore * 0.5);
    return sb - sa;
  });
}

function clamp(n: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, n));
}
