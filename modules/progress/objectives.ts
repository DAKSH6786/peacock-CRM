import "server-only";

import type { HealthStatus, Prisma } from "@prisma/client";

import { prisma } from "@/database";
import { createAuditLog } from "@/modules/audit/service";
import type { SessionUser } from "@/permissions/types";

import {
  averageProgress,
  calculateHealth,
  computeKeyResultProgress,
  DEFAULT_HEALTH_RULES,
  type HealthRuleDef,
} from "./health";
import type {
  KeyResultCreateInput,
  ObjectiveCreateInput,
} from "./schemas";

const objectiveInclude = {
  department: { select: { id: true, name: true, code: true } },
  team: { select: { id: true, name: true, code: true } },
  primaryOwner: { select: { id: true, name: true, email: true } },
  parent: { select: { id: true, title: true, scope: true } },
  children: { select: { id: true, title: true, scope: true, progressPct: true, health: true } },
  owners: {
    include: { user: { select: { id: true, name: true, email: true } } },
  },
  keyResults: {
    where: { deletedAt: null },
    include: {
      owner: { select: { id: true, name: true, email: true } },
      updates: { orderBy: { createdAt: "desc" as const }, take: 10 },
      comments: { where: { deletedAt: null }, orderBy: { createdAt: "desc" as const }, take: 10 },
    },
  },
  milestones: { where: { deletedAt: null }, orderBy: { dueDate: "asc" as const } },
  initiatives: { where: { deletedAt: null } },
  progressUpdates: { orderBy: { createdAt: "desc" as const }, take: 20 },
} satisfies Prisma.ObjectiveInclude;

async function loadHealthRules(organizationId: string): Promise<HealthRuleDef[]> {
  const rules = await prisma.progressHealthRule.findMany({
    where: { organizationId, isActive: true },
    orderBy: { sortOrder: "asc" },
  });
  if (rules.length === 0) return DEFAULT_HEALTH_RULES;
  return rules.map((r) => ({
    name: r.name,
    health: r.health,
    match: r.match as HealthRuleDef["match"],
    sortOrder: r.sortOrder,
    isActive: r.isActive,
  }));
}

export async function refreshObjectiveProgress(objectiveId: string) {
  const objective = await prisma.objective.findUnique({
    where: { id: objectiveId },
    include: {
      keyResults: { where: { deletedAt: null } },
      progressUpdates: { take: 1, orderBy: { createdAt: "desc" } },
    },
  });
  if (!objective) return null;

  const krProgress = objective.keyResults.map((kr) => kr.progressPct);
  const progressPct =
    krProgress.length > 0 ? averageProgress(krProgress) : objective.progressPct;

  const rules = await loadHealthRules(objective.organizationId);
  const healthResult = calculateHealth(
    {
      progressPct,
      status: objective.status,
      dueDate: objective.dueDate,
      hasUpdates: objective.progressUpdates.length > 0,
      overridden: objective.healthOverridden,
      overrideHealth: objective.healthOverridden ? objective.health : null,
    },
    rules,
  );

  return prisma.objective.update({
    where: { id: objectiveId },
    data: {
      progressPct,
      health: healthResult.health,
      status:
        progressPct >= 100 && objective.status !== "CANCELLED"
          ? "COMPLETED"
          : objective.status === "NOT_STARTED" && progressPct > 0
            ? "IN_PROGRESS"
            : objective.status,
    },
  });
}

export async function listObjectives(input: {
  organizationId: string;
  scope?: string;
  departmentId?: string;
  quarter?: string;
  health?: string;
  parentId?: string | null;
}) {
  return prisma.objective.findMany({
    where: {
      organizationId: input.organizationId,
      deletedAt: null,
      ...(input.scope ? { scope: input.scope as never } : {}),
      ...(input.departmentId ? { departmentId: input.departmentId } : {}),
      ...(input.quarter ? { quarter: input.quarter } : {}),
      ...(input.health ? { health: input.health as never } : {}),
      ...(input.parentId === null
        ? { parentId: null }
        : input.parentId
          ? { parentId: input.parentId }
          : {}),
    },
    include: {
      department: { select: { id: true, name: true, code: true } },
      primaryOwner: { select: { id: true, name: true, email: true } },
      parent: { select: { id: true, title: true } },
      keyResults: { where: { deletedAt: null }, select: { id: true, progressPct: true } },
      _count: { select: { children: true } },
    },
    orderBy: [{ priority: "desc" }, { updatedAt: "desc" }],
    take: 300,
  });
}

export async function getObjectiveDetail(organizationId: string, objectiveId: string) {
  return prisma.objective.findFirst({
    where: { id: objectiveId, organizationId, deletedAt: null },
    include: objectiveInclude,
  });
}

