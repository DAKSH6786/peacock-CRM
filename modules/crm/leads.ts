import "server-only";

import type { Prisma } from "@prisma/client";

import { prisma } from "@/database";
import { createAuditLog } from "@/modules/audit/service";
import type { SessionUser } from "@/permissions/types";

import { findDuplicateHits } from "./duplicates";
import { validateStageEntry } from "./duplicates";
import {
  daysSince,
  normalizeCompanyName,
  normalizeDomain,
  normalizeEmail,
  normalizePhone,
  splitPersonName,
} from "./normalize";
import {
  DEFAULT_SCORING_RULES,
  scoreLead,
  type ScoringRuleDef,
} from "./scoring";
import type {
  ConvertLeadInput,
  LeadCreateInput,
  LeadUpdateInput,
} from "./schemas";

const leadListInclude = {
  source: true,
  status: true,
  stage: true,
  pipeline: true,
  assignedUser: { select: { id: true, name: true, email: true } },
  lostReason: true,
  leadTags: { include: { tag: true } },
  followUps: {
    where: { completedAt: null },
    orderBy: { dueAt: "asc" as const },
    take: 1,
  },
} satisfies Prisma.LeadInclude;

export type LeadListFilters = {
  q?: string;
  sourceId?: string;
  statusId?: string;
  stageId?: string;
  pipelineId?: string;
  assignedUserId?: string;
  country?: string;
  tagId?: string;
  staleOnly?: boolean;
  followUp?: "overdue" | "upcoming" | "none";
};

export async function listLeads(input: {
  organizationId: string;
  filters?: LeadListFilters;
  take?: number;
}) {
  const f = input.filters ?? {};
  const now = new Date();

  const where: Prisma.LeadWhereInput = {
    organizationId: input.organizationId,
    deletedAt: null,
    ...(f.sourceId ? { sourceId: f.sourceId } : {}),
    ...(f.statusId ? { statusId: f.statusId } : {}),
    ...(f.stageId ? { stageId: f.stageId } : {}),
    ...(f.pipelineId ? { pipelineId: f.pipelineId } : {}),
    ...(f.assignedUserId ? { assignedUserId: f.assignedUserId } : {}),
    ...(f.country ? { country: { equals: f.country, mode: "insensitive" } } : {}),
    ...(f.tagId ? { leadTags: { some: { tagId: f.tagId } } } : {}),
    ...(f.q
      ? {
          OR: [
            { personName: { contains: f.q, mode: "insensitive" } },
            { companyName: { contains: f.q, mode: "insensitive" } },
            { email: { contains: f.q, mode: "insensitive" } },
            { phone: { contains: f.q, mode: "insensitive" } },
          ],
        }
      : {}),
    ...(f.followUp === "overdue"
      ? { nextFollowUpAt: { lt: now } }
      : f.followUp === "upcoming"
        ? { nextFollowUpAt: { gte: now } }
        : f.followUp === "none"
          ? { nextFollowUpAt: null }
          : {}),
  };

  const leads = await prisma.lead.findMany({
    where,
    include: leadListInclude,
    orderBy: [{ updatedAt: "desc" }],
    take: input.take ?? 500,
  });

  return leads.map((lead) => {
    const ageDays = daysSince(lead.createdAt, now) ?? 0;
    const lastStageAt =
      lead.updatedAt; /* refined by history when available */
    const staleAfter = lead.stage?.staleAfterDays ?? null;
    const stale =
      Boolean(staleAfter) &&
      daysSince(lastStageAt, now)! >= (staleAfter as number);

    return {
      ...lead,
      ageDays,
      stale,
      nextFollowUp: lead.followUps[0] ?? null,
      tags: lead.leadTags.map((lt) => lt.tag),
    };
  });
}

export async function getLeadDetail(organizationId: string, leadId: string) {
  return prisma.lead.findFirst({
    where: { id: leadId, organizationId, deletedAt: null },
    include: {
      ...leadListInclude,
      company: true,
      contact: true,
      campaign: true,
      stageHistory: {
        include: { toStage: true },
        orderBy: { createdAt: "desc" },
        take: 50,
      },
      assignmentHistory: { orderBy: { createdAt: "desc" }, take: 50 },
      activities: { orderBy: { occurredAt: "desc" }, take: 50 },
      callLogs: { orderBy: { occurredAt: "desc" }, take: 50 },
      meetings: { orderBy: { startsAt: "desc" }, take: 50 },
      notesList: { orderBy: { createdAt: "desc" }, take: 50 },
      emailActivities: { orderBy: { createdAt: "desc" }, take: 50 },
      followUps: { orderBy: { dueAt: "asc" }, take: 50 },
      deals: { where: { deletedAt: null }, take: 20 },
    },
  });
}

