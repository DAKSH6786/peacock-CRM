import "server-only";

import { prisma } from "@/database";
import { createAuditLog } from "@/modules/audit/service";
import type { SessionUser } from "@/permissions/types";

import { getLeadDetail, moveLeadStage } from "./leads";
import { computeAndPersistLeadScore } from "./leads";

export async function logLeadActivity(input: {
  user: SessionUser;
  organizationId: string;
  leadId: string;
  type: "NOTE" | "CALL" | "MEETING" | "EMAIL" | "OTHER";
  subject?: string | null;
  body?: string | null;
  occurredAt?: string;
  direction?: "INBOUND" | "OUTBOUND";
  durationSec?: number;
  outcome?: string | null;
  startsAt?: string;
  endsAt?: string;
  location?: string | null;
}) {
  const lead = await prisma.lead.findFirst({
    where: {
      id: input.leadId,
      organizationId: input.organizationId,
      deletedAt: null,
    },
  });
  if (!lead) throw new Error("Lead not found");

  const occurredAt = input.occurredAt ? new Date(input.occurredAt) : new Date();

  await prisma.$transaction(async (tx) => {
    await tx.leadActivity.create({
      data: {
        organizationId: input.organizationId,
        leadId: input.leadId,
        type: input.type,
        subject: input.subject ?? null,
        body: input.body ?? null,
        occurredAt,
        createdById: input.user.id,
      },
    });

    if (input.type === "NOTE") {
      await tx.note.create({
        data: {
          organizationId: input.organizationId,
          leadId: input.leadId,
          body: input.body || input.subject || "",
          createdById: input.user.id,
        },
      });
    }

    if (input.type === "CALL") {
      await tx.callLog.create({
        data: {
          organizationId: input.organizationId,
          leadId: input.leadId,
          direction: input.direction ?? "OUTBOUND",
          durationSec: input.durationSec,
          outcome: input.outcome ?? null,
          notes: input.body ?? null,
          occurredAt,
          createdById: input.user.id,
        },
      });
    }

    if (input.type === "MEETING") {
      await tx.meeting.create({
        data: {
          organizationId: input.organizationId,
          leadId: input.leadId,
          title: input.subject || "Meeting",
          startsAt: input.startsAt ? new Date(input.startsAt) : occurredAt,
          endsAt: input.endsAt
            ? new Date(input.endsAt)
            : new Date(occurredAt.getTime() + 30 * 60_000),
          location: input.location ?? null,
          notes: input.body ?? null,
          createdById: input.user.id,
        },
      });
    }

    if (input.type === "EMAIL") {
      await tx.emailActivity.create({
        data: {
          organizationId: input.organizationId,
          leadId: input.leadId,
          direction: input.direction ?? "OUTBOUND",
          subject: input.subject ?? "(no subject)",
          body: input.body ?? null,
          createdById: input.user.id,
        },
      });
    }

    await tx.lead.update({
      where: { id: input.leadId },
      data: {
        lastContactedAt: occurredAt,
        engagementScore: { increment: 5 },
      },
    });
  });

  await computeAndPersistLeadScore(input.leadId);
  return getLeadDetail(input.organizationId, input.leadId);
}

export async function createFollowUp(input: {
  user: SessionUser;
  organizationId: string;
  leadId: string;
  dueAt: string;
  notes?: string | null;
  assignedUserId?: string | null;
}) {
  const dueAt = new Date(input.dueAt);
  await prisma.followUp.create({
    data: {
      organizationId: input.organizationId,
      leadId: input.leadId,
      dueAt,
      notes: input.notes ?? null,
      assignedUserId: input.assignedUserId ?? input.user.id,
    },
  });
  await prisma.lead.update({
    where: { id: input.leadId },
    data: { nextFollowUpAt: dueAt },
  });
  return getLeadDetail(input.organizationId, input.leadId);
}