export async function createObjective(input: {
  user: SessionUser;
  organizationId: string;
  data: ObjectiveCreateInput;
}) {
  const objective = await prisma.objective.create({
    data: {
      organizationId: input.organizationId,
      title: input.data.title,
      description: input.data.description ?? null,
      scope: input.data.scope,
      parentId: input.data.parentId ?? null,
      departmentId: input.data.departmentId ?? null,
      teamId: input.data.teamId ?? null,
      primaryOwnerId: input.data.primaryOwnerId ?? input.user.id,
      financialYearId: input.data.financialYearId ?? null,
      quarter: input.data.quarter ?? null,
      startDate: input.data.startDate
        ? new Date(input.data.startDate)
        : null,
      dueDate: input.data.dueDate ? new Date(input.data.dueDate) : null,
      priority: input.data.priority ?? "MEDIUM",
      visibility: input.data.visibility ?? "ORGANIZATION",
      tags: input.data.tags ?? [],
      createdById: input.user.id,
      owners: {
        create: [
          {
            organizationId: input.organizationId,
            userId: input.data.primaryOwnerId ?? input.user.id,
            role: "OWNER",
          },
          ...(input.data.contributorIds ?? []).map((userId) => ({
            organizationId: input.organizationId,
            userId,
            role: "CONTRIBUTOR",
          })),
        ],
      },
    },
  });

  await createAuditLog({
    organizationId: input.organizationId,
    actorId: input.user.id,
    action: "CREATE",
    entityType: "Objective",
    entityId: objective.id,
    metadata: { title: objective.title, scope: objective.scope },
  });

  return getObjectiveDetail(input.organizationId, objective.id);
}

export async function updateObjective(input: {
  user: SessionUser;
  organizationId: string;
  objectiveId: string;
  data: Record<string, unknown>;
}) {
  const existing = await prisma.objective.findFirst({
    where: {
      id: input.objectiveId,
      organizationId: input.organizationId,
      deletedAt: null,
    },
  });
  if (!existing) throw new Error("Objective not found");

  const healthOverride =
    input.data.health &&
    input.data.health !== existing.health &&
    input.data.healthOverrideReason;

  if (input.data.health && !healthOverride && input.data.health !== existing.health) {
    // Allow only via recorded override
    if (!input.data.healthOverrideReason) {
      throw new Error("Health override requires an explanation");
    }
  }

  await prisma.objective.update({
    where: { id: input.objectiveId },
    data: {
      ...(input.data.title != null ? { title: String(input.data.title) } : {}),
      ...(input.data.description !== undefined
        ? { description: input.data.description as string | null }
        : {}),
      ...(input.data.scope ? { scope: input.data.scope as never } : {}),
      ...(input.data.parentId !== undefined
        ? { parentId: input.data.parentId as string | null }
        : {}),
      ...(input.data.departmentId !== undefined
        ? { departmentId: input.data.departmentId as string | null }
        : {}),
      ...(input.data.teamId !== undefined
        ? { teamId: input.data.teamId as string | null }
        : {}),
      ...(input.data.primaryOwnerId !== undefined
        ? { primaryOwnerId: input.data.primaryOwnerId as string | null }
        : {}),
      ...(input.data.quarter !== undefined
        ? { quarter: input.data.quarter as string | null }
        : {}),
      ...(input.data.priority ? { priority: input.data.priority as never } : {}),
      ...(input.data.status ? { status: input.data.status as never } : {}),
      ...(input.data.progressPct != null
        ? { progressPct: Number(input.data.progressPct) }
        : {}),
      ...(input.data.visibility
        ? { visibility: String(input.data.visibility) }
        : {}),
      ...(input.data.tags ? { tags: input.data.tags as string[] } : {}),
      ...(input.data.dueDate !== undefined
        ? {
            dueDate: input.data.dueDate
              ? new Date(String(input.data.dueDate))
              : null,
          }
        : {}),
      ...(input.data.health
        ? {
            health: input.data.health as HealthStatus,
            healthOverridden: true,
            healthOverrideReason: String(input.data.healthOverrideReason),
          }
        : {}),
      updatedById: input.user.id,
    },
  });

  if (input.data.health) {
    await createAuditLog({
      organizationId: input.organizationId,
      actorId: input.user.id,
      action: "UPDATE",
      entityType: "ObjectiveHealthOverride",
      entityId: input.objectiveId,
      metadata: {
        health: String(input.data.health),
        reason:
          input.data.healthOverrideReason != null
            ? String(input.data.healthOverrideReason)
            : null,
      },
    });
  }

  if (!input.data.health) {
    await refreshObjectiveProgress(input.objectiveId);
  }

  await createAuditLog({
    organizationId: input.organizationId,
    actorId: input.user.id,
    action: "UPDATE",
    entityType: "Objective",
    entityId: input.objectiveId,
  });

  return getObjectiveDetail(input.organizationId, input.objectiveId);
}