async function loadScoringRules(organizationId: string): Promise<ScoringRuleDef[]> {
  const rules = await prisma.leadScoringRule.findMany({
    where: { organizationId, isActive: true, deletedAt: null },
    orderBy: { sortOrder: "asc" },
  });
  if (rules.length === 0) return DEFAULT_SCORING_RULES;
  return rules.map((r) => ({
    factor: r.factor,
    label: r.label,
    points: r.points,
    match: r.match,
    isActive: r.isActive,
  }));
}

export async function computeAndPersistLeadScore(leadId: string) {
  const lead = await prisma.lead.findUnique({
    where: { id: leadId },
    include: {
      source: true,
      activities: true,
      callLogs: true,
      meetings: true,
      notesList: true,
      emailActivities: true,
    },
  });
  if (!lead) return null;

  const rules = await loadScoringRules(lead.organizationId);
  const activityCount =
    lead.activities.length +
    lead.callLogs.length +
    lead.meetings.length +
    lead.notesList.length +
    lead.emailActivities.length;

  const result = scoreLead(
    {
      companySize: lead.companySize,
      country: lead.country,
      sourceCode: lead.source?.code,
      budgetMinor: lead.budgetMinor ?? lead.estimatedValueMinor,
      interestedServices: lead.interestedServices,
      engagementScore: lead.engagementScore,
      activityCount,
      daysSinceContact: daysSince(lead.lastContactedAt),
      decisionTimeline: lead.decisionTimeline,
      existingRelationship: lead.existingRelationship,
      websiteQuality: lead.websiteQuality,
      ageDays: daysSince(lead.createdAt),
    },
    rules,
  );

  return prisma.lead.update({
    where: { id: leadId },
    data: {
      leadScore: result.score,
      scoreBreakdown: result.breakdown as unknown as Prisma.InputJsonValue,
    },
  });
}

function identityFields(input: {
  email?: string | null;
  phone?: string | null;
  companyName?: string | null;
  website?: string | null;
}) {
  return {
    normalizedEmail: normalizeEmail(input.email),
    normalizedPhone: normalizePhone(input.phone),
    normalizedCompany: normalizeCompanyName(input.companyName),
    normalizedDomain:
      normalizeDomain(input.website) ?? normalizeDomain(input.email),
  };
}

export async function createLead(input: {
  user: SessionUser;
  organizationId: string;
  data: LeadCreateInput;
}) {
  const defaults = await getCrmDefaults(input.organizationId);
  const identity = identityFields(input.data);

  const lead = await prisma.lead.create({
    data: {
      organizationId: input.organizationId,
      personName: input.data.personName,
      companyName: input.data.companyName ?? null,
      email: input.data.email || null,
      phone: input.data.phone ?? null,
      country: input.data.country ?? null,
      city: input.data.city ?? null,
      website: input.data.website ?? null,
      sourceId: input.data.sourceId ?? defaults.sourceId,
      statusId: input.data.statusId ?? defaults.statusId,
      pipelineId: input.data.pipelineId ?? defaults.pipelineId,
      stageId: input.data.stageId ?? defaults.stageId,
      campaignId: input.data.campaignId ?? null,
      estimatedValueMinor: input.data.estimatedValueMinor ?? null,
      currencyCode: input.data.currencyCode ?? "INR",
      probability:
        input.data.probability ??
        defaults.stageProbability ??
        null,
      expectedClosingDate: input.data.expectedClosingDate
        ? new Date(input.data.expectedClosingDate)
        : null,
      assignedUserId: input.data.assignedUserId ?? input.user.id,
      nextFollowUpAt: input.data.nextFollowUpAt
        ? new Date(input.data.nextFollowUpAt)
        : null,
      interestedServices: input.data.interestedServices ?? [],
      notes: input.data.notes ?? null,
      companySize: input.data.companySize ?? null,
      budgetMinor: input.data.budgetMinor ?? null,
      decisionTimeline: input.data.decisionTimeline ?? null,
      websiteQuality: input.data.websiteQuality ?? null,
      existingRelationship: input.data.existingRelationship ?? false,
      createdById: input.user.id,
      ...identity,
      ...(input.data.tagIds?.length
        ? {
            leadTags: {
              create: input.data.tagIds.map((tagId) => ({
                tagId,
              })),
            },
          }
        : {}),
      ...(input.data.stageId || defaults.stageId
        ? {
            stageHistory: {
              create: {
                organizationId: input.organizationId,
                toStageId: (input.data.stageId ?? defaults.stageId)!,
                changedById: input.user.id,
                note: "Lead created",
              },
            },
          }
        : {}),
      assignmentHistory: {
        create: {
          organizationId: input.organizationId,
          toUserId: input.data.assignedUserId ?? input.user.id,
          changedById: input.user.id,
          reason: "Initial assignment",
        },
      },
    },
  });

  await computeAndPersistLeadScore(lead.id);
  await refreshDuplicateCandidates(input.organizationId, lead.id);

  await createAuditLog({
    organizationId: input.organizationId,
    actorId: input.user.id,
    action: "CREATE",
    entityType: "Lead",
    entityId: lead.id,
    metadata: { personName: lead.personName },
  });

  return getLeadDetail(input.organizationId, lead.id);
}

