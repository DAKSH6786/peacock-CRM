import type { HealthStatus, ProgressStatus } from "@prisma/client";

export type HealthRuleMatch = {
  minProgress?: number;
  maxProgress?: number;
  maxDaysOverdue?: number;
  statuses?: ProgressStatus[];
  requireStarted?: boolean;
};

export type HealthRuleDef = {
  name: string;
  health: HealthStatus;
  match: HealthRuleMatch;
  sortOrder?: number;
  isActive?: boolean;
};

export const DEFAULT_HEALTH_RULES: HealthRuleDef[] = [
  {
    name: "Completed",
    health: "GREEN",
    match: { statuses: ["COMPLETED"], minProgress: 100 },
    sortOrder: 1,
  },
  {
    name: "On track",
    health: "GREEN",
    match: { minProgress: 70, maxDaysOverdue: 0, statuses: ["IN_PROGRESS"] },
    sortOrder: 2,
  },
  {
    name: "At risk",
    health: "AMBER",
    match: {
      minProgress: 40,
      maxProgress: 69,
      maxDaysOverdue: 7,
      statuses: ["IN_PROGRESS", "AT_RISK"],
    },
    sortOrder: 3,
  },
  {
    name: "Off track",
    health: "RED",
    match: {
      maxProgress: 39,
      statuses: ["IN_PROGRESS", "AT_RISK", "BLOCKED"],
    },
    sortOrder: 4,
  },
  {
    name: "Not started / insufficient info",
    health: "GREY",
    match: { statuses: ["NOT_STARTED"], requireStarted: false },
    sortOrder: 5,
  },
];

export type HealthInput = {
  progressPct: number;
  status: ProgressStatus;
  dueDate?: Date | null;
  now?: Date;
  hasUpdates?: boolean;
  overridden?: boolean;
  overrideHealth?: HealthStatus | null;
};

function daysOverdue(dueDate: Date | null | undefined, now: Date): number {
  if (!dueDate) return 0;
  const diff = Math.floor((now.getTime() - dueDate.getTime()) / 86_400_000);
  return Math.max(0, diff);
}

function ruleMatches(rule: HealthRuleDef, input: HealthInput, overdue: number): boolean {
  const match = rule.match;
  if (match.statuses && !match.statuses.includes(input.status)) return false;
  if (match.minProgress != null && input.progressPct < match.minProgress) return false;
  if (match.maxProgress != null && input.progressPct > match.maxProgress) return false;
  if (match.maxDaysOverdue != null && overdue > match.maxDaysOverdue) {
    // overdue beyond tolerance → this rule does not count as on-track/at-risk match
    if (rule.health === "GREEN" || rule.health === "AMBER") return false;
  }
  if (match.requireStarted === false && input.status === "NOT_STARTED") return true;
  if (match.requireStarted && !input.hasUpdates && input.status === "NOT_STARTED") {
    return true;
  }
  return true;
}

/**
 * Configurable health calculation. Manual override wins only when recorded.
 */
export function calculateHealth(
  input: HealthInput,
  rules: HealthRuleDef[] = DEFAULT_HEALTH_RULES,
): { health: HealthStatus; source: "override" | "rule" | "default"; ruleName?: string } {
  if (input.overridden && input.overrideHealth) {
    return { health: input.overrideHealth, source: "override" };
  }

  const now = input.now ?? new Date();
  const overdue = daysOverdue(input.dueDate, now);
  const active = [...rules]
    .filter((r) => r.isActive !== false)
    .sort((a, b) => (a.sortOrder ?? 0) - (b.sortOrder ?? 0));

  // Prefer more severe matches when overdue is high
  if (overdue > 14 && input.status !== "COMPLETED" && input.status !== "CANCELLED") {
    return { health: "RED", source: "rule", ruleName: "Severely overdue" };
  }

  for (const rule of active) {
    if (ruleMatches(rule, input, overdue)) {
      return { health: rule.health, source: "rule", ruleName: rule.name };
    }
  }

  if (input.status === "NOT_STARTED" || input.progressPct === 0) {
    return { health: "GREY", source: "default", ruleName: "Insufficient information" };
  }

  return { health: "AMBER", source: "default" };
}

export function computeKeyResultProgress(input: {
  metricType: string;
  baseline?: number | null;
  target?: number | null;
  currentValue?: number | null;
}): number {
  const { metricType, baseline = 0, target, currentValue } = input;
  if (currentValue == null || target == null) return 0;

  if (metricType === "BOOLEAN" || metricType === "MILESTONE") {
    return currentValue >= target ? 100 : 0;
  }

  const base = baseline ?? 0;
  const span = Number(target) - Number(base);
  if (span === 0) return Number(currentValue) >= Number(target) ? 100 : 0;
  const pct = ((Number(currentValue) - Number(base)) / span) * 100;
  return Math.max(0, Math.min(100, Math.round(pct)));
}

export function averageProgress(values: number[]): number {
  if (values.length === 0) return 0;
  return Math.round(values.reduce((a, b) => a + b, 0) / values.length);
}