export async function completeFollowUp(input: {
  user: SessionUser;
  organizationId: string;
  followUpId: string;
}) {
  const followUp = await prisma.followUp.findFirst({
    where: { id: input.followUpId, organizationId: input.organizationId },
  });
  if (!followUp) throw new Error("Follow-up not found");

  await prisma.followUp.update({
    where: { id: followUp.id },
    data: { completedAt: new Date() },
  });

  const next = await prisma.followUp.findFirst({
    where: {
      leadId: followUp.leadId,
      completedAt: null,
      organizationId: input.organizationId,
    },
    orderBy: { dueAt: "asc" },
  });

  await prisma.lead.update({
    where: { id: followUp.leadId },
    data: { nextFollowUpAt: next?.dueAt ?? null },
  });

  return getLeadDetail(input.organizationId, followUp.leadId);
}

export async function rescheduleFollowUp(input: {
  user: SessionUser;
  organizationId: string;
  followUpId: string;
  dueAt: string;
}) {
  const followUp = await prisma.followUp.findFirst({
    where: { id: input.followUpId, organizationId: input.organizationId },
  });
  if (!followUp) throw new Error("Follow-up not found");

  const dueAt = new Date(input.dueAt);
  await prisma.followUp.update({
    where: { id: followUp.id },
    data: { dueAt },
  });
  await prisma.lead.update({
    where: { id: followUp.leadId },
    data: { nextFollowUpAt: dueAt },
  });
  return getLeadDetail(input.organizationId, followUp.leadId);
}

export async function listFollowUps(input: {
  organizationId: string;
  from?: Date;
  to?: Date;
  assignedUserId?: string;
}) {
  return prisma.followUp.findMany({
    where: {
      organizationId: input.organizationId,
      ...(input.assignedUserId
        ? { assignedUserId: input.assignedUserId }
        : {}),
      ...(input.from || input.to
        ? {
            dueAt: {
              ...(input.from ? { gte: input.from } : {}),
              ...(input.to ? { lte: input.to } : {}),
            },
          }
        : {}),
    },
    include: {
      lead: {
        select: {
          id: true,
          personName: true,
          companyName: true,
          assignedUserId: true,
        },
      },
    },
    orderBy: { dueAt: "asc" },
    take: 500,
  });
}

export async function getFollowUpReminders(organizationId: string) {
  const now = new Date();
  const in48h = new Date(now.getTime() + 48 * 60 * 60_000);

  const [overdue, upcoming] = await Promise.all([
    prisma.followUp.findMany({
      where: {
        organizationId,
        completedAt: null,
        dueAt: { lt: now },
      },
      include: {
        lead: { select: { id: true, personName: true, companyName: true } },
      },
      orderBy: { dueAt: "asc" },
      take: 100,
    }),
    prisma.followUp.findMany({
      where: {
        organizationId,
        completedAt: null,
        dueAt: { gte: now, lte: in48h },
      },
      include: {
        lead: { select: { id: true, personName: true, companyName: true } },
      },
      orderBy: { dueAt: "asc" },
      take: 100,
    }),
  ]);

  return { overdue, upcoming };
}

export async function bulkAssignLeads(input: {
  user: SessionUser;
  organizationId: string;
  leadIds: string[];
  assignedUserId: string | null;
  reason?: string;
}) {
  const leads = await prisma.lead.findMany({
    where: {
      organizationId: input.organizationId,
      id: { in: input.leadIds },
      deletedAt: null,
    },
  });

  await prisma.$transaction(
    leads.map((lead) =>
      prisma.lead.update({
        where: { id: lead.id },
        data: {
          assignedUserId: input.assignedUserId,
          assignmentHistory: {
            create: {
              organizationId: input.organizationId,
              fromUserId: lead.assignedUserId,
              toUserId: input.assignedUserId,
              changedById: input.user.id,
              reason: input.reason ?? "Bulk assignment",
            },
          },
        },
      }),
    ),
  );

  await createAuditLog({
    organizationId: input.organizationId,
    actorId: input.user.id,
    action: "UPDATE",
    entityType: "LeadBulkAssign",
    metadata: {
      count: leads.length,
      assignedUserId: input.assignedUserId,
    },
  });

  return { updated: leads.length };
}

