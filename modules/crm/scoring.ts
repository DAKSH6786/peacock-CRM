export type ScoringFactor =
  | "company_size"
  | "country"
  | "source"
  | "budget"
  | "service_interest"
  | "engagement"
  | "activities"
  | "response_recency"
  | "decision_timeline"
  | "existing_relationship"
  | "website_quality"
  | "lead_age";

export type ScoreBreakdownItem = {
  factor: ScoringFactor | string;
  label: string;
  points: number;
  reason: string;
};

export type LeadScoringInput = {
  companySize?: string | null;
  country?: string | null;
  sourceCode?: string | null;
  budgetMinor?: number | null;
  interestedServices?: unknown;
  engagementScore?: number | null;
  activityCount?: number;
  daysSinceContact?: number | null;
  decisionTimeline?: string | null;
  existingRelationship?: boolean | null;
  websiteQuality?: number | null;
  ageDays?: number | null;
};

export type ScoringRuleDef = {
  factor: string;
  label: string;
  points: number;
  match?: unknown;
  isActive?: boolean;
};

type MatchExpr =
  | { op: "eq"; value: string | number | boolean }
  | { op: "gte"; value: number }
  | { op: "lte"; value: number }
  | { op: "between"; min: number; max: number }
  | { op: "includes"; value: string }
  | { op: "exists" }
  | { op: "truthy" };

function readFactorValue(
  factor: string,
  input: LeadScoringInput,
): unknown {
  switch (factor) {
    case "company_size":
      return input.companySize ?? null;
    case "country":
      return input.country ?? null;
    case "source":
      return input.sourceCode ?? null;
    case "budget":
      return input.budgetMinor ?? null;
    case "service_interest": {
      if (!input.interestedServices) return null;
      if (Array.isArray(input.interestedServices)) {
        return input.interestedServices.length;
      }
      return 1;
    }
    case "engagement":
      return input.engagementScore ?? 0;
    case "activities":
      return input.activityCount ?? 0;
    case "response_recency":
      return input.daysSinceContact ?? null;
    case "decision_timeline":
      return input.decisionTimeline ?? null;
    case "existing_relationship":
      return Boolean(input.existingRelationship);
    case "website_quality":
      return input.websiteQuality ?? null;
    case "lead_age":
      return input.ageDays ?? null;
    default:
      return null;
  }
}

function matches(match: unknown, value: unknown): boolean {
  if (match == null) {
    return value != null && value !== "" && value !== false;
  }
  const expr = match as MatchExpr;
  switch (expr.op) {
    case "eq":
      return value === expr.value || String(value) === String(expr.value);
    case "gte":
      return typeof value === "number" && value >= expr.value;
    case "lte":
      return typeof value === "number" && value <= expr.value;
    case "between":
      return (
        typeof value === "number" && value >= expr.min && value <= expr.max
      );
    case "includes":
      return String(value ?? "")
        .toLowerCase()
        .includes(String(expr.value).toLowerCase());
    case "exists":
      return value != null && value !== "";
    case "truthy":
      return Boolean(value);
    default:
      return false;
  }
}

/** Default transparent rules used when an org has none configured */
export const DEFAULT_SCORING_RULES: ScoringRuleDef[] = [
  {
    factor: "company_size",
    label: "Enterprise company size",
    points: 15,
    match: { op: "includes", value: "enterprise" },
  },
  {
    factor: "company_size",
    label: "Mid-market company size",
    points: 10,
    match: { op: "includes", value: "mid" },
  },
  {
    factor: "country",
    label: "Priority market (IN/US/GB/AE)",
    points: 8,
    match: { op: "includes", value: "IN" },
  },
  {
    factor: "source",
    label: "Inbound / referral source",
    points: 12,
    match: { op: "includes", value: "REF" },
  },
  {
    factor: "source",
    label: "Website source",
    points: 8,
    match: { op: "includes", value: "WEB" },
  },
  {
    factor: "budget",
    label: "Budget ≥ ₹5L",
    points: 20,
    match: { op: "gte", value: 500_000_00 },
  },
  {
    factor: "budget",
    label: "Budget ≥ ₹1L",
    points: 10,
    match: { op: "gte", value: 100_000_00 },
  },
  {
    factor: "service_interest",
    label: "Has service interest",
    points: 8,
    match: { op: "gte", value: 1 },
  },
  {
    factor: "engagement",
    label: "High engagement",
    points: 10,
    match: { op: "gte", value: 50 },
  },
  {
    factor: "activities",
    label: "3+ activities logged",
    points: 10,
    match: { op: "gte", value: 3 },
  },
  {
    factor: "response_recency",
    label: "Contacted within 7 days",
    points: 12,
    match: { op: "lte", value: 7 },
  },
  {
    factor: "decision_timeline",
    label: "Near-term decision",
    points: 10,
    match: { op: "includes", value: "30" },
  },
  {
    factor: "existing_relationship",
    label: "Existing relationship",
    points: 15,
    match: { op: "truthy" },
  },
  {
    factor: "website_quality",
    label: "Strong website quality",
    points: 5,
    match: { op: "gte", value: 7 },
  },
  {
    factor: "lead_age",
    label: "Fresh lead (<14 days)",
    points: 5,
    match: { op: "lte", value: 14 },
  },
];

export function scoreLead(
  input: LeadScoringInput,
  rules: ScoringRuleDef[] = DEFAULT_SCORING_RULES,
): { score: number; breakdown: ScoreBreakdownItem[] } {
  const active = rules.filter((r) => r.isActive !== false);
  const breakdown: ScoreBreakdownItem[] = [];

  for (const rule of active) {
    const value = readFactorValue(rule.factor, input);
    if (!matches(rule.match, value)) continue;
    breakdown.push({
      factor: rule.factor,
      label: rule.label,
      points: rule.points,
      reason: `Matched ${rule.factor}=${String(value)}`,
    });
  }

  const score = Math.min(
    100,
    breakdown.reduce((sum, item) => sum + item.points, 0),
  );
  return { score, breakdown };
}