export async function updateLead(input: {
  user: SessionUser;
  organizationId: string;
  leadId: string;
  data: LeadUpdateInput;
}) {
  const existing = await prisma.lead.findFirst({
    where: {
      id: input.leadId,
      organizationId: input.organizationId,
      deletedAt: null,
    },
  });
  if (!existing) throw new Error("Lead not found");

  const identity = identityFields({
    email: input.data.email !== undefined ? input.data.email : existing.email,
    phone: input.data.phone !== undefined ? input.data.phone : existing.phone,
    companyName:
      input.data.companyName !== undefined
        ? input.data.companyName
        : existing.companyName,
    website:
      input.data.website !== undefined ? input.data.website : existing.website,
  });

  if (
    input.data.assignedUserId !== undefined &&
    input.data.assignedUserId !== existing.assignedUserId
  ) {
    await prisma.leadAssignmentHistory.create({
      data: {
        organizationId: input.organizationId,
        leadId: input.leadId,
        fromUserId: existing.assignedUserId,
        toUserId: input.data.assignedUserId,
        changedById: input.user.id,
        reason: "Manual reassignment",
      },
    });
  }

  await prisma.lead.update({
    where: { id: input.leadId },
    data: {
      ...(input.data.personName !== undefined
        ? { personName: input.data.personName }
        : {}),
      ...(input.data.companyName !== undefined
        ? { companyName: input.data.companyName }
        : {}),
      ...(input.data.email !== undefined
        ? { email: input.data.email || null }
        : {}),
      ...(input.data.phone !== undefined ? { phone: input.data.phone } : {}),
      ...(input.data.country !== undefined ? { country: input.data.country } : {}),
      ...(input.data.city !== undefined ? { city: input.data.city } : {}),
      ...(input.data.website !== undefined ? { website: input.data.website } : {}),
      ...(input.data.sourceId !== undefined ? { sourceId: input.data.sourceId } : {}),
      ...(input.data.statusId !== undefined ? { statusId: input.data.statusId } : {}),
      ...(input.data.pipelineId !== undefined
        ? { pipelineId: input.data.pipelineId }
        : {}),
      ...(input.data.campaignId !== undefined
        ? { campaignId: input.data.campaignId }
        : {}),
      ...(input.data.estimatedValueMinor !== undefined
        ? { estimatedValueMinor: input.data.estimatedValueMinor }
        : {}),
      ...(input.data.currencyCode !== undefined
        ? { currencyCode: input.data.currencyCode }
        : {}),
      ...(input.data.probability !== undefined
        ? { probability: input.data.probability }
        : {}),
      ...(input.data.expectedClosingDate !== undefined
        ? {
            expectedClosingDate: input.data.expectedClosingDate
              ? new Date(input.data.expectedClosingDate)
              : null,
          }
        : {}),
      ...(input.data.assignedUserId !== undefined
        ? { assignedUserId: input.data.assignedUserId }
        : {}),
      ...(input.data.nextFollowUpAt !== undefined
        ? {
            nextFollowUpAt: input.data.nextFollowUpAt
              ? new Date(input.data.nextFollowUpAt)
              : null,
          }
        : {}),
      ...(input.data.interestedServices !== undefined
        ? { interestedServices: input.data.interestedServices }
        : {}),
      ...(input.data.notes !== undefined ? { notes: input.data.notes } : {}),
      ...(input.data.companySize !== undefined
        ? { companySize: input.data.companySize }
        : {}),
      ...(input.data.budgetMinor !== undefined
        ? { budgetMinor: input.data.budgetMinor }
        : {}),
      ...(input.data.decisionTimeline !== undefined
        ? { decisionTimeline: input.data.decisionTimeline }
        : {}),
      ...(input.data.websiteQuality !== undefined
        ? { websiteQuality: input.data.websiteQuality }
        : {}),
      ...(input.data.existingRelationship !== undefined
        ? { existingRelationship: input.data.existingRelationship }
        : {}),
      ...(input.data.lostReasonId !== undefined
        ? { lostReasonId: input.data.lostReasonId }
        : {}),
      updatedById: input.user.id,
      ...identity,
    },
  });

  if (input.data.stageId && input.data.stageId !== existing.stageId) {
    await moveLeadStage({
      user: input.user,
      organizationId: input.organizationId,
      leadId: input.leadId,
      stageId: input.data.stageId,
      confirmClose: true,
    });
  }

  await computeAndPersistLeadScore(input.leadId);
  await refreshDuplicateCandidates(input.organizationId, input.leadId);

  await createAuditLog({
    organizationId: input.organizationId,
    actorId: input.user.id,
    action: "UPDATE",
    entityType: "Lead",
    entityId: input.leadId,
  });

  return getLeadDetail(input.organizationId, input.leadId);
}

