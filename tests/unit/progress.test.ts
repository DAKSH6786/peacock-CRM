import { describe, expect, it } from "vitest";

import {
  averageProgress,
  calculateHealth,
  computeKeyResultProgress,
  DEFAULT_HEALTH_RULES,
} from "@/modules/progress/health";
import {
  businessReviewSchema,
  keyResultCreateSchema,
  keyResultValueUpdateSchema,
  objectiveCreateSchema,
  objectiveUpdateSchema,
  progressUpdateSchema,
  scorecardSchema,
} from "@/modules/progress/schemas";
import { hasPermission } from "@/permissions/types";

describe("progress health calculation", () => {
  it("returns override when recorded", () => {
    const result = calculateHealth(
      {
        progressPct: 10,
        status: "IN_PROGRESS",
        overridden: true,
        overrideHealth: "GREEN",
      },
      DEFAULT_HEALTH_RULES,
    );
    expect(result.source).toBe("override");
    expect(result.health).toBe("GREEN");
  });

  it("marks not started as grey", () => {
    const result = calculateHealth({
      progressPct: 0,
      status: "NOT_STARTED",
    });
    expect(result.health).toBe("GREY");
  });

  it("marks severely overdue as red", () => {
    const result = calculateHealth({
      progressPct: 80,
      status: "IN_PROGRESS",
      dueDate: new Date("2020-01-01"),
      now: new Date("2026-07-01"),
    });
    expect(result.health).toBe("RED");
  });

  it("computes KR progress for number and boolean types", () => {
    expect(
      computeKeyResultProgress({
        metricType: "NUMBER",
        baseline: 0,
        target: 100,
        currentValue: 40,
      }),
    ).toBe(40);
    expect(
      computeKeyResultProgress({
        metricType: "PERCENT",
        baseline: 20,
        target: 40,
        currentValue: 30,
      }),
    ).toBe(50);
    expect(
      computeKeyResultProgress({
        metricType: "BOOLEAN",
        baseline: 0,
        target: 1,
        currentValue: 1,
      }),
    ).toBe(100);
    expect(
      computeKeyResultProgress({
        metricType: "MILESTONE",
        target: 1,
        currentValue: 0,
      }),
    ).toBe(0);
    expect(averageProgress([50, 100])).toBe(75);
  });
});

describe("progress validation schemas", () => {
  it("validates objective create with levels and parent", () => {
    const parsed = objectiveCreateSchema.parse({
      title: "Grow ARR",
      scope: "COMPANY",
      parentId: null,
      quarter: "Q2",
      tags: ["growth"],
    });
    expect(parsed.scope).toBe("COMPANY");
  });

  it("requires health override explanation on update schema shape", () => {
    const parsed = objectiveUpdateSchema.parse({
      health: "RED",
      healthOverrideReason: "Blocked by vendor delay",
    });
    expect(parsed.healthOverrideReason).toContain("vendor");
  });

  it("supports all KR measurement types", () => {
    for (const metricType of [
      "NUMBER",
      "CURRENCY",
      "PERCENT",
      "BOOLEAN",
      "MILESTONE",
      "CUSTOM",
    ] as const) {
      const parsed = keyResultCreateSchema.parse({
        objectiveId: "obj-1",
        title: "KR",
        metricType,
        target: 10,
        baseline: 0,
      });
      expect(parsed.metricType).toBe(metricType);
    }
  });

  it("records append-only value updates with evidence", () => {
    const parsed = keyResultValueUpdateSchema.parse({
      newValue: 42,
      confidenceScore: 80,
      note: "Weekly update",
      evidence: "https://example.com/proof",
    });
    expect(parsed.newValue).toBe(42);
  });

  it("validates weekly/monthly progress updates with blockers", () => {
    const parsed = progressUpdateSchema.parse({
      cadence: "WEEKLY",
      periodStart: "2026-07-01",
      periodEnd: "2026-07-07",
      body: "Shipped milestone",
      riskFlag: true,
      blocker: "Waiting on client assets",
      confidenceScore: 55,
    });
    expect(parsed.cadence).toBe("WEEKLY");
  });

  it("validates business review snapshot payload", () => {
    const parsed = businessReviewSchema.parse({
      title: "July review",
      reviewType: "MONTHLY",
      periodStart: "2026-07-01",
      periodEnd: "2026-07-31",
      majorWins: "Closed deal",
      missedTargets: "Win rate",
      items: [
        {
          itemType: "ACTION",
          title: "Follow up pipeline",
          dueDate: "2026-08-01",
        },
      ],
    });
    expect(parsed.items?.[0]?.itemType).toBe("ACTION");
  });

  it("validates configurable scorecards", () => {
    const parsed = scorecardSchema.parse({
      departmentId: "dept-1",
      name: "FY scorecard",
      kpiIds: ["kpi-1", "kpi-2"],
    });
    expect(parsed.kpiIds).toHaveLength(2);
  });
});

describe("progress permissions", () => {
  it("grants progress view/manage by role", () => {
    expect(hasPermission("SUPER_ADMIN", "progress:view")).toBe(true);
    expect(hasPermission("SUPER_ADMIN", "progress:manage")).toBe(true);
    expect(hasPermission("DEPARTMENT_HEAD", "progress:review")).toBe(true);
    expect(hasPermission("EMPLOYEE", "progress:view")).toBe(true);
    expect(hasPermission("EMPLOYEE", "progress:manage")).toBe(false);
    expect(hasPermission("VIEWER", "progress:view")).toBe(false);
  });
});