export async function bulkChangeStage(input: {
  user: SessionUser;
  organizationId: string;
  leadIds: string[];
  stageId: string;
  lostReasonId?: string | null;
  confirmClose?: boolean;
}) {
  const results = [];
  for (const leadId of input.leadIds) {
    const result = await moveLeadStage({
      user: input.user,
      organizationId: input.organizationId,
      leadId,
      stageId: input.stageId,
      lostReasonId: input.lostReasonId,
      confirmClose: input.confirmClose,
    });
    results.push({ leadId, result });
  }
  return results;
}

export async function bulkManageTags(input: {
  user: SessionUser;
  organizationId: string;
  leadIds: string[];
  tagIds: string[];
  mode: "ADD" | "REMOVE" | "SET";
}) {
  for (const leadId of input.leadIds) {
    if (input.mode === "SET" || input.mode === "REMOVE") {
      await prisma.leadTag.deleteMany({
        where: {
          leadId,
          ...(input.mode === "REMOVE" ? { tagId: { in: input.tagIds } } : {}),
        },
      });
    }
    if (input.mode === "ADD" || input.mode === "SET") {
      for (const tagId of input.tagIds) {
        await prisma.leadTag.upsert({
          where: { leadId_tagId: { leadId, tagId } },
          create: {
            leadId,
            tagId,
          },
          update: {},
        });
      }
    }
  }
  return { updated: input.leadIds.length };
}

export async function getPipelineBoard(input: {
  organizationId: string;
  pipelineId?: string;
}) {
  const pipeline = input.pipelineId
    ? await prisma.pipeline.findFirst({
        where: {
          id: input.pipelineId,
          organizationId: input.organizationId,
          deletedAt: null,
        },
        include: {
          stages: {
            where: { deletedAt: null },
            orderBy: { sortOrder: "asc" },
          },
        },
      })
    : await prisma.pipeline.findFirst({
        where: { organizationId: input.organizationId, deletedAt: null },
        orderBy: [{ isDefault: "desc" }, { createdAt: "asc" }],
        include: {
          stages: {
            where: { deletedAt: null },
            orderBy: { sortOrder: "asc" },
          },
        },
      });

  if (!pipeline) return null;

  const leads = await prisma.lead.findMany({
    where: {
      organizationId: input.organizationId,
      pipelineId: pipeline.id,
      deletedAt: null,
    },
    include: {
      assignedUser: { select: { id: true, name: true, email: true } },
      leadTags: { include: { tag: true } },
      stageHistory: { orderBy: { createdAt: "desc" }, take: 1 },
    },
    orderBy: { updatedAt: "desc" },
  });

  const now = new Date();
  const columns = pipeline.stages.map((stage) => {
    const cards = leads
      .filter((l) => l.stageId === stage.id)
      .map((lead) => {
        const enteredAt = lead.stageHistory[0]?.createdAt ?? lead.createdAt;
        const ageDays = Math.floor(
          (now.getTime() - enteredAt.getTime()) / 86_400_000,
        );
        const stale =
          Boolean(stage.staleAfterDays) &&
          ageDays >= (stage.staleAfterDays as number);
        return {
          id: lead.id,
          personName: lead.personName,
          companyName: lead.companyName,
          estimatedValueMinor: lead.estimatedValueMinor,
          currencyCode: lead.currencyCode,
          leadScore: lead.leadScore,
          probability: lead.probability ?? stage.probability,
          assignedUser: lead.assignedUser,
          tags: lead.leadTags.map((t) => t.tag),
          nextFollowUpAt: lead.nextFollowUpAt,
          ageDays,
          stale,
          enteredStageAt: enteredAt.toISOString(),
        };
      });

    return {
      stage: {
        id: stage.id,
        name: stage.name,
        code: stage.code,
        color: stage.color,
        probability: stage.probability,
        sortOrder: stage.sortOrder,
        requiredFields: stage.requiredFields,
        staleAfterDays: stage.staleAfterDays,
        isClosedWon: stage.isClosedWon,
        isClosedLost: stage.isClosedLost,
      },
      cards,
      totalValueMinor: cards.reduce(
        (sum, c) => sum + (c.estimatedValueMinor ?? 0),
        0,
      ),
      weightedValueMinor: cards.reduce(
        (sum, c) =>
          sum +
          Math.round(
            ((c.estimatedValueMinor ?? 0) * (c.probability ?? 0)) / 100,
          ),
        0,
      ),
    };
  });

  return { pipeline, columns };
}