export async function moveLeadStage(input: {
  user: SessionUser;
  organizationId: string;
  leadId: string;
  stageId: string;
  note?: string;
  lostReasonId?: string | null;
  confirmClose?: boolean;
}) {
  const lead = await prisma.lead.findFirst({
    where: {
      id: input.leadId,
      organizationId: input.organizationId,
      deletedAt: null,
    },
  });
  if (!lead) throw new Error("Lead not found");

  const stage = await prisma.pipelineStage.findFirst({
    where: {
      id: input.stageId,
      organizationId: input.organizationId,
      deletedAt: null,
    },
  });
  if (!stage) throw new Error("Stage not found");

  const gate = validateStageEntry(
    {
      personName: lead.personName,
      email: lead.email,
      phone: lead.phone,
      companyName: lead.companyName,
      estimatedValueMinor: lead.estimatedValueMinor,
      assignedUserId: lead.assignedUserId,
      sourceId: lead.sourceId,
      interestedServices: lead.interestedServices,
    },
    stage.requiredFields,
  );
  if (!gate.ok) {
    return {
      ok: false as const,
      reason: "REQUIRED_FIELDS" as const,
      missingFields: gate.missingFields,
    };
  }

  if ((stage.isClosedWon || stage.isClosedLost) && !input.confirmClose) {
    return {
      ok: false as const,
      reason: "CONFIRM_CLOSE" as const,
      stage,
    };
  }

  if (stage.isClosedLost && !input.lostReasonId && !lead.lostReasonId) {
    return {
      ok: false as const,
      reason: "LOST_REASON_REQUIRED" as const,
    };
  }

  await prisma.$transaction(async (tx) => {
    await tx.lead.update({
      where: { id: lead.id },
      data: {
        stageId: stage.id,
        pipelineId: stage.pipelineId,
        probability: stage.probability,
        lostReasonId: stage.isClosedLost
          ? (input.lostReasonId ?? lead.lostReasonId)
          : lead.lostReasonId,
        updatedById: input.user.id,
      },
    });
    await tx.leadStageHistory.create({
      data: {
        organizationId: input.organizationId,
        leadId: lead.id,
        fromStageId: lead.stageId,
        toStageId: stage.id,
        changedById: input.user.id,
        note: input.note ?? null,
      },
    });
  });

  await createAuditLog({
    organizationId: input.organizationId,
    actorId: input.user.id,
    action: "UPDATE",
    entityType: "Lead",
    entityId: lead.id,
    metadata: {
      action: "stage_move",
      fromStageId: lead.stageId,
      toStageId: stage.id,
    },
  });

  return {
    ok: true as const,
    lead: await getLeadDetail(input.organizationId, lead.id),
  };
}