export async function createKeyResult(input: {
  user: SessionUser;
  organizationId: string;
  data: KeyResultCreateInput;
}) {
  const progressPct = computeKeyResultProgress({
    metricType: input.data.metricType,
    baseline: input.data.baseline,
    target: input.data.target,
    currentValue: input.data.currentValue,
  });

  const kr = await prisma.keyResult.create({
    data: {
      organizationId: input.organizationId,
      objectiveId: input.data.objectiveId,
      title: input.data.title,
      metricType: input.data.metricType,
      baseline: input.data.baseline ?? null,
      target: input.data.target ?? null,
      currentValue: input.data.currentValue ?? null,
      unit: input.data.unit ?? null,
      progressPct,
      ownerUserId: input.data.ownerUserId ?? input.user.id,
      updateFrequency: input.data.updateFrequency ?? "WEEKLY",
      confidenceScore: input.data.confidenceScore ?? null,
      dueDate: input.data.dueDate ? new Date(input.data.dueDate) : null,
      evidence: input.data.evidence ?? null,
      status: progressPct > 0 ? "IN_PROGRESS" : "NOT_STARTED",
    },
  });

  if (input.data.currentValue != null) {
    await prisma.keyResultUpdate.create({
      data: {
        organizationId: input.organizationId,
        keyResultId: kr.id,
        previousValue: null,
        newValue: input.data.currentValue,
        previousProgressPct: 0,
        progressPct,
        confidenceScore: input.data.confidenceScore ?? null,
        note: "Initial value",
        evidence: input.data.evidence ?? null,
        createdById: input.user.id,
      },
    });
  }

  await refreshObjectiveProgress(input.data.objectiveId);
  return kr;
}

/**
 * Append-only KR value update — never silently overwrites history.
 */
export async function recordKeyResultValue(input: {
  user: SessionUser;
  organizationId: string;
  keyResultId: string;
  newValue: number;
  confidenceScore?: number | null;
  note?: string | null;
  evidence?: string | null;
}) {
  const kr = await prisma.keyResult.findFirst({
    where: {
      id: input.keyResultId,
      organizationId: input.organizationId,
      deletedAt: null,
    },
  });
  if (!kr) throw new Error("Key result not found");

  const previousValue = kr.currentValue ? Number(kr.currentValue) : null;
  const progressPct = computeKeyResultProgress({
    metricType: kr.metricType,
    baseline: kr.baseline ? Number(kr.baseline) : null,
    target: kr.target ? Number(kr.target) : null,
    currentValue: input.newValue,
  });

  await prisma.$transaction(async (tx) => {
    await tx.keyResultUpdate.create({
      data: {
        organizationId: input.organizationId,
        keyResultId: kr.id,
        previousValue,
        newValue: input.newValue,
        previousProgressPct: kr.progressPct,
        progressPct,
        confidenceScore: input.confidenceScore ?? kr.confidenceScore,
        note: input.note ?? null,
        evidence: input.evidence ?? null,
        createdById: input.user.id,
      },
    });
    await tx.keyResult.update({
      where: { id: kr.id },
      data: {
        currentValue: input.newValue,
        progressPct,
        confidenceScore: input.confidenceScore ?? kr.confidenceScore,
        evidence: input.evidence ?? kr.evidence,
        status: progressPct >= 100 ? "COMPLETED" : "IN_PROGRESS",
      },
    });
  });

  await refreshObjectiveProgress(kr.objectiveId);
  await createAuditLog({
    organizationId: input.organizationId,
    actorId: input.user.id,
    action: "UPDATE",
    entityType: "KeyResult",
    entityId: kr.id,
    metadata: { previousValue, newValue: input.newValue, progressPct },
  });

  return prisma.keyResult.findUnique({
    where: { id: kr.id },
    include: {
      updates: { orderBy: { createdAt: "desc" }, take: 50 },
      comments: { where: { deletedAt: null }, orderBy: { createdAt: "desc" } },
    },
  });
}

export async function addKeyResultComment(input: {
  user: SessionUser;
  organizationId: string;
  keyResultId: string;
  body: string;
}) {
  return prisma.keyResultComment.create({
    data: {
      organizationId: input.organizationId,
      keyResultId: input.keyResultId,
      body: input.body,
      createdById: input.user.id,
    },
  });
}
