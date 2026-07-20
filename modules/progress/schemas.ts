import { z } from "zod";

export const objectiveCreateSchema = z.object({
  title: z.string().min(1).max(300),
  description: z.string().max(10000).optional().nullable(),
  scope: z.enum(["COMPANY", "DEPARTMENT", "TEAM", "INDIVIDUAL"]),
  parentId: z.string().optional().nullable(),
  departmentId: z.string().optional().nullable(),
  teamId: z.string().optional().nullable(),
  primaryOwnerId: z.string().optional().nullable(),
  contributorIds: z.array(z.string()).optional(),
  financialYearId: z.string().optional().nullable(),
  quarter: z.string().max(20).optional().nullable(),
  startDate: z.string().optional().nullable(),
  dueDate: z.string().optional().nullable(),
  priority: z.enum(["LOW", "MEDIUM", "HIGH", "CRITICAL"]).optional(),
  visibility: z.enum(["ORGANIZATION", "DEPARTMENT", "TEAM", "PRIVATE"]).optional(),
  tags: z.array(z.string()).optional(),
});

export const objectiveUpdateSchema = objectiveCreateSchema.partial().extend({
  status: z
    .enum([
      "NOT_STARTED",
      "IN_PROGRESS",
      "AT_RISK",
      "BLOCKED",
      "COMPLETED",
      "CANCELLED",
    ])
    .optional(),
  progressPct: z.number().int().min(0).max(100).optional(),
  health: z.enum(["GREEN", "AMBER", "RED", "GREY"]).optional(),
  healthOverrideReason: z.string().max(2000).optional().nullable(),
});

export const keyResultCreateSchema = z.object({
  objectiveId: z.string().min(1),
  title: z.string().min(1).max(300),
  metricType: z.enum([
    "NUMBER",
    "PERCENT",
    "CURRENCY",
    "BOOLEAN",
    "TEXT",
    "MILESTONE",
    "CUSTOM",
  ]),
  baseline: z.number().optional().nullable(),
  target: z.number().optional().nullable(),
  currentValue: z.number().optional().nullable(),
  unit: z.string().max(40).optional().nullable(),
  ownerUserId: z.string().optional().nullable(),
  updateFrequency: z.enum(["WEEKLY", "MONTHLY", "QUARTERLY", "AD_HOC"]).optional(),
  confidenceScore: z.number().int().min(0).max(100).optional().nullable(),
  dueDate: z.string().optional().nullable(),
  evidence: z.string().max(5000).optional().nullable(),
});

export const keyResultValueUpdateSchema = z.object({
  newValue: z.number(),
  confidenceScore: z.number().int().min(0).max(100).optional().nullable(),
  note: z.string().max(5000).optional().nullable(),
  evidence: z.string().max(5000).optional().nullable(),
});

export const progressUpdateSchema = z.object({
  objectiveId: z.string().optional().nullable(),
  cadence: z.enum(["WEEKLY", "MONTHLY"]),
  periodStart: z.string(),
  periodEnd: z.string(),
  body: z.string().min(1).max(20000),
  progressPct: z.number().int().min(0).max(100).optional().nullable(),
  confidenceScore: z.number().int().min(0).max(100).optional().nullable(),
  health: z.enum(["GREEN", "AMBER", "RED", "GREY"]).optional().nullable(),
  riskFlag: z.boolean().optional(),
  blocker: z.string().max(5000).optional().nullable(),
  evidence: z.string().max(5000).optional().nullable(),
});

export const businessReviewSchema = z.object({
  title: z.string().min(1).max(300),
  reviewType: z.enum(["MONTHLY", "QUARTERLY"]),
  periodStart: z.string(),
  periodEnd: z.string(),
  summary: z.string().max(20000).optional().nullable(),
  majorWins: z.string().max(20000).optional().nullable(),
  missedTargets: z.string().max(20000).optional().nullable(),
  items: z
    .array(
      z.object({
        itemType: z.enum(["WIN", "MISS", "RISK", "DECISION", "ACTION"]),
        title: z.string().min(1).max(300),
        body: z.string().max(5000).optional().nullable(),
        ownerUserId: z.string().optional().nullable(),
        dueDate: z.string().optional().nullable(),
      }),
    )
    .optional(),
});

export const scorecardSchema = z.object({
  departmentId: z.string().min(1),
  name: z.string().min(1).max(200),
  description: z.string().max(2000).optional().nullable(),
  kpiIds: z.array(z.string()).default([]),
});

export type ObjectiveCreateInput = z.infer<typeof objectiveCreateSchema>;
export type KeyResultCreateInput = z.infer<typeof keyResultCreateSchema>;
export type BusinessReviewInput = z.infer<typeof businessReviewSchema>;