export async function convertLead(input: {
  user: SessionUser;
  organizationId: string;
  leadId: string;
  options: ConvertLeadInput;
}) {
  const lead = await prisma.lead.findFirst({
    where: {
      id: input.leadId,
      organizationId: input.organizationId,
      deletedAt: null,
    },
    include: { stage: true },
  });
  if (!lead) throw new Error("Lead not found");

  const result = await prisma.$transaction(async (tx) => {
    let companyId = lead.companyId;
    let contactId = lead.contactId;
    let dealId: string | null = null;
    let clientAccountId: string | null = null;
    let projectId: string | null = null;

    if (input.options.createCompany && !companyId) {
      const company = await tx.clientCompany.create({
        data: {
          organizationId: input.organizationId,
          name: lead.companyName || `${lead.personName} Company`,
          website: lead.website,
          domain: normalizeDomain(lead.website) ?? normalizeDomain(lead.email),
          normalizedName: normalizeCompanyName(
            lead.companyName || lead.personName,
          ),
          normalizedDomain:
            normalizeDomain(lead.website) ?? normalizeDomain(lead.email),
          phone: lead.phone,
          createdById: input.user.id,
        },
      });
      companyId = company.id;
    }

    if (input.options.createContact && !contactId) {
      const { firstName, lastName } = splitPersonName(lead.personName);
      const contact = await tx.contact.create({
        data: {
          organizationId: input.organizationId,
          companyId,
          firstName,
          lastName,
          email: lead.email,
          phone: lead.phone,
          normalizedEmail: normalizeEmail(lead.email),
        },
      });
      contactId = contact.id;
    }

    if (input.options.createDeal) {
      const pipelineId = lead.pipelineId;
      const stageId = lead.stageId;
      if (!pipelineId || !stageId) {
        throw new Error("Lead must be on a pipeline stage before conversion");
      }
      const deal = await tx.deal.create({
        data: {
          organizationId: input.organizationId,
          name:
            input.options.dealName ||
            `${lead.companyName || lead.personName} — Deal`,
          leadId: lead.id,
          companyId,
          pipelineId,
          stageId,
          ownerUserId: lead.assignedUserId ?? input.user.id,
          valueMinor: lead.estimatedValueMinor ?? 0,
          currencyCode: lead.currencyCode,
          probability: lead.probability ?? lead.stage?.probability ?? 0,
          expectedCloseDate: lead.expectedClosingDate,
        },
      });
      dealId = deal.id;
      await tx.dealStageHistory.create({
        data: {
          organizationId: input.organizationId,
          dealId: deal.id,
          toStageId: stageId,
          changedById: input.user.id,
          note: "Created from lead conversion",
        },
      });
    }

    if (input.options.createClientAccount && companyId) {
      const account = await tx.clientAccount.create({
        data: {
          organizationId: input.organizationId,
          companyId,
          name: lead.companyName || `${lead.personName} Account`,
          accountManagerId: lead.assignedUserId,
          status: "ACTIVE",
        },
      });
      clientAccountId = account.id;
    }

    if (input.options.createProjectPlaceholder && clientAccountId) {
      const code = `PRJ-${Date.now().toString(36).toUpperCase()}`;
      const project = await tx.project.create({
        data: {
          organizationId: input.organizationId,
          clientAccountId,
          companyId,
          dealId,
          name:
            input.options.projectName ||
            `${lead.companyName || lead.personName} — Kickoff`,
          code,
          status: "PLANNED",
          createdById: input.user.id,
        },
      });
      projectId = project.id;
    }

    await tx.lead.update({
      where: { id: lead.id },
      data: {
        companyId,
        contactId,
        updatedById: input.user.id,
      },
    });

    await tx.leadActivity.create({
      data: {
        organizationId: input.organizationId,
        leadId: lead.id,
        type: "CONVERSION",
        subject: "Lead converted",
        body: JSON.stringify({
          companyId,
          contactId,
          dealId,
          clientAccountId,
          projectId,
        }),
        createdById: input.user.id,
      },
    });

    return { companyId, contactId, dealId, clientAccountId, projectId };
  });

  await createAuditLog({
    organizationId: input.organizationId,
    actorId: input.user.id,
    action: "CREATE",
    entityType: "LeadConversion",
    entityId: lead.id,
    metadata: result,
  });

  return { ...result, lead: await getLeadDetail(input.organizationId, lead.id) };
}