export async function getSalespersonWorkload(organizationId: string) {
  const leads = await prisma.lead.findMany({
    where: { organizationId, deletedAt: null },
    select: {
      id: true,
      assignedUserId: true,
      estimatedValueMinor: true,
      nextFollowUpAt: true,
      stage: { select: { isClosedWon: true, isClosedLost: true } },
      assignedUser: { select: { id: true, name: true, email: true } },
    },
  });

  const now = new Date();
  const map = new Map<
    string,
    {
      userId: string;
      name: string;
      email: string;
      openLeads: number;
      overdueFollowUps: number;
      pipelineValueMinor: number;
    }
  >();

  for (const lead of leads) {
    if (!lead.assignedUser) continue;
    if (lead.stage?.isClosedWon || lead.stage?.isClosedLost) continue;
    const key = lead.assignedUser.id;
    const row = map.get(key) ?? {
      userId: lead.assignedUser.id,
      name: lead.assignedUser.name ?? lead.assignedUser.email,
      email: lead.assignedUser.email,
      openLeads: 0,
      overdueFollowUps: 0,
      pipelineValueMinor: 0,
    };
    row.openLeads += 1;
    row.pipelineValueMinor += lead.estimatedValueMinor ?? 0;
    if (lead.nextFollowUpAt && lead.nextFollowUpAt < now) {
      row.overdueFollowUps += 1;
    }
    map.set(key, row);
  }

  return [...map.values()].sort((a, b) => b.openLeads - a.openLeads);
}

export async function getLeadActivityReport(organizationId: string) {
  const since = new Date(Date.now() - 30 * 86_400_000);
  const activities = await prisma.leadActivity.groupBy({
    by: ["type"],
    where: { organizationId, occurredAt: { gte: since } },
    _count: { _all: true },
  });
  const calls = await prisma.callLog.count({
    where: { organizationId, occurredAt: { gte: since } },
  });
  const meetings = await prisma.meeting.count({
    where: { organizationId, startsAt: { gte: since } },
  });
  const followUpsCompleted = await prisma.followUp.count({
    where: { organizationId, completedAt: { gte: since } },
  });

  return {
    since: since.toISOString(),
    byType: activities.map((a) => ({ type: a.type, count: a._count._all })),
    calls,
    meetings,
    followUpsCompleted,
  };
}

export async function createQuoteFromLead(input: {
  user: SessionUser;
  organizationId: string;
  leadId: string;
}) {
  const lead = await prisma.lead.findFirst({
    where: {
      id: input.leadId,
      organizationId: input.organizationId,
      deletedAt: null,
    },
  });
  if (!lead) throw new Error("Lead not found");
  if (!lead.companyId) {
    throw new Error("Convert lead to a company before generating a quote");
  }

  const quoteNumber = `QT-${Date.now().toString(36).toUpperCase()}`;
  const quote = await prisma.quote.create({
    data: {
      organizationId: input.organizationId,
      companyId: lead.companyId,
      dealId: null,
      quoteNumber,
      status: "DRAFT",
      currencyCode: lead.currencyCode,
      subtotalMinor: lead.estimatedValueMinor ?? 0,
      taxTotalMinor: 0,
      totalMinor: lead.estimatedValueMinor ?? 0,
      createdById: input.user.id,
    },
  });

  await prisma.leadActivity.create({
    data: {
      organizationId: input.organizationId,
      leadId: lead.id,
      type: "QUOTE",
      subject: `Quote ${quoteNumber} created`,
      body: quote.id,
      createdById: input.user.id,
    },
  });

  return quote;
}