export async function refreshDuplicateCandidates(
  organizationId: string,
  leadId: string,
) {
  const lead = await prisma.lead.findFirst({
    where: { id: leadId, organizationId, deletedAt: null },
  });
  if (!lead) return [];

  const pool = await prisma.lead.findMany({
    where: { organizationId, deletedAt: null, NOT: { id: leadId } },
    select: {
      id: true,
      email: true,
      phone: true,
      website: true,
      companyName: true,
      normalizedEmail: true,
      normalizedPhone: true,
      normalizedCompany: true,
      normalizedDomain: true,
    },
    take: 2000,
  });

  const hits = findDuplicateHits(lead, pool);
  for (const hit of hits) {
    await prisma.leadDuplicateCandidate.upsert({
      where: {
        leadId_matchLeadId_matchType: {
          leadId: hit.leadId,
          matchLeadId: hit.matchLeadId,
          matchType: hit.matchType,
        },
      },
      create: {
        organizationId,
        leadId: hit.leadId,
        matchLeadId: hit.matchLeadId,
        matchType: hit.matchType,
        matchValue: hit.matchValue,
        status: "PENDING",
      },
      update: {
        matchValue: hit.matchValue,
        status: "PENDING",
      },
    });
  }
  return hits;
}

export async function listDuplicateReviews(organizationId: string) {
  return prisma.leadDuplicateCandidate.findMany({
    where: { organizationId, status: "PENDING" },
    include: {
      lead: {
        select: {
          id: true,
          personName: true,
          companyName: true,
          email: true,
          phone: true,
        },
      },
      matchLead: {
        select: {
          id: true,
          personName: true,
          companyName: true,
          email: true,
          phone: true,
        },
      },
    },
    orderBy: { createdAt: "desc" },
    take: 200,
  });
}

export async function reviewDuplicate(input: {
  user: SessionUser;
  organizationId: string;
  candidateId: string;
  decision: "DISMISS" | "KEEP_BOTH";
}) {
  return prisma.leadDuplicateCandidate.updateMany({
    where: { id: input.candidateId, organizationId: input.organizationId },
    data: {
      status: "DISMISSED",
      reviewedById: input.user.id,
      reviewedAt: new Date(),
    },
  });
}

async function getCrmDefaults(organizationId: string) {
  const [pipeline, status, source] = await Promise.all([
    prisma.pipeline.findFirst({
      where: { organizationId, deletedAt: null },
      orderBy: [{ isDefault: "desc" }, { createdAt: "asc" }],
      include: {
        stages: {
          where: { deletedAt: null },
          orderBy: { sortOrder: "asc" },
          take: 1,
        },
      },
    }),
    prisma.leadStatus.findFirst({
      where: { organizationId, deletedAt: null },
      orderBy: { sortOrder: "asc" },
    }),
    prisma.leadSource.findFirst({
      where: { organizationId, deletedAt: null, isActive: true },
    }),
  ]);

  return {
    pipelineId: pipeline?.id ?? null,
    stageId: pipeline?.stages[0]?.id ?? null,
    stageProbability: pipeline?.stages[0]?.probability ?? null,
    statusId: status?.id ?? null,
    sourceId: source?.id ?? null,
  };
}

export async function getCrmLookups(organizationId: string) {
  const [sources, statuses, pipelines, lostReasons, tags, users, scoringRules] =
    await Promise.all([
      prisma.leadSource.findMany({
        where: { organizationId, deletedAt: null, isActive: true },
        orderBy: { name: "asc" },
      }),
      prisma.leadStatus.findMany({
        where: { organizationId, deletedAt: null, isActive: true },
        orderBy: { sortOrder: "asc" },
      }),
      prisma.pipeline.findMany({
        where: { organizationId, deletedAt: null },
        include: {
          stages: {
            where: { deletedAt: null },
            orderBy: { sortOrder: "asc" },
          },
        },
        orderBy: [{ isDefault: "desc" }, { name: "asc" }],
      }),
      prisma.lostReason.findMany({
        where: { organizationId, deletedAt: null, isActive: true },
        orderBy: { name: "asc" },
      }),
      prisma.tag.findMany({
        where: { organizationId, deletedAt: null },
        orderBy: { name: "asc" },
      }),
      prisma.user.findMany({
        where: { organizationId, deletedAt: null, status: "ACTIVE" },
        select: { id: true, name: true, email: true },
        orderBy: { name: "asc" },
      }),
      prisma.leadScoringRule.findMany({
        where: { organizationId, deletedAt: null },
        orderBy: { sortOrder: "asc" },
      }),
    ]);

  return {
    sources,
    statuses,
    pipelines,
    lostReasons,
    tags,
    users,
    scoringRules:
      scoringRules.length > 0 ? scoringRules : DEFAULT_SCORING_RULES,
  };
}
